"""
OpenAI LLM 客户端实现
"""
import json
from typing import List, Dict, Any, Optional, AsyncIterator
import httpx
from openai import AsyncOpenAI

from .base import BaseLLM
from src.core.config import settings
from src.core.logging import get_logger
from src.core.exceptions import LLMException

logger = get_logger("llm.openai")


class OpenAIClient(BaseLLM):
    """
    OpenAI API 客户端
    
    支持：
    - 标准聊天
    - 工具调用 (Function Calling)
    - 流式响应
    """
    
    def __init__(
        self,
        api_key: str = None,
        base_url: str = None,
        model: str = None,
        **kwargs
    ):
        """
        初始化 OpenAI 客户端
        
        Args:
            api_key: API 密钥
            base_url: API 基础 URL（用于代理或兼容接口）
            model: 默认模型
            **kwargs: 其他配置
        """
        super().__init__(model=model or settings.openai_model, **kwargs)
        
        self.api_key = api_key or settings.openai_api_key
        self.base_url = base_url or settings.openai_base_url
        
        # 初始化异步客户端
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        
        self.client = AsyncOpenAI(**client_kwargs)
        
        logger.debug(f"OpenAI client initialized with model: {self.model}")
    
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
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大 token 数
            **kwargs: 其他参数
            
        Returns:
            模型响应文本
        """
        try:
            logger.debug(f"Sending chat request with {len(messages)} messages")
            
            request_params = {
                "model": kwargs.get("model", self.model),
                "messages": messages,
                "temperature": temperature,
            }
            
            if max_tokens:
                request_params["max_tokens"] = max_tokens
            
            response = await self.client.chat.completions.create(**request_params)
            
            content = response.choices[0].message.content
            logger.debug(f"Received response: {content[:100]}...")
            
            return content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise LLMException(
                message=f"LLM 调用失败: {str(e)}",
                details={"model": self.model}
            )
    
    async def chat_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        带工具调用的聊天
        
        Args:
            messages: 消息列表
            tools: 工具定义列表（OpenAI 格式）
            temperature: 温度参数
            **kwargs: 其他参数
            
        Returns:
            包含响应内容和工具调用的字典
        """
        try:
            logger.debug(f"Sending chat request with {len(tools)} tools")
            
            response = await self.client.chat.completions.create(
                model=kwargs.get("model", self.model),
                messages=messages,
                tools=tools,
                tool_choice=kwargs.get("tool_choice", "auto"),
                temperature=temperature,
            )
            
            message = response.choices[0].message
            
            result = {
                "content": message.content,
                "tool_calls": [],
                "finish_reason": response.choices[0].finish_reason
            }
            
            # 解析工具调用
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    result["tool_calls"].append({
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "arguments": json.loads(tool_call.function.arguments)
                    })
            
            logger.debug(f"Response with {len(result['tool_calls'])} tool calls")
            return result
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise LLMException(
                message=f"LLM 工具调用失败: {str(e)}",
                details={"model": self.model, "tools_count": len(tools)}
            )
    
    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        流式聊天
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            **kwargs: 其他参数
            
        Yields:
            响应文本片段
        """
        try:
            stream = await self.client.chat.completions.create(
                model=kwargs.get("model", self.model),
                messages=messages,
                temperature=temperature,
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI streaming error: {str(e)}")
            raise LLMException(
                message=f"LLM 流式调用失败: {str(e)}",
                details={"model": self.model}
            )
    
    def format_tools_for_api(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        将工具定义转换为 OpenAI API 格式
        
        Args:
            tools: 工具定义列表
            
        Returns:
            OpenAI 格式的工具列表
        """
        formatted = []
        for tool in tools:
            formatted.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {
                        "type": "object",
                        "properties": {},
                        "required": []
                    })
                }
            })
        return formatted
