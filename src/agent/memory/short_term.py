"""
短期记忆模块
存储当前对话的上下文信息
"""
from typing import List, Optional, Dict, Any
from collections import deque
from ..schemas.message import Message, MessageRole
from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger("memory.short_term")


class ShortTermMemory:
    """
    短期记忆
    - 保存当前会话的消息历史
    - 支持滑动窗口限制长度
    - 支持消息检索
    """
    
    def __init__(self, max_messages: int = None):
        """
        初始化短期记忆
        
        Args:
            max_messages: 最大消息数量，超出后移除最早的消息
        """
        self.max_messages = max_messages or settings.max_history_length
        self._messages: deque[Message] = deque(maxlen=self.max_messages)
        self._system_message: Optional[Message] = None
        logger.debug(f"ShortTermMemory initialized with max_messages={self.max_messages}")
    
    def add_message(self, message: Message) -> None:
        """
        添加消息到记忆
        
        Args:
            message: 消息对象
        """
        if message.role == MessageRole.SYSTEM:
            # 系统消息单独存储，不受滑动窗口限制
            self._system_message = message
            logger.debug("System message updated")
        else:
            self._messages.append(message)
            logger.debug(f"Added {message.role} message, total: {len(self._messages)}")
    
    def add_user_message(self, content: str) -> Message:
        """添加用户消息的便捷方法"""
        message = Message(role=MessageRole.USER, content=content)
        self.add_message(message)
        return message
    
    def add_assistant_message(self, content: str) -> Message:
        """添加助手消息的便捷方法"""
        message = Message(role=MessageRole.ASSISTANT, content=content)
        self.add_message(message)
        return message
    
    def get_messages(self, include_system: bool = True) -> List[Message]:
        """
        获取所有消息
        
        Args:
            include_system: 是否包含系统消息
            
        Returns:
            消息列表
        """
        messages = []
        if include_system and self._system_message:
            messages.append(self._system_message)
        messages.extend(list(self._messages))
        return messages
    
    def get_messages_for_llm(self) -> List[Dict[str, Any]]:
        """
        获取适合发送给 LLM 的消息格式
        
        Returns:
            LLM 格式的消息列表
        """
        return [msg.to_llm_format() for msg in self.get_messages()]
    
    def get_last_n_messages(self, n: int) -> List[Message]:
        """
        获取最近 n 条消息
        
        Args:
            n: 消息数量
            
        Returns:
            消息列表
        """
        messages = list(self._messages)
        return messages[-n:] if n < len(messages) else messages
    
    def get_context_summary(self) -> str:
        """
        获取上下文摘要
        用于传递给 Planner 做任务规划
        
        Returns:
            上下文摘要字符串
        """
        messages = self.get_last_n_messages(5)
        summary_parts = []
        for msg in messages:
            role = "用户" if msg.role == MessageRole.USER else "助手"
            # 截断过长的内容
            content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
            summary_parts.append(f"{role}: {content}")
        return "\n".join(summary_parts)
    
    def clear(self) -> None:
        """清空所有消息"""
        self._messages.clear()
        self._system_message = None
        logger.debug("ShortTermMemory cleared")
    
    def set_system_message(self, content: str) -> None:
        """设置系统消息"""
        self._system_message = Message(role=MessageRole.SYSTEM, content=content)
    
    def __len__(self) -> int:
        """返回消息数量（不含系统消息）"""
        return len(self._messages)
    
    def to_dict(self) -> Dict[str, Any]:
        """导出为字典格式"""
        return {
            "system_message": self._system_message.content if self._system_message else None,
            "messages": [
                {"role": m.role, "content": m.content[:100]}
                for m in self._messages
            ],
            "total_count": len(self._messages)
        }
