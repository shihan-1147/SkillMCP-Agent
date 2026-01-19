"""
结果整合技能
将多个来源的信息进行汇总和格式化
"""

from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from src.core.logging import get_logger

from ..base import BaseSkill

if TYPE_CHECKING:
    from src.llm.base import BaseLLM
    from src.mcp.client import MCPClient

logger = get_logger("skills.summarize")


class OutputFormat(str, Enum):
    """输出格式"""

    TEXT = "text"
    MARKDOWN = "markdown"
    JSON = "json"
    BULLET = "bullet"


class OutputStyle(str, Enum):
    """输出风格"""

    CONCISE = "concise"  # 简洁
    DETAILED = "detailed"  # 详细
    PROFESSIONAL = "professional"  # 专业


# 整合提示词模板
SUMMARIZE_PROMPT = """请将以下多个信息来源整合为一个清晰、有条理的回答。

## 原始问题
{original_query}

## 信息来源
{sources_text}

## 要求
- 输出格式: {format}
- 输出风格: {style}
- 提取关键信息，去除冗余
- 保持信息准确性，不添加臆测
- 如有冲突信息，请说明

请生成整合后的回答："""


class SummarizeSkill(BaseSkill):
    """
    结果整合技能

    能力：
    - 多源信息整合
    - 信息提炼和摘要
    - 格式化输出

    此技能主要依赖 LLM 进行文本处理，不需要外部 MCP 工具
    """

    name = "summarize"
    description = "整合多个来源的信息，生成结构化摘要。适用于多步骤任务的最终整合。"
    required_tools = []  # 主要使用 LLM，不需要外部工具

    def __init__(self, llm: "BaseLLM" = None):
        """
        初始化技能

        Args:
            llm: LLM 实例
        """
        super().__init__()
        self.llm = llm

    async def execute(
        self,
        description: str,
        tool_name: Optional[str] = None,
        tool_params: Dict[str, Any] = None,
        context: Dict[str, Any] = None,
        mcp_client: "MCPClient" = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        执行结果整合

        Args:
            description: 整合描述
            tool_params: 参数 (inputs, format, style)
            context: 上下文信息（包含前置步骤结果）
            mcp_client: MCP 客户端（此技能可能不需要）

        Returns:
            整合结果
        """
        logger.info(f"Executing summarize: {description}")

        try:
            # 解析参数
            params = tool_params or {}
            output_format = params.get("format", OutputFormat.MARKDOWN)
            output_style = params.get("style", OutputStyle.CONCISE)
            max_length = params.get("max_length", 1000)

            # 收集待整合的信息
            inputs = self._collect_inputs(params, context)

            if not inputs:
                return {"success": False, "error": "没有可整合的信息"}

            # 获取原始查询
            original_query = (
                context.get("original_query", description) if context else description
            )

            # 执行整合
            if self.llm:
                result = await self._summarize_with_llm(
                    original_query=original_query,
                    inputs=inputs,
                    output_format=output_format,
                    output_style=output_style,
                    max_length=max_length,
                )
            else:
                # 简单整合（无 LLM）
                result = self._simple_summarize(
                    inputs=inputs, output_format=output_format
                )

            logger.info("Summarize completed")
            return result

        except Exception as e:
            logger.error(f"Summarize failed: {str(e)}")
            return {"success": False, "error": str(e)}

    def _collect_inputs(
        self, params: Dict[str, Any], context: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        收集待整合的信息

        Args:
            params: 技能参数
            context: 上下文

        Returns:
            信息列表
        """
        inputs = []

        # 从参数中获取
        if params.get("inputs"):
            inputs.extend(params["inputs"])

        # 从上下文中获取前置步骤结果
        if context:
            previous_results = context.get("previous_results", {})
            for step_id, result in previous_results.items():
                inputs.append(
                    {
                        "source": f"步骤{step_id}",
                        "content": self._extract_content(result),
                    }
                )

        return inputs

    def _extract_content(self, result: Any) -> str:
        """从结果中提取内容"""
        if isinstance(result, str):
            return result
        elif isinstance(result, dict):
            # 尝试常见的内容字段
            for key in ["content", "data", "result", "summary", "answer"]:
                if key in result:
                    return self._extract_content(result[key])
            return str(result)
        elif isinstance(result, list):
            return "\n".join(str(item) for item in result)
        return str(result)

    async def _summarize_with_llm(
        self,
        original_query: str,
        inputs: List[Dict[str, Any]],
        output_format: str,
        output_style: str,
        max_length: int,
    ) -> Dict[str, Any]:
        """使用 LLM 进行整合"""

        # 构建信息源文本
        sources_text = self._format_sources(inputs)

        # 构建提示词
        prompt = SUMMARIZE_PROMPT.format(
            original_query=original_query,
            sources_text=sources_text,
            format=output_format,
            style=output_style,
        )

        # 调用 LLM
        response = await self.llm.chat(
            messages=[{"role": "user", "content": prompt}], temperature=0.5
        )

        # 提取关键点
        key_points = self._extract_key_points(response)

        return {
            "success": True,
            "data": {
                "summary": response,
                "key_points": key_points,
                "sources": [inp.get("source", "unknown") for inp in inputs],
                "format": output_format,
                "input_count": len(inputs),
            },
        }

    def _simple_summarize(
        self, inputs: List[Dict[str, Any]], output_format: str
    ) -> Dict[str, Any]:
        """简单整合（不使用 LLM）"""

        parts = []
        sources = []

        for inp in inputs:
            source = inp.get("source", "未知来源")
            content = inp.get("content", "")
            sources.append(source)

            if output_format == OutputFormat.MARKDOWN:
                parts.append(f"### {source}\n\n{content}")
            elif output_format == OutputFormat.BULLET:
                parts.append(f"• **{source}**: {content}")
            else:
                parts.append(f"[{source}] {content}")

        separator = "\n\n" if output_format == OutputFormat.MARKDOWN else "\n"
        summary = separator.join(parts)

        return {
            "success": True,
            "data": {
                "summary": summary,
                "key_points": [],
                "sources": sources,
                "format": output_format,
                "input_count": len(inputs),
            },
        }

    def _format_sources(self, inputs: List[Dict[str, Any]]) -> str:
        """格式化信息源"""
        parts = []
        for i, inp in enumerate(inputs, 1):
            source = inp.get("source", f"来源{i}")
            content = inp.get("content", "")
            parts.append(f"### 来源 {i}: {source}\n{content}")
        return "\n\n".join(parts)

    def _extract_key_points(self, text: str) -> List[str]:
        """从文本中提取关键点"""
        # 简单实现：查找列表项
        import re

        key_points = []

        # 查找 Markdown 列表项
        patterns = [
            r"^[-*•]\s+(.+)$",  # 无序列表
            r"^\d+\.\s+(.+)$",  # 有序列表
        ]

        for line in text.split("\n"):
            for pattern in patterns:
                match = re.match(pattern, line.strip())
                if match:
                    key_points.append(match.group(1))
                    break

        # 限制数量
        return key_points[:5]
