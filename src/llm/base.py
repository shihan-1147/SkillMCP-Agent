"""
LLM 基类定义
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator


class BaseLLM(ABC):
    """
    LLM 调用的抽象基类
    
    所有 LLM 实现都必须继承此类
    """
    
    def __init__(self, model: str = None, **kwargs):
        """
        初始化 LLM
        
        Args:
            model: 模型名称
            **kwargs: 其他配置参数
        """
        self.model = model
        self.config = kwargs
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = None,
        **kwargs
    ) -> str:
        """
        发送聊天请求
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大生成 token 数
            **kwargs: 其他参数
            
        Returns:
            模型响应文本
        """
        pass
    
    @abstractmethod
    async def chat_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        带工具调用的聊天请求
        
        Args:
            messages: 消息列表
            tools: 工具定义列表
            temperature: 温度参数
            **kwargs: 其他参数
            
        Returns:
            包含响应和工具调用的字典
        """
        pass
    
    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        流式聊天（可选实现）
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            **kwargs: 其他参数
            
        Yields:
            响应文本片段
        """
        # 默认实现：非流式
        response = await self.chat(messages, temperature, **kwargs)
        yield response
    
    def count_tokens(self, text: str) -> int:
        """
        计算 token 数量（可选实现）
        
        Args:
            text: 输入文本
            
        Returns:
            token 数量
        """
        # 简单估算：约 4 个字符一个 token
        return len(text) // 4
