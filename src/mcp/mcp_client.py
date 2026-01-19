"""
MCP Client 实现

使用官方 MCP Python SDK 连接外部 MCP Server
支持 stdio / SSE / Streamable HTTP 传输方式
"""

import asyncio
import json
import os
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger("mcp.mcp_client")


class MCPClientManager:
    """
    MCP Client 管理器

    管理多个 MCP Server 连接，支持：
    - 12306-mcp: 火车票查询
    - amap-mcp: 高德地图 API
    - 其他 MCP Server
    """

    def __init__(self):
        self.settings = get_settings()
        self.exit_stack = AsyncExitStack()
        self._sessions: Dict[str, ClientSession] = {}
        self._tools_cache: Dict[str, List[Dict]] = {}
        self._initialized = False

    async def initialize(self):
        """初始化 MCP Client 管理器"""
        if self._initialized:
            return

        logger.info("Initializing MCP Client Manager...")

        # 尝试连接已配置的 MCP Server
        await self._connect_configured_servers()

        self._initialized = True
        logger.info(
            f"MCP Client Manager initialized, {len(self._sessions)} servers connected"
        )

    async def _connect_configured_servers(self):
        """连接配置的 MCP Server"""
        # 从环境变量或配置文件获取 MCP Server 配置
        mcp_config = self._load_mcp_config()

        for server_name, config in mcp_config.items():
            try:
                await self._connect_server(server_name, config)
            except Exception as e:
                logger.warning(f"Failed to connect to MCP server {server_name}: {e}")

    def _load_mcp_config(self) -> Dict[str, Dict]:
        """
        加载 MCP Server 配置

        优先级:
        1. 环境变量 MCP_SERVERS_CONFIG
        2. 用户配置文件 ~/.mcp/config.json
        3. 项目配置文件 ./mcp_config.json
        """
        config = {}

        # 检查环境变量
        env_config = os.environ.get("MCP_SERVERS_CONFIG")
        if env_config:
            try:
                config = json.loads(env_config)
                logger.info("Loaded MCP config from environment variable")
                return config
            except json.JSONDecodeError:
                pass

        # 检查项目配置文件
        project_config_path = os.path.join(os.getcwd(), "mcp_config.json")
        if os.path.exists(project_config_path):
            try:
                with open(project_config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                logger.info(f"Loaded MCP config from {project_config_path}")
                return config
            except Exception as e:
                logger.warning(f"Failed to load {project_config_path}: {e}")

        # 返回默认配置（尝试连接常用的 MCP Server）
        return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Dict]:
        """获取默认 MCP Server 配置"""
        return {
            # 12306 MCP Server (npm 包)
            "12306-mcp": {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "12306-mcp"],
                "enabled": True,
            },
            # 高德地图 MCP Server (npm 包)
            # "amap-mcp": {
            #     "transport": "stdio",
            #     "command": "npx",
            #     "args": ["-y", "@anthropic/amap-maps-mcp"],
            #     "env": {"AMAP_API_KEY": self.settings.amap_api_key},
            #     "enabled": False  # 需要 API key
            # }
        }

    async def _connect_server(self, name: str, config: Dict):
        """
        连接单个 MCP Server

        Args:
            name: 服务器名称
            config: 服务器配置
        """
        if not config.get("enabled", True):
            logger.info(f"MCP server {name} is disabled, skipping")
            return

        transport = config.get("transport", "stdio")

        if transport == "stdio":
            await self._connect_stdio_server(name, config)
        elif transport == "sse":
            await self._connect_sse_server(name, config)
        else:
            logger.warning(f"Unsupported transport type: {transport}")

    async def _connect_stdio_server(self, name: str, config: Dict):
        """通过 stdio 连接 MCP Server"""
        command = config.get("command", "npx")
        args = config.get("args", [])
        env = config.get("env", None)

        # 合并环境变量
        if env:
            full_env = {**os.environ, **env}
        else:
            full_env = None

        server_params = StdioServerParameters(command=command, args=args, env=full_env)

        logger.info(
            f"Connecting to MCP server {name} via stdio: {command} {' '.join(args)}"
        )

        try:
            # 使用 exit_stack 管理连接生命周期
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read_stream, write_stream = stdio_transport

            session = await self.exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )

            # 初始化会话
            await session.initialize()

            # 获取工具列表
            tools_resp = await session.list_tools()
            tools = [
                {
                    "name": t.name,
                    "description": t.description,
                    "input_schema": t.inputSchema,
                }
                for t in tools_resp.tools
            ]

            self._sessions[name] = session
            self._tools_cache[name] = tools

            logger.info(
                f"Connected to MCP server {name}, available tools: {[t['name'] for t in tools]}"
            )

        except Exception as e:
            logger.error(f"Failed to connect to MCP server {name}: {e}")
            raise

    async def _connect_sse_server(self, name: str, config: Dict):
        """通过 SSE 连接 MCP Server"""
        # TODO: 实现 SSE 传输
        logger.warning(f"SSE transport not yet implemented for {name}")

    def get_session(self, server_name: str) -> Optional[ClientSession]:
        """获取指定服务器的 session"""
        return self._sessions.get(server_name)

    def list_available_servers(self) -> List[str]:
        """列出所有已连接的服务器"""
        return list(self._sessions.keys())

    def list_tools(self, server_name: str = None) -> List[Dict]:
        """
        列出工具

        Args:
            server_name: 服务器名称，None 表示所有服务器
        """
        if server_name:
            return self._tools_cache.get(server_name, [])

        # 返回所有服务器的工具
        all_tools = []
        for name, tools in self._tools_cache.items():
            for tool in tools:
                all_tools.append({**tool, "server": name})
        return all_tools

    async def call_tool(
        self, server_name: str, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        调用 MCP 工具

        Args:
            server_name: MCP 服务器名称
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        session = self._sessions.get(server_name)
        if not session:
            return {
                "success": False,
                "error": f"MCP server '{server_name}' not connected",
            }

        try:
            logger.info(
                f"Calling MCP tool {server_name}/{tool_name} with args: {arguments}"
            )

            result = await session.call_tool(tool_name, arguments)

            # 解析结果内容
            content = result.content
            if content and len(content) > 0:
                # MCP 返回的内容可能是 TextContent 或其他类型
                text_content = []
                for item in content:
                    if hasattr(item, "text"):
                        text_content.append(item.text)
                    elif hasattr(item, "data"):
                        text_content.append(str(item.data))

                return {
                    "success": True,
                    "data": "\n".join(text_content),
                    "raw": content,
                }

            return {"success": True, "data": None, "raw": content}

        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {e}")
            return {"success": False, "error": str(e)}

    async def close(self):
        """关闭所有 MCP 连接"""
        logger.info("Closing MCP Client Manager...")
        await self.exit_stack.aclose()
        self._sessions.clear()
        self._tools_cache.clear()
        self._initialized = False


# 全局实例
_mcp_client_manager: Optional[MCPClientManager] = None


def get_mcp_client_manager() -> MCPClientManager:
    """获取 MCP Client 管理器"""
    global _mcp_client_manager
    if _mcp_client_manager is None:
        _mcp_client_manager = MCPClientManager()
    return _mcp_client_manager


async def initialize_mcp_client():
    """初始化 MCP Client"""
    manager = get_mcp_client_manager()
    await manager.initialize()
    return manager
