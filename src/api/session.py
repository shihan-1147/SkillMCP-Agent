"""
会话管理器

管理多轮对话的会话状态
"""

import asyncio
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.core.logging import get_logger

from .schemas import ChatMessage

logger = get_logger("api.session")


@dataclass
class Session:
    """
    会话对象

    存储单个会话的状态和历史
    """

    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    messages: List[ChatMessage] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: str, content: str) -> ChatMessage:
        """添加消息"""
        message = ChatMessage(role=role, content=content)
        self.messages.append(message)
        self.last_active = datetime.now()
        return message

    def get_history(self, limit: int = 20) -> List[ChatMessage]:
        """获取历史消息"""
        return self.messages[-limit:] if limit else self.messages

    def get_history_for_llm(self, limit: int = 10) -> List[Dict[str, str]]:
        """获取适合 LLM 的历史格式"""
        history = self.get_history(limit)
        return [{"role": m.role, "content": m.content} for m in history]

    @property
    def message_count(self) -> int:
        return len(self.messages)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
            "message_count": self.message_count,
        }


class SessionManager:
    """
    会话管理器

    功能：
    - 创建和管理会话
    - 存储对话历史
    - 自动清理过期会话

    使用示例:
    ```python
    manager = SessionManager()

    # 获取或创建会话
    session = manager.get_or_create("session_123")

    # 添加消息
    session.add_message("user", "你好")
    session.add_message("assistant", "你好！有什么可以帮助你的？")

    # 获取历史
    history = session.get_history_for_llm()
    ```
    """

    def __init__(
        self,
        max_sessions: int = 1000,
        session_ttl_hours: int = 24,
        cleanup_interval_minutes: int = 30,
    ):
        """
        初始化会话管理器

        Args:
            max_sessions: 最大会话数
            session_ttl_hours: 会话过期时间（小时）
            cleanup_interval_minutes: 清理间隔（分钟）
        """
        self.max_sessions = max_sessions
        self.session_ttl = timedelta(hours=session_ttl_hours)
        self.cleanup_interval = timedelta(minutes=cleanup_interval_minutes)

        self._sessions: OrderedDict[str, Session] = OrderedDict()
        self._last_cleanup = datetime.now()
        self._lock = asyncio.Lock()

    def generate_session_id(self) -> str:
        """生成唯一会话 ID"""
        return f"sess_{uuid.uuid4().hex[:12]}"

    async def get_or_create(self, session_id: str = None) -> Session:
        """
        获取或创建会话

        Args:
            session_id: 会话 ID，为空则创建新会话

        Returns:
            Session 对象
        """
        async with self._lock:
            # 检查是否需要清理
            await self._maybe_cleanup()

            if session_id and session_id in self._sessions:
                session = self._sessions[session_id]
                session.last_active = datetime.now()
                # 移到末尾（LRU）
                self._sessions.move_to_end(session_id)
                return session

            # 创建新会话
            new_id = session_id or self.generate_session_id()
            session = Session(session_id=new_id)

            # 检查容量
            if len(self._sessions) >= self.max_sessions:
                # 移除最旧的会话
                oldest_id = next(iter(self._sessions))
                del self._sessions[oldest_id]
                logger.debug(f"Removed oldest session: {oldest_id}")

            self._sessions[new_id] = session
            logger.info(f"Created new session: {new_id}")

            return session

    async def get(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        async with self._lock:
            return self._sessions.get(session_id)

    async def delete(self, session_id: str) -> bool:
        """删除会话"""
        async with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.info(f"Deleted session: {session_id}")
                return True
            return False

    async def list_sessions(self, limit: int = 100, offset: int = 0) -> List[Session]:
        """列出会话"""
        async with self._lock:
            sessions = list(self._sessions.values())
            # 按最后活跃时间倒序
            sessions.sort(key=lambda s: s.last_active, reverse=True)
            return sessions[offset : offset + limit]

    async def count(self) -> int:
        """获取会话数量"""
        return len(self._sessions)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "active_sessions": len(self._sessions),
            "max_sessions": self.max_sessions,
            "session_ttl_hours": self.session_ttl.total_seconds() / 3600,
        }

    async def _maybe_cleanup(self) -> None:
        """可能执行清理"""
        now = datetime.now()
        if now - self._last_cleanup < self.cleanup_interval:
            return

        self._last_cleanup = now
        expired = []

        for session_id, session in self._sessions.items():
            if now - session.last_active > self.session_ttl:
                expired.append(session_id)

        for session_id in expired:
            del self._sessions[session_id]

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")

    async def clear_all(self) -> int:
        """清除所有会话"""
        async with self._lock:
            count = len(self._sessions)
            self._sessions.clear()
            logger.info(f"Cleared all {count} sessions")
            return count


# 全局会话管理器实例
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """获取全局会话管理器"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
