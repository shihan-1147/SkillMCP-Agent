"""
Ollama LLM 客户端

支持本地部署的 Ollama 模型调用
"""

import json
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx

from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger("core.ollama")


class OllamaClient:
    """
    Ollama LLM 客户端

    支持：
    - 普通对话
    - 流式对话
    - 工具调用（Tool Calling）
    """

    def __init__(self, base_url: str = None, model: str = None, timeout: float = 120.0):
        """
        初始化 Ollama 客户端

        Args:
            base_url: Ollama API 地址
            model: 默认模型
            timeout: 请求超时时间
        """
        settings = get_settings()
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.model = model or settings.ollama_model
        self.timeout = timeout
        self._client = None

        logger.info(
            f"OllamaClient initialized: model={self.model}, base_url={self.base_url}"
        )

    def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url, timeout=httpx.Timeout(self.timeout)
            )
        return self._client

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        tools: List[Dict] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        发送聊天请求

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数
            tools: 工具定义列表（用于 Tool Calling）

        Returns:
            响应字典
        """
        client = self._get_client()
        model = model or self.model

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        # 添加工具定义（如果支持）
        if tools:
            payload["tools"] = tools

        try:
            response = await client.post("/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()

            return {
                "success": True,
                "content": data.get("message", {}).get("content", ""),
                "role": data.get("message", {}).get("role", "assistant"),
                "tool_calls": data.get("message", {}).get("tool_calls", []),
                "model": model,
                "done": data.get("done", True),
                "total_duration": data.get("total_duration"),
                "eval_count": data.get("eval_count"),
            }

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Ollama HTTP error: {e.response.status_code} - {e.response.text}"
            )
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "content": "",
            }
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            return {"success": False, "error": str(e), "content": ""}

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """
        流式聊天

        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数

        Yields:
            响应文本片段
        """
        client = self._get_client()
        model = model or self.model

        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            async with client.stream("POST", "/api/chat", json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            content = data.get("message", {}).get("content", "")
                            if content:
                                yield content
                            if data.get("done", False):
                                break
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            logger.error(f"Ollama stream error: {e}")
            yield f"[Error: {str(e)}]"

    async def generate(
        self,
        prompt: str,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> str:
        """
        简单文本生成

        Args:
            prompt: 输入提示
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数

        Returns:
            生成的文本
        """
        result = await self.chat(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        return result.get("content", "")

    async def check_model(self, model: str = None) -> bool:
        """
        检查模型是否可用

        Args:
            model: 模型名称

        Returns:
            是否可用
        """
        client = self._get_client()
        model = model or self.model

        try:
            response = await client.post("/api/show", json={"name": model})
            return response.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> List[str]:
        """
        列出可用模型

        Returns:
            模型名称列表
        """
        client = self._get_client()

        try:
            response = await client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []

    async def close(self):
        """关闭客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None


# 全局客户端实例
_ollama_client: Optional[OllamaClient] = None


def get_ollama_client() -> OllamaClient:
    """获取全局 Ollama 客户端"""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client
