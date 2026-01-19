"""
Agent 执行追踪器

记录 Agent 执行的每一步，包括：
- 任务规划
- 技能选择
- MCP 工具调用
- RAG 检索
- 结果生成

支持：
- 实时日志输出
- 结构化追踪数据
- 执行时间统计
"""
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import time
import json
import asyncio

from src.core.logging import get_logger

logger = get_logger("agent.tracer")


class TraceEventType(str, Enum):
    """追踪事件类型"""
    # Agent 生命周期
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    AGENT_ERROR = "agent_error"
    
    # 规划阶段
    PLANNER_START = "planner_start"
    PLANNER_INTENT = "planner_intent"
    PLANNER_PLAN = "planner_plan"
    PLANNER_END = "planner_end"
    
    # 技能选择
    SKILL_SELECT_START = "skill_select_start"
    SKILL_SELECTED = "skill_selected"
    SKILL_EXECUTE_START = "skill_execute_start"
    SKILL_EXECUTE_END = "skill_execute_end"
    
    # MCP 工具调用
    MCP_CALL_START = "mcp_call_start"
    MCP_CALL_END = "mcp_call_end"
    MCP_CALL_ERROR = "mcp_call_error"
    
    # RAG 检索
    RAG_QUERY_START = "rag_query_start"
    RAG_QUERY_END = "rag_query_end"
    RAG_CONTEXT_BUILD = "rag_context_build"
    
    # LLM 调用
    LLM_CALL_START = "llm_call_start"
    LLM_CALL_END = "llm_call_end"
    
    # 推理阶段
    REASONER_START = "reasoner_start"
    REASONER_END = "reasoner_end"


@dataclass
class TraceEvent:
    """追踪事件"""
    event_type: TraceEventType
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: Optional[float] = None
    data: Dict[str, Any] = field(default_factory=dict)
    parent_id: Optional[str] = None
    trace_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "duration_ms": self.duration_ms,
            "data": self.data,
            "parent_id": self.parent_id,
            "trace_id": self.trace_id,
        }


@dataclass
class ToolCallRecord:
    """工具调用记录"""
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    success: bool = True
    error: Optional[str] = None
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "result": self.result,
            "success": self.success,
            "error": self.error,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
        }


