"""
Tool 调用记录器

完整记录所有 MCP 工具调用：
- 调用参数
- 返回结果
- 执行时间
- 调用链路

支持：
- 持久化存储 (JSON/SQLite)
- 查询和分析
- 导出报告
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import json
import asyncio
from collections import defaultdict

from src.core.logging import get_logger
from src.core.config import get_settings

logger = get_logger("tool.recorder")


@dataclass
class ToolCallEntry:
    """工具调用条目"""
    id: str
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    success: bool = True
    error: Optional[str] = None
    
    # 时间信息
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    
    # 上下文信息
    session_id: Optional[str] = None
    trace_id: Optional[str] = None
    skill_name: Optional[str] = None
    user_query: Optional[str] = None
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def complete(self, result: Dict[str, Any] = None, error: str = None):
        """完成调用"""
        self.end_time = datetime.now()
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        
        if error:
            self.success = False
            self.error = error
        else:
            self.success = True
            self.result = result
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "result": self.result,
            "success": self.success,
            "error": self.error,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "session_id": self.session_id,
            "trace_id": self.trace_id,
            "skill_name": self.skill_name,
            "user_query": self.user_query,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolCallEntry":
        return cls(
            id=data["id"],
            tool_name=data["tool_name"],
            arguments=data.get("arguments", {}),
            result=data.get("result"),
            success=data.get("success", True),
            error=data.get("error"),
            start_time=datetime.fromisoformat(data["start_time"]) if data.get("start_time") else datetime.now(),
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            duration_ms=data.get("duration_ms"),
            session_id=data.get("session_id"),
            trace_id=data.get("trace_id"),
            skill_name=data.get("skill_name"),
            user_query=data.get("user_query"),
            metadata=data.get("metadata", {}),
        )


class ToolRecorder:
    """
    工具调用记录器
    
    使用示例:
    ```python
    recorder = ToolRecorder()
    
    # 开始记录
    entry = recorder.start_call(
        tool_name="weather_query",
        arguments={"city": "北京"},
        session_id="session_123"
    )
    
    # 执行工具调用
    result = await mcp.call("weather_query", {"city": "北京"})
    
    # 完成记录
    recorder.end_call(entry.id, result=result)
    
    # 查询记录
    calls = recorder.get_calls_by_tool("weather_query")
    stats = recorder.get_statistics()
    ```
    """
    
    def __init__(self, storage_path: str = None, max_entries: int = 10000):
        """
        初始化记录器
        
        Args:
            storage_path: 存储路径
            max_entries: 最大记录数
        """
        self.storage_path = Path(storage_path) if storage_path else None
        self.max_entries = max_entries
        
        self.entries: Dict[str, ToolCallEntry] = {}
        self._call_order: List[str] = []  # 保持顺序
        
        # 统计缓存
        self._stats_cache: Optional[Dict[str, Any]] = None
        self._stats_cache_time: Optional[datetime] = None
        
        # 从存储加载
        if self.storage_path and self.storage_path.exists():
            self._load_from_storage()
    
    def start_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        session_id: str = None,
        trace_id: str = None,
        skill_name: str = None,
        user_query: str = None,
        **metadata
    ) -> ToolCallEntry:
        """
        开始记录工具调用
        
        Args:
            tool_name: 工具名称
            arguments: 调用参数
            session_id: 会话 ID
            trace_id: 追踪 ID
            skill_name: 技能名称
            user_query: 用户查询
            **metadata: 额外元数据
        
        Returns:
            ToolCallEntry: 调用条目
        """
        import uuid
        entry_id = f"call_{uuid.uuid4().hex[:12]}"
        
        entry = ToolCallEntry(
            id=entry_id,
            tool_name=tool_name,
            arguments=arguments,
            session_id=session_id,
            trace_id=trace_id,
            skill_name=skill_name,
            user_query=user_query,
            metadata=metadata,
        )
        
        self.entries[entry_id] = entry
        self._call_order.append(entry_id)
        
        # 清理旧记录
        self._cleanup_old_entries()
        
        # 清除统计缓存
        self._stats_cache = None
        
        logger.debug(f"Started tool call: {tool_name} ({entry_id})")
        return entry
    
    def end_call(
        self,
        entry_id: str,
        result: Dict[str, Any] = None,
        error: str = None
    ) -> Optional[ToolCallEntry]:
        """
        完成工具调用记录
        
        Args:
            entry_id: 条目 ID
            result: 调用结果
            error: 错误信息
        
        Returns:
            ToolCallEntry: 更新后的条目
        """
        entry = self.entries.get(entry_id)
        if not entry:
            logger.warning(f"Tool call entry not found: {entry_id}")
            return None
        
        entry.complete(result=result, error=error)
        
        # 清除统计缓存
        self._stats_cache = None
        
        # 持久化
        if self.storage_path:
            self._save_to_storage()
        
        status = "success" if entry.success else "failed"
        logger.debug(f"Completed tool call: {entry.tool_name} ({status}, {entry.duration_ms:.1f}ms)")
        
        return entry
    
    def record_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Dict[str, Any] = None,
        error: str = None,
        duration_ms: float = None,
        **context
    ) -> ToolCallEntry:
        """
        一次性记录完整的工具调用
        
        Args:
            tool_name: 工具名称
            arguments: 调用参数
            result: 调用结果
            error: 错误信息
            duration_ms: 执行时间
            **context: 上下文信息
        
        Returns:
            ToolCallEntry: 调用条目
        """
        entry = self.start_call(tool_name, arguments, **context)
        entry.complete(result=result, error=error)
        if duration_ms is not None:
            entry.duration_ms = duration_ms
        
        if self.storage_path:
            self._save_to_storage()
        
        return entry
    
    def get_call(self, entry_id: str) -> Optional[ToolCallEntry]:
        """获取调用记录"""
        return self.entries.get(entry_id)
    
    def get_all_calls(self) -> List[ToolCallEntry]:
        """获取所有调用记录"""
        return [self.entries[id] for id in self._call_order if id in self.entries]
    
    def get_calls_by_tool(self, tool_name: str) -> List[ToolCallEntry]:
        """按工具名获取调用记录"""
        return [e for e in self.get_all_calls() if e.tool_name == tool_name]
    
    def get_calls_by_session(self, session_id: str) -> List[ToolCallEntry]:
        """按会话获取调用记录"""
        return [e for e in self.get_all_calls() if e.session_id == session_id]
    
    def get_calls_by_trace(self, trace_id: str) -> List[ToolCallEntry]:
        """按追踪 ID 获取调用记录"""
        return [e for e in self.get_all_calls() if e.trace_id == trace_id]
    
    def get_recent_calls(self, limit: int = 100) -> List[ToolCallEntry]:
        """获取最近的调用记录"""
        return self.get_all_calls()[-limit:]
    
    def get_failed_calls(self) -> List[ToolCallEntry]:
        """获取失败的调用记录"""
        return [e for e in self.get_all_calls() if not e.success]
    
    def get_statistics(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计数据字典
        """
        # 检查缓存
        if not force_refresh and self._stats_cache:
            cache_age = datetime.now() - self._stats_cache_time
            if cache_age < timedelta(seconds=30):
                return self._stats_cache
        
        all_calls = self.get_all_calls()
        
        # 基础统计
        total_calls = len(all_calls)
        successful_calls = sum(1 for e in all_calls if e.success)
        failed_calls = total_calls - successful_calls
        
        # 按工具统计
        tool_stats = defaultdict(lambda: {"count": 0, "success": 0, "total_duration_ms": 0})
        for entry in all_calls:
            stats = tool_stats[entry.tool_name]
            stats["count"] += 1
            if entry.success:
                stats["success"] += 1
            if entry.duration_ms:
                stats["total_duration_ms"] += entry.duration_ms
        
        # 计算平均时间
        for tool_name, stats in tool_stats.items():
            if stats["count"] > 0:
                stats["avg_duration_ms"] = stats["total_duration_ms"] / stats["count"]
                stats["success_rate"] = stats["success"] / stats["count"] * 100
        
        # 时间分布
        durations = [e.duration_ms for e in all_calls if e.duration_ms]
        
        result = {
            "total_calls": total_calls,
            "successful_calls": successful_calls,
            "failed_calls": failed_calls,
            "success_rate": successful_calls / total_calls * 100 if total_calls > 0 else 0,
            "tool_stats": dict(tool_stats),
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            "min_duration_ms": min(durations) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
            "unique_tools": len(tool_stats),
            "unique_sessions": len(set(e.session_id for e in all_calls if e.session_id)),
        }
        
        # 更新缓存
        self._stats_cache = result
        self._stats_cache_time = datetime.now()
        
        return result
    
    def export_report(self, format: str = "json") -> str:
        """
        导出报告
        
        Args:
            format: 格式 (json/markdown)
        
        Returns:
            报告内容
        """
        stats = self.get_statistics()
        calls = self.get_all_calls()
        
        if format == "json":
            return json.dumps({
                "statistics": stats,
                "calls": [e.to_dict() for e in calls],
                "generated_at": datetime.now().isoformat(),
            }, ensure_ascii=False, indent=2)
        
        elif format == "markdown":
            lines = [
                "# Tool Call Report",
                "",
                f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "## Statistics",
                "",
                f"- Total Calls: {stats['total_calls']}",
                f"- Success Rate: {stats['success_rate']:.1f}%",
                f"- Average Duration: {stats['avg_duration_ms']:.1f}ms",
                f"- Unique Tools: {stats['unique_tools']}",
                "",
                "## Tool Breakdown",
                "",
                "| Tool | Calls | Success Rate | Avg Duration |",
                "|------|-------|--------------|--------------|",
            ]
            
            for tool_name, tool_stat in stats["tool_stats"].items():
                lines.append(
                    f"| {tool_name} | {tool_stat['count']} | "
                    f"{tool_stat['success_rate']:.1f}% | "
                    f"{tool_stat.get('avg_duration_ms', 0):.1f}ms |"
                )
            
            lines.extend([
                "",
                "## Recent Calls",
                "",
            ])
            
            for entry in calls[-10:]:
                status = "✅" if entry.success else "❌"
                lines.append(
                    f"- {status} `{entry.tool_name}` - {entry.duration_ms:.1f}ms"
                )
            
            return "\n".join(lines)
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def clear(self):
        """清除所有记录"""
        self.entries.clear()
        self._call_order.clear()
        self._stats_cache = None
        
        if self.storage_path and self.storage_path.exists():
            self.storage_path.unlink()
    
    def _cleanup_old_entries(self):
        """清理旧记录"""
        while len(self._call_order) > self.max_entries:
            old_id = self._call_order.pop(0)
            self.entries.pop(old_id, None)
    
    def _save_to_storage(self):
        """保存到存储"""
        if not self.storage_path:
            return
        
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "entries": [e.to_dict() for e in self.get_all_calls()],
            "saved_at": datetime.now().isoformat(),
        }
        
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load_from_storage(self):
        """从存储加载"""
        if not self.storage_path or not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for entry_data in data.get("entries", []):
                entry = ToolCallEntry.from_dict(entry_data)
                self.entries[entry.id] = entry
                self._call_order.append(entry.id)
            
            logger.info(f"Loaded {len(self.entries)} tool call records")
        
        except Exception as e:
            logger.error(f"Failed to load tool call records: {e}")


# 全局记录器
_global_recorder: Optional[ToolRecorder] = None


def get_tool_recorder() -> ToolRecorder:
    """获取全局工具记录器"""
    global _global_recorder
    if _global_recorder is None:
        settings = get_settings()
        storage_path = Path(settings.data_dir) / "tool_calls.json"
        _global_recorder = ToolRecorder(storage_path=str(storage_path))
    return _global_recorder


def record_tool_call(
    tool_name: str,
    arguments: Dict[str, Any],
    result: Dict[str, Any] = None,
    error: str = None,
    **context
) -> ToolCallEntry:
    """便捷函数：记录工具调用"""
    recorder = get_tool_recorder()
    return recorder.record_call(tool_name, arguments, result, error, **context)
