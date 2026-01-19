"""
记忆管理器
统一管理短期和长期记忆
"""
from typing import List, Dict, Any, Optional
from .short_term import ShortTermMemory
from .long_term import LongTermMemory
from ..schemas.message import Message, MessageRole
from src.core.logging import get_logger

logger = get_logger("memory.manager")


class MemoryManager:
    """
    记忆管理器
    - 统一管理短期和长期记忆
    - 提供记忆整合能力
    - 支持上下文构建
    """
    
    def __init__(
        self,
        short_term: ShortTermMemory = None,
        long_term: LongTermMemory = None
    ):
        """
        初始化记忆管理器
        
        Args:
            short_term: 短期记忆实例
            long_term: 长期记忆实例
        """
        self.short_term = short_term or ShortTermMemory()
        self.long_term = long_term or LongTermMemory()
        logger.debug("MemoryManager initialized")
    
    def add_user_input(self, content: str) -> Message:
        """
        添加用户输入
        
        Args:
            content: 用户输入内容
            
        Returns:
            消息对象
        """
        return self.short_term.add_user_message(content)
    
    def add_agent_response(self, content: str) -> Message:
        """
        添加 Agent 响应
        
        Args:
            content: Agent 响应内容
            
        Returns:
            消息对象
        """
        return self.short_term.add_assistant_message(content)
    
    def set_system_prompt(self, prompt: str) -> None:
        """设置系统提示词"""
        self.short_term.set_system_message(prompt)
    
    def get_conversation_context(self) -> List[Dict[str, Any]]:
        """
        获取对话上下文（用于 LLM 调用）
        
        Returns:
            LLM 格式的消息列表
        """
        return self.short_term.get_messages_for_llm()
    
    def get_enhanced_context(self, current_query: str) -> Dict[str, Any]:
        """
        获取增强上下文
        包含短期记忆 + 相关的长期记忆
        
        Args:
            current_query: 当前查询
            
        Returns:
            增强上下文字典
        """
        # 短期对话历史
        conversation = self.short_term.get_context_summary()
        
        # 相关历史记录
        relevant_history = self.long_term.get_relevant_history(current_query, limit=3)
        
        # 用户偏好
        preferences = self.long_term.retrieve(category="preference", limit=5)
        
        return {
            "conversation_history": conversation,
            "relevant_past_tasks": relevant_history,
            "user_preferences": [p.content for p in preferences],
            "messages_for_llm": self.get_conversation_context()
        }
    
    def save_task_result(self, task_id: str, query: str, result: str) -> None:
        """
        保存任务结果到长期记忆
        
        Args:
            task_id: 任务ID
            query: 原始查询
            result: 执行结果
        """
        self.long_term.store_task_summary(task_id, query, result)
        logger.debug(f"Task result saved to long-term memory: {task_id}")
    
    def learn_preference(self, preference: str) -> None:
        """
        学习用户偏好
        
        Args:
            preference: 偏好内容
        """
        self.long_term.store_user_preference(preference)
        logger.info(f"Learned new preference: {preference[:50]}...")
    
    def clear_conversation(self) -> None:
        """清空当前对话（短期记忆）"""
        self.short_term.clear()
        logger.debug("Conversation cleared")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        return {
            "short_term": self.short_term.to_dict(),
            "long_term": self.long_term.get_stats()
        }