class AgentTracer:
    """
    Agent 执行追踪器
    
    使用示例:
    ```python
    tracer = AgentTracer()
    
    with tracer.trace("agent_start", {"query": "北京天气"}):
        with tracer.trace("planner_start"):
            # 规划逻辑
            tracer.log_intent("weather")
        
        with tracer.trace("mcp_call_start", {"tool": "weather_query"}):
            # MCP 调用
            result = await mcp.call(...)
            tracer.log_tool_call("weather_query", args, result)
    
    # 获取追踪报告
    report = tracer.get_report()
    ```
    """
    
    def __init__(self, trace_id: str = None, enable_console: bool = True):
        """
        初始化追踪器
        
        Args:
            trace_id: 追踪 ID
            enable_console: 是否输出到控制台
        """
        import uuid
        self.trace_id = trace_id or f"trace_{uuid.uuid4().hex[:8]}"
        self.enable_console = enable_console
        
        self.events: List[TraceEvent] = []
        self.tool_calls: List[ToolCallRecord] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        self._event_stack: List[TraceEvent] = []
        self._listeners: List[Callable[[TraceEvent], None]] = []
    
    def add_listener(self, listener: Callable[[TraceEvent], None]):
        """添加事件监听器"""
        self._listeners.append(listener)
    
    def _emit_event(self, event: TraceEvent):
        """发送事件"""
        self.events.append(event)
        
        # 控制台输出
        if self.enable_console:
            self._log_to_console(event)
        
        # 通知监听器
        for listener in self._listeners:
            try:
                listener(event)
            except Exception as e:
                logger.error(f"Listener error: {e}")
    
    def _log_to_console(self, event: TraceEvent):
        """输出到控制台"""
        indent = "  " * len(self._event_stack)
        
        # 事件图标
        icons = {
            TraceEventType.AGENT_START: "🚀",
            TraceEventType.AGENT_END: "✅",
            TraceEventType.AGENT_ERROR: "❌",
            TraceEventType.PLANNER_START: "🎯",
            TraceEventType.PLANNER_INTENT: "💡",
            TraceEventType.PLANNER_PLAN: "📋",
            TraceEventType.PLANNER_END: "✓",
            TraceEventType.SKILL_SELECTED: "⚡",
            TraceEventType.SKILL_EXECUTE_START: "▶️",
            TraceEventType.SKILL_EXECUTE_END: "✓",
            TraceEventType.MCP_CALL_START: "🔧",
            TraceEventType.MCP_CALL_END: "✓",
            TraceEventType.MCP_CALL_ERROR: "❌",
            TraceEventType.RAG_QUERY_START: "📚",
            TraceEventType.RAG_QUERY_END: "✓",
            TraceEventType.LLM_CALL_START: "🤖",
            TraceEventType.LLM_CALL_END: "✓",
            TraceEventType.REASONER_START: "🧠",
            TraceEventType.REASONER_END: "✓",
        }
        
        icon = icons.get(event.event_type, "•")
        
        # 格式化消息
        msg = f"{indent}{icon} [{event.event_type.value}]"
        
        if event.duration_ms is not None:
            msg += f" ({event.duration_ms:.1f}ms)"
        
        if event.data:
            # 只显示关键数据
            key_data = {k: v for k, v in event.data.items() 
                       if k in ["query", "intent", "tool", "skill", "result", "error", "count"]}
            if key_data:
                msg += f" {json.dumps(key_data, ensure_ascii=False)}"
        
        logger.info(msg)
    
    def start(self, query: str = None, **kwargs):
        """开始追踪"""
        self.start_time = datetime.now()
        data = {"query": query, **kwargs} if query else kwargs
        
        event = TraceEvent(
            event_type=TraceEventType.AGENT_START,
            data=data,
            trace_id=self.trace_id
        )
        self._emit_event(event)
        return self
    
    def end(self, success: bool = True, result: Any = None, error: str = None):
        """结束追踪"""
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds() * 1000
        
        event = TraceEvent(
            event_type=TraceEventType.AGENT_END if success else TraceEventType.AGENT_ERROR,
            duration_ms=duration,
            data={
                "success": success,
                "result_length": len(str(result)) if result else 0,
                "error": error,
                "total_events": len(self.events),
                "total_tool_calls": len(self.tool_calls),
            },
            trace_id=self.trace_id
        )
        self._emit_event(event)
    
    def trace(self, event_type: TraceEventType, data: Dict[str, Any] = None):
        """
        上下文管理器追踪
        
        Usage:
            with tracer.trace(TraceEventType.PLANNER_START):
                # 规划逻辑
        """
        return _TraceContext(self, event_type, data or {})
    
    def log_event(self, event_type: TraceEventType, data: Dict[str, Any] = None, duration_ms: float = None):
        """记录单个事件"""
        parent_id = self._event_stack[-1].trace_id if self._event_stack else None
        
        event = TraceEvent(
            event_type=event_type,
            data=data or {},
            duration_ms=duration_ms,
            parent_id=parent_id,
            trace_id=self.trace_id
        )
        self._emit_event(event)
    
    def log_intent(self, intent: str, confidence: float = None):
        """记录意图识别"""
        self.log_event(TraceEventType.PLANNER_INTENT, {
            "intent": intent,
            "confidence": confidence
        })
    
    def log_plan(self, plan: List[str]):
        """记录执行计划"""
        self.log_event(TraceEventType.PLANNER_PLAN, {
            "steps": plan,
            "step_count": len(plan)
        })
    
    def log_skill_selected(self, skill_name: str, reason: str = None):
        """记录技能选择"""
        self.log_event(TraceEventType.SKILL_SELECTED, {
            "skill": skill_name,
            "reason": reason
        })
    
    def log_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Dict[str, Any] = None,
        success: bool = True,
        error: str = None,
        duration_ms: float = None
    ):
        """记录工具调用"""
        record = ToolCallRecord(
            tool_name=tool_name,
            arguments=arguments,
            result=result,
            success=success,
            error=error,
            duration_ms=duration_ms,
            end_time=datetime.now()
        )
        self.tool_calls.append(record)
        
        self.log_event(
            TraceEventType.MCP_CALL_END if success else TraceEventType.MCP_CALL_ERROR,
            {
                "tool": tool_name,
                "success": success,
                "error": error,
            },
            duration_ms
        )
    
    def log_rag_query(self, query: str, results_count: int, duration_ms: float = None):
        """记录 RAG 检索"""
        self.log_event(TraceEventType.RAG_QUERY_END, {
            "query": query[:50] + "..." if len(query) > 50 else query,
            "count": results_count,
        }, duration_ms)
    
    def get_report(self) -> Dict[str, Any]:
        """获取追踪报告"""
        total_duration = None
        if self.start_time and self.end_time:
            total_duration = (self.end_time - self.start_time).total_seconds() * 1000
        
        return {
            "trace_id": self.trace_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_duration_ms": total_duration,
            "event_count": len(self.events),
            "tool_call_count": len(self.tool_calls),
            "events": [e.to_dict() for e in self.events],
            "tool_calls": [t.to_dict() for t in self.tool_calls],
        }
    
    def get_timeline(self) -> List[Dict[str, Any]]:
        """获取时间线视图"""
        timeline = []
        for event in self.events:
            timeline.append({
                "time": event.timestamp.strftime("%H:%M:%S.%f")[:-3],
                "type": event.event_type.value,
                "duration_ms": event.duration_ms,
                "summary": self._get_event_summary(event)
            })
        return timeline
    
    def _get_event_summary(self, event: TraceEvent) -> str:
        """获取事件摘要"""
        data = event.data
        
        if event.event_type == TraceEventType.AGENT_START:
            return f"开始处理: {data.get('query', '')[:30]}..."
        elif event.event_type == TraceEventType.PLANNER_INTENT:
            return f"识别意图: {data.get('intent')}"
        elif event.event_type == TraceEventType.SKILL_SELECTED:
            return f"选择技能: {data.get('skill')}"
        elif event.event_type in (TraceEventType.MCP_CALL_START, TraceEventType.MCP_CALL_END):
            return f"MCP 工具: {data.get('tool')}"
        elif event.event_type == TraceEventType.RAG_QUERY_END:
            return f"RAG 检索: {data.get('count')} 条结果"
        elif event.event_type == TraceEventType.AGENT_END:
            return f"完成 (共 {data.get('total_tool_calls', 0)} 次工具调用)"
        
        return event.event_type.value


