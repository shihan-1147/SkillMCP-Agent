"""
Chat 服务

处理聊天请求，整合 Agent、MCP、RAG
对外屏蔽内部实现细节
"""

import time
from contextlib import nullcontext
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from src.agent.tool_recorder import get_tool_recorder, record_tool_call
from src.agent.tracer import (AgentTracer, TraceEventType, create_tracer,
                              set_tracer)
from src.core.config import get_settings
from src.core.exceptions import AgentException
from src.core.logging import get_logger
from src.core.ollama import get_ollama_client

from .schemas import ChatRequest, ChatResponse, ResponseStatus, StructuredData
from .session import Session, get_session_manager

logger = get_logger("api.chat_service")


class ChatService:
    """
    聊天服务

    职责：
    - 接收用户消息
    - 管理会话
    - 调用 Agent 处理请求
    - 格式化响应

    前端无需感知 MCP / RAG / Agent 内部细节
    """

    def __init__(self):
        self.settings = get_settings()
        self._agent = None
        self._mcp = None
        self._rag = None
        self._initialized = False

    async def initialize(self) -> None:
        """初始化服务"""
        if self._initialized:
            return

        logger.info("Initializing ChatService...")

        # 初始化 MCP 系统
        try:
            from src.mcp import initialize_mcp

            self._mcp = await initialize_mcp()
            logger.info("MCP system initialized")
        except Exception as e:
            logger.warning(f"MCP initialization failed: {e}")

        # 初始化 RAG 系统
        try:
            from pathlib import Path

            from src.rag import get_rag_pipeline
            from src.rag.embedder import MockEmbedder

            self._rag = get_rag_pipeline()

            # 自动加载文档目录
            docs_dir = Path(self.settings.documents_dir)
            if docs_dir.exists():
                await self._rag.load_documents(docs_dir)
                logger.info(f"RAG loaded documents from {docs_dir}")
        except Exception as e:
            logger.warning(f"RAG initialization failed: {e}")

        self._initialized = True
        logger.info("ChatService initialized")

    async def chat(self, request: ChatRequest, debug: bool = False) -> ChatResponse:
        """
        处理聊天请求

        Args:
            request: 聊天请求
            debug: 是否返回调试信息

        Returns:
            聊天响应
        """
        await self.initialize()

        # 创建追踪器
        tracer = create_tracer(enable_console=True)
        tracer.start(query=request.message[:100])

        # 获取或创建会话
        session_manager = get_session_manager()
        session = await session_manager.get_or_create(request.session_id)

        # 记录用户消息
        session.add_message("user", request.message)

        logger.info(
            f"Chat request: session={session.session_id}, message={request.message[:50]}..."
        )

        try:
            # 处理消息
            reply, structured_data, sources, debug_info = await self._process_message(
                message=request.message, session=session, debug=debug, tracer=tracer
            )

            # 记录助手回复
            session.add_message("assistant", reply)

            # 结束追踪
            tracer.end(success=True, result=reply)

            # 添加追踪信息到调试数据
            if debug and debug_info:
                debug_info["trace"] = tracer.get_timeline()
                debug_info["tool_calls"] = [t.to_dict() for t in tracer.tool_calls]

            return ChatResponse(
                status=ResponseStatus.SUCCESS,
                message="OK",
                reply=reply,
                session_id=session.session_id,
                structured_data=structured_data,
                sources=sources,
                debug_info=debug_info if debug else None,
            )

        except Exception as e:
            logger.error(f"Chat processing error: {e}")

            # 结束追踪（失败）
            tracer.end(success=False, error=str(e))

            # 生成错误回复
            error_reply = f"抱歉，处理您的请求时出现了问题。请稍后再试。"
            session.add_message("assistant", error_reply)

            return ChatResponse(
                status=ResponseStatus.ERROR,
                message=str(e),
                reply=error_reply,
                session_id=session.session_id,
                debug_info=(
                    {"error": str(e), "trace": tracer.get_timeline()} if debug else None
                ),
            )

    async def _process_message(
        self,
        message: str,
        session: Session,
        debug: bool = False,
        tracer: AgentTracer = None,
    ) -> Tuple[
        str, Optional[List[StructuredData]], Optional[List[str]], Optional[Dict]
    ]:
        """
        处理用户消息

        根据消息内容路由到不同的处理流程

        Returns:
            (reply, structured_data, sources, debug_info)
        """
        debug_info = {} if debug else None
        structured_data = []
        sources = []
        tool_recorder = get_tool_recorder()

        # 获取对话历史
        history = session.get_history_for_llm(limit=10)

        # 分析意图并路由
        with tracer.trace(TraceEventType.PLANNER_START) if tracer else nullcontext():
            intent = self._analyze_intent(message)
            if tracer:
                tracer.log_intent(intent)

        if debug:
            debug_info["intent"] = intent
            debug_info["history_length"] = len(history)

        # 根据意图处理
        if intent == "weather":
            if tracer:
                tracer.log_skill_selected("weather_skill", "检测到天气查询关键词")
            reply, data = await self._handle_weather(
                message, tracer, tool_recorder, session.session_id
            )
            if data:
                structured_data.append(data)
                sources.append("weather_api")

        elif intent == "train":
            if tracer:
                tracer.log_skill_selected("train_skill", "检测到火车票查询关键词")
            reply, data = await self._handle_train(
                message, tracer, tool_recorder, session.session_id
            )
            if data:
                structured_data.append(data)
                sources.append("12306_api")

        elif intent == "knowledge":
            if tracer:
                tracer.log_skill_selected("knowledge_skill", "检测到知识查询关键词")
            reply, data, rag_sources = await self._handle_knowledge(
                message, tracer, tool_recorder, session.session_id
            )
            if data:
                structured_data.append(data)
            sources.extend(rag_sources)

        else:
            if tracer:
                tracer.log_skill_selected("general_skill", "通用对话")
            # 通用对话
            reply = await self._handle_general(message, history)

        if debug:
            debug_info["structured_data_count"] = len(structured_data)
            debug_info["sources"] = sources

        return (
            reply,
            structured_data if structured_data else None,
            sources if sources else None,
            debug_info,
        )

    def _analyze_intent(self, message: str) -> str:
        """
        分析用户意图

        简单的关键词匹配，实际项目中可以用 LLM 分类
        """
        message_lower = message.lower()

        # 天气相关
        weather_keywords = ["天气", "气温", "下雨", "晴天", "温度", "穿什么"]
        if any(kw in message_lower for kw in weather_keywords):
            return "weather"

        # 火车票相关
        train_keywords = ["火车", "高铁", "动车", "车票", "12306", "火车票"]
        if any(kw in message_lower for kw in train_keywords):
            return "train"

        # 知识查询
        knowledge_keywords = ["什么是", "如何", "怎么", "为什么", "介绍", "解释"]
        if any(kw in message_lower for kw in knowledge_keywords):
            return "knowledge"

        return "general"

    async def _handle_weather(
        self,
        message: str,
        tracer: AgentTracer = None,
        tool_recorder=None,
        session_id: str = None,
    ) -> Tuple[str, Optional[StructuredData]]:
        """处理天气查询"""
        # 提取城市
        city = self._extract_city(message) or "北京"

        try:
            if self._mcp:
                # 记录工具调用开始
                start_time = time.time()
                if tracer:
                    tracer.log_event(
                        TraceEventType.MCP_CALL_START,
                        {"tool": "weather_query", "city": city},
                    )

                result = await self._mcp.client.call_tool(
                    "weather_query", {"city": city, "type": "live"}
                )

                # 记录工具调用结束
                duration_ms = (time.time() - start_time) * 1000
                if tracer:
                    tracer.log_tool_call(
                        tool_name="weather_query",
                        arguments={"city": city, "type": "live"},
                        result=result,
                        success=result.get("success", False),
                        duration_ms=duration_ms,
                    )

                if tool_recorder:
                    tool_recorder.record_call(
                        tool_name="weather_query",
                        arguments={"city": city, "type": "live"},
                        result=result,
                        duration_ms=duration_ms,
                        session_id=session_id,
                        skill_name="weather_skill",
                        user_query=message,
                    )

                if result.get("success"):
                    data = result["data"]

                    # 生成自然语言回复 (适配真实 API 返回格式)
                    weather = data.get("weather", "未知")
                    weather_icon = data.get("weather_icon", "🌡️")
                    temperature = data.get("temperature", "N/A")
                    wind_dir = data.get("wind_direction", "")
                    wind_power = data.get("wind_power", "")
                    suggestion = data.get("suggestion", "暂无建议")
                    data_source = data.get("data_source", "")

                    reply_parts = [
                        f"{city}当前天气{weather} {weather_icon}，",
                        f"温度{temperature}℃，",
                        f"{wind_dir}{wind_power}。",
                    ]

                    if suggestion:
                        reply_parts.append(f"\n\n💡 {suggestion}")

                    if data_source:
                        reply_parts.append(f"\n\n📊 数据来源: {data_source}")

                    reply = "".join(reply_parts)

                    structured = StructuredData(
                        type="weather",
                        data={
                            "city": city,
                            "weather": weather,
                            "temperature": temperature,
                            "humidity": data.get("humidity", "N/A"),
                            "wind": f"{wind_dir}{wind_power}",
                            "suggestion": suggestion,
                            "data_source": data_source,
                        },
                    )

                    return reply, structured
                else:
                    # API 调用失败，返回真实的错误信息
                    error_msg = result.get("error", "未知错误")
                    reply = f"❌ 无法获取{city}的天气信息\n\n**原因**: {error_msg}"

                    structured = StructuredData(
                        type="error",
                        data={
                            "error_type": "api_error",
                            "message": error_msg,
                            "city": city,
                        },
                    )

                    return reply, structured

            # Fallback
            return f"抱歉，暂时无法获取{city}的天气信息。", None

        except Exception as e:
            logger.error(f"Weather query error: {e}")
            return f"查询{city}天气时出现问题，请稍后再试。", None

    async def _handle_train(
        self,
        message: str,
        tracer: AgentTracer = None,
        tool_recorder=None,
        session_id: str = None,
    ) -> Tuple[str, Optional[StructuredData]]:
        """处理火车票查询"""
        # 提取出发地和目的地
        origin, destination = self._extract_route(message)

        if not origin or not destination:
            return "请告诉我您的出发城市和目的地城市，例如：北京到上海的高铁。", None

        try:
            if self._mcp:
                # 获取日期
                start_time = time.time()
                if tracer:
                    tracer.log_event(
                        TraceEventType.MCP_CALL_START, {"tool": "system_time"}
                    )

                date_result = await self._mcp.client.call_tool(
                    "system_time", {"action": "get_current"}
                )

                duration_ms = (time.time() - start_time) * 1000
                if tracer:
                    tracer.log_tool_call(
                        "system_time",
                        {"action": "get_current"},
                        date_result,
                        True,
                        duration_ms=duration_ms,
                    )

                today = date_result["data"]["date"]

                # 解析相对日期
                if "明天" in message:
                    start_time = time.time()
                    date_result = await self._mcp.client.call_tool(
                        "system_time",
                        {"action": "parse_relative", "relative_expr": "明天"},
                    )
                    duration_ms = (time.time() - start_time) * 1000
                    if tracer:
                        tracer.log_tool_call(
                            "system_time",
                            {"action": "parse_relative"},
                            date_result,
                            True,
                            duration_ms=duration_ms,
                        )
                    today = date_result["data"]["parsed_date"]

                # 查询车票
                start_time = time.time()
                if tracer:
                    tracer.log_event(
                        TraceEventType.MCP_CALL_START, {"tool": "12306_query"}
                    )

                result = await self._mcp.client.call_tool(
                    "12306_query",
                    {
                        "action": "query_tickets",
                        "origin": origin,
                        "destination": destination,
                        "date": today,
                    },
                )

                duration_ms = (time.time() - start_time) * 1000
                if tracer:
                    tracer.log_tool_call(
                        tool_name="12306_query",
                        arguments={
                            "origin": origin,
                            "destination": destination,
                            "date": today,
                        },
                        result=result,
                        success=result.get("success", False),
                        duration_ms=duration_ms,
                    )

                if tool_recorder:
                    tool_recorder.record_call(
                        tool_name="12306_query",
                        arguments={
                            "origin": origin,
                            "destination": destination,
                            "date": today,
                        },
                        result=result,
                        duration_ms=duration_ms,
                        session_id=session_id,
                        skill_name="train_skill",
                        user_query=message,
                    )

                if result.get("success"):
                    data = result["data"]
                    trains = data["trains"][:5]  # 只取前5个

                    # 生成自然语言回复
                    reply_parts = [
                        f"🚄 {origin} → {destination} ({data['date']})",
                        f"共找到 {data['total']} 个车次，以下是部分结果：\n",
                    ]

                    for train in trains:
                        seats_info = "、".join(
                            f"{k}:{v}" for k, v in train["seats"].items()
                        )
                        reply_parts.append(
                            f"• {train['train_no']} ({train['train_type']})\n"
                            f"  {train['departure_time']} → {train['arrival_time']} "
                            f"({train['duration']})\n"
                            f"  {seats_info}"
                        )

                    reply = "\n".join(reply_parts)

                    structured = StructuredData(
                        type="train",
                        data={
                            "origin": origin,
                            "destination": destination,
                            "date": data["date"],
                            "total": data["total"],
                            "trains": trains,
                        },
                    )

                    return reply, structured
                else:
                    # API 调用失败，返回真实的错误信息
                    error_msg = result.get("error", "未知错误")
                    suggestion = result.get("suggestion", [])
                    query_info = result.get("query_info", {})

                    reply_parts = [
                        f"❌ 无法查询 {origin} → {destination} 的火车票",
                        f"\n**原因**: {error_msg}",
                        f"\n**查询信息**:",
                        f"- 出发站: {origin} ({query_info.get('origin_code', 'N/A')})",
                        f"- 到达站: {destination} ({query_info.get('destination_code', 'N/A')})",
                        f"- 日期: {query_info.get('date', 'N/A')}",
                    ]

                    if suggestion:
                        reply_parts.append("\n**建议**:")
                        for s in suggestion:
                            reply_parts.append(f"- {s}")

                    reply = "\n".join(reply_parts)

                    # 返回结构化错误数据
                    structured = StructuredData(
                        type="error",
                        data={
                            "error_type": "api_not_available",
                            "message": error_msg,
                            "query_info": query_info,
                            "suggestion": suggestion,
                        },
                    )

                    return reply, structured

            return f"抱歉，暂时无法查询{origin}到{destination}的车票信息。", None

        except Exception as e:
            logger.error(f"Train query error: {e}")
            return "查询车票时出现问题，请稍后再试。", None

    async def _handle_knowledge(
        self,
        message: str,
        tracer: AgentTracer = None,
        tool_recorder=None,
        session_id: str = None,
    ) -> Tuple[str, Optional[StructuredData], List[str]]:
        """处理知识查询（RAG）"""
        sources = []

        try:
            if self._rag and self._rag._initialized:
                # RAG 检索
                start_time = time.time()
                if tracer:
                    tracer.log_event(
                        TraceEventType.RAG_QUERY_START, {"query": message[:50]}
                    )

                results = await self._rag.retrieve(message, top_k=3)

                duration_ms = (time.time() - start_time) * 1000
                if tracer:
                    tracer.log_rag_query(message, len(results), duration_ms)

                if results:
                    # 获取上下文
                    context = self._rag.get_context_for_prompt(results)

                    # 收集来源
                    sources = list(
                        set(r.chunk.metadata.get("title", "unknown") for r in results)
                    )

                    # 生成回复（这里简化处理，实际应该用 LLM）
                    reply = self._generate_knowledge_reply(message, results)

                    structured = StructuredData(
                        type="knowledge",
                        data={
                            "query": message,
                            "sources": sources,
                            "context_length": len(context),
                        },
                    )

                    return reply, structured, sources

            # 如果 RAG 不可用，尝试使用 MCP 工具
            if self._mcp:
                start_time = time.time()
                if tracer:
                    tracer.log_event(
                        TraceEventType.MCP_CALL_START, {"tool": "rag_retriever"}
                    )

                result = await self._mcp.client.call_tool(
                    "rag_retriever", {"query": message, "top_k": 3}
                )

                duration_ms = (time.time() - start_time) * 1000
                if tracer:
                    tracer.log_tool_call(
                        tool_name="rag_retriever",
                        arguments={"query": message, "top_k": 3},
                        result=result,
                        success=result.get("success", False),
                        duration_ms=duration_ms,
                    )

                if tool_recorder:
                    tool_recorder.record_call(
                        tool_name="rag_retriever",
                        arguments={"query": message, "top_k": 3},
                        result=result,
                        duration_ms=duration_ms,
                        session_id=session_id,
                        skill_name="knowledge_skill",
                        user_query=message,
                    )

                if result.get("success") and result["data"]["documents"]:
                    docs = result["data"]["documents"]
                    sources = [doc.get("title", "unknown") for doc in docs]

                    reply = self._generate_knowledge_reply_from_docs(message, docs)

                    return reply, None, sources

            return f"抱歉，我暂时没有找到关于「{message}」的相关信息。", None, []

        except Exception as e:
            logger.error(f"Knowledge query error: {e}")
            return "查询知识库时出现问题，请稍后再试。", None, []

    async def _handle_general(self, message: str, history: List[Dict[str, str]]) -> str:
        """
        处理通用对话

        使用 Ollama LLM 进行智能回复
        """
        try:
            # 获取 Ollama 客户端
            client = get_ollama_client()

            # 构建消息历史
            messages = []

            # 添加系统提示（可选）
            system_prompt = (
                "你是一个智能助手，可以帮助用户查询天气、火车票信息，"
                "或者回答各种问题。请用友好、专业的语气回复用户。"
            )
            messages.append({"role": "system", "content": system_prompt})

            # 添加历史对话
            for msg in history[-10:]:  # 最多保留最近 10 轮对话
                messages.append({"role": msg["role"], "content": msg["content"]})

            # 添加当前用户消息
            messages.append({"role": "user", "content": message})

            # 调用 Ollama 模型
            logger.info(f"Calling Ollama model: {self.settings.ollama_model}")
            response = await client.chat(
                messages=messages, temperature=0.7, max_tokens=2048
            )

            # 提取回复内容
            if response and response.get("success") and response.get("content"):
                reply = response["content"]
                logger.info(f"Ollama response: {reply[:100]}...")
                return reply
            else:
                error_msg = (
                    response.get("error", "Unknown error")
                    if response
                    else "No response"
                )
                logger.warning(f"Ollama response failed: {error_msg}")
                return "抱歉，我暂时无法回答这个问题。"

        except Exception as e:
            logger.error(f"Ollama chat error: {e}", exc_info=True)
            # 返回友好的错误信息
            return (
                "抱歉，我遇到了一些技术问题。请确保：\n"
                f"1. Ollama 服务正在运行\n"
                f"2. 模型 {self.settings.ollama_model} 已下载\n\n"
                "你可以尝试运行：ollama pull qwen3:latest"
            )

    def _extract_city(self, message: str) -> Optional[str]:
        """从消息中提取城市名"""
        cities = [
            "北京",
            "上海",
            "广州",
            "深圳",
            "杭州",
            "成都",
            "武汉",
            "西安",
            "南京",
            "重庆",
            "天津",
            "苏州",
            "青岛",
            "厦门",
            "大连",
            "哈尔滨",
            "长沙",
            "郑州",
        ]
        for city in cities:
            if city in message:
                return city
        return None

    def _extract_route(self, message: str) -> Tuple[Optional[str], Optional[str]]:
        """
        从消息中提取出发地和目的地

        使用多种模式匹配，支持任意城市名
        """
        import re

        # 先移除时间相关的词
        clean_message = re.sub(
            r"(今天|明天|后天|大后天|下周[一二三四五六日天]?|这周[一二三四五六日天]?|周[一二三四五六日天])",
            "",
            message,
        )

        # 模式1: "从A到B" 或 "A到B" 或 "A去B"
        patterns = [
            r"从([^\s到去往从]{2,6}?)(?:到|去|往)([^\s的高动火车票]{2,6})",
            r"([^\s从]{2,4}?)(?:到|去|往)([^\s的高动火车票]{2,4})",
        ]

        for pattern in patterns:
            match = re.search(pattern, clean_message)
            if match:
                origin = match.group(1).strip()
                destination = match.group(2).strip()
                # 清理多余字符
                origin = re.sub(r"[从去往到的查一下]", "", origin)
                destination = re.sub(r"[从去往到的]", "", destination)
                if (
                    origin
                    and destination
                    and len(origin) >= 2
                    and len(destination) >= 2
                ):
                    return origin, destination

        # 模式2: 已知城市列表匹配（作为备选）
        cities = [
            "北京",
            "上海",
            "广州",
            "深圳",
            "杭州",
            "成都",
            "武汉",
            "西安",
            "南京",
            "重庆",
            "天津",
            "苏州",
            "石家庄",
            "郑州",
            "长沙",
            "济南",
            "青岛",
            "大连",
            "沈阳",
            "哈尔滨",
            "长春",
            "合肥",
            "福州",
            "厦门",
            "南昌",
            "昆明",
            "贵阳",
            "南宁",
            "海口",
            "兰州",
            "西宁",
            "银川",
            "乌鲁木齐",
            "呼和浩特",
            "拉萨",
            "太原",
            "保定",
            "唐山",
            "秦皇岛",
            "邯郸",
            "廊坊",
            "无锡",
            "常州",
            "徐州",
            "扬州",
            "泰州",
            "镇江",
            "宁波",
            "温州",
            "嘉兴",
            "绍兴",
            "金华",
            "台州",
        ]

        found = []
        for city in cities:
            if city in message:
                pos = message.find(city)
                found.append((city, pos))

        # 按出现位置排序
        found.sort(key=lambda x: x[1])

        if len(found) >= 2:
            return found[0][0], found[1][0]
        elif len(found) == 1:
            return found[0][0], None
        return None, None

    def _generate_knowledge_reply(self, query: str, results) -> str:
        """根据检索结果生成知识回复"""
        if not results:
            return f"抱歉，没有找到关于「{query}」的相关信息。"

        # 简单拼接检索结果
        parts = [f"关于「{query}」，我找到了以下信息：\n"]

        for i, result in enumerate(results[:3], 1):
            content = result.chunk.content[:200]
            title = result.chunk.metadata.get("title", "")
            parts.append(f"**{i}. {title}**\n{content}...\n")

        return "\n".join(parts)

    def _generate_knowledge_reply_from_docs(self, query: str, docs: List[Dict]) -> str:
        """根据文档列表生成知识回复"""
        if not docs:
            return f"抱歉，没有找到关于「{query}」的相关信息。"

        parts = [f"关于「{query}」，我找到了以下信息：\n"]

        for i, doc in enumerate(docs[:3], 1):
            content = doc.get("content", "")[:200]
            title = doc.get("title", "")
            parts.append(f"**{i}. {title}**\n{content}...\n")

        return "\n".join(parts)


# 全局服务实例
_chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """获取全局聊天服务"""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
