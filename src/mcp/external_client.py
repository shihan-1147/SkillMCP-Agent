"""
外部 MCP 服务调用客户端

调用外部 MCP 服务器（如 12306-mcp、高德地图等）
"""

import asyncio
import json
import subprocess
from typing import Any, Dict, List, Optional

import httpx

from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger("mcp.external_client")


class ExternalMCPClient:
    """
    外部 MCP 服务客户端

    用于调用外部 MCP 服务器的工具，如 12306-mcp、amap-maps-mcp 等
    这些服务通过 npx 启动，使用标准输入/输出通信
    """

    def __init__(self):
        self.settings = get_settings()
        self._12306_available = False
        self._amap_available = False

    async def call_12306_tickets(
        self,
        from_city: str,
        to_city: str,
        date: str,
        train_type: str = "GD",  # G=高铁, D=动车, GD=高铁+动车
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        调用 12306 MCP 查询火车票

        注意：此方法需要通过 VS Code MCP 协议调用
        实际实现需要配合 VS Code MCP 客户端
        """
        # 这里我们使用 HTTP 代理方式调用
        # 实际的 MCP 调用需要通过 VS Code 的 MCP 客户端

        logger.info(f"12306 query: {from_city} -> {to_city} on {date}")

        return {
            "success": False,
            "error": "外部 MCP 调用需要通过 VS Code MCP 客户端",
            "hint": "请直接使用 VS Code 中的 12306-mcp 工具",
        }


# 全局客户端实例
_external_mcp_client: Optional[ExternalMCPClient] = None


def get_external_mcp_client() -> ExternalMCPClient:
    """获取外部 MCP 客户端"""
    global _external_mcp_client
    if _external_mcp_client is None:
        _external_mcp_client = ExternalMCPClient()
    return _external_mcp_client