class _TraceContext:
    """追踪上下文管理器"""
    
    def __init__(self, tracer: AgentTracer, event_type: TraceEventType, data: Dict[str, Any]):
        self.tracer = tracer
        self.event_type = event_type
        self.data = data
        self.start_time = None
        self.event = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.event = TraceEvent(
            event_type=self.event_type,
            data=self.data,
            parent_id=self.tracer._event_stack[-1].trace_id if self.tracer._event_stack else None,
            trace_id=self.tracer.trace_id
        )
        self.tracer._event_stack.append(self.event)
        self.tracer._emit_event(self.event)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        self.tracer._event_stack.pop()
        
        # 记录结束事件
        end_type = self._get_end_event_type()
        if end_type:
            end_event = TraceEvent(
                event_type=end_type,
                duration_ms=duration_ms,
                data={"error": str(exc_val)} if exc_val else {},
                parent_id=self.event.parent_id,
                trace_id=self.tracer.trace_id
            )
            self.tracer._emit_event(end_event)
        
        return False
    
    async def __aenter__(self):
        return self.__enter__()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return self.__exit__(exc_type, exc_val, exc_tb)
    
    def _get_end_event_type(self) -> Optional[TraceEventType]:
        """获取对应的结束事件类型"""
        mapping = {
            TraceEventType.PLANNER_START: TraceEventType.PLANNER_END,
            TraceEventType.SKILL_EXECUTE_START: TraceEventType.SKILL_EXECUTE_END,
            TraceEventType.MCP_CALL_START: TraceEventType.MCP_CALL_END,
            TraceEventType.RAG_QUERY_START: TraceEventType.RAG_QUERY_END,
            TraceEventType.LLM_CALL_START: TraceEventType.LLM_CALL_END,
            TraceEventType.REASONER_START: TraceEventType.REASONER_END,
        }
        return mapping.get(self.event_type)


# 全局追踪器
_current_tracer: Optional[AgentTracer] = None


def get_tracer() -> Optional[AgentTracer]:
    """获取当前追踪器"""
    return _current_tracer


def set_tracer(tracer: AgentTracer):
    """设置当前追踪器"""
    global _current_tracer
    _current_tracer = tracer


def create_tracer(trace_id: str = None, enable_console: bool = True) -> AgentTracer:
    """创建并设置新追踪器"""
    tracer = AgentTracer(trace_id=trace_id, enable_console=enable_console)
    set_tracer(tracer)
    return tracer
