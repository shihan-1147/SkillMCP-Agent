"""
MCP Server
管理和暴露所有 MCP 工具
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional

from src.core.exceptions import MCPException
from src.core.logging import get_logger

from .protocol.types import Tool, ToolResult
from .registry import ToolRegistry
from .tools.base import BaseTool

logger = get_logger("mcp.server")


class MCPServer:
    """
    MCP Server

    职责：
    - 管理工具的注册和暴露
    - 提供工具调用的标准接口
    - 支持工具的发现和描述

    这是 MCP 工具层的核心，与 Agent 完全解耦
    """

    def __init__(self, name: str = "SkillMCP-Server"):
        """
        初始化 MCP Server

        Args:
            name: Server 名称
        """
        self.name = name
        self.version = "1.0.0"
        self.registry = ToolRegistry()
        self._initialized = False
        logger.info(f"MCP Server '{name}' created")

    def register_tool(self, tool: BaseTool) -> None:
        """
        注册工具

        Args:
            tool: 工具实例
        """
        self.registry.register(
            name=tool.name, implementation=tool, definition=tool.get_definition()
        )
        logger.info(f"Tool registered: {tool.name}")

    def register_tools(self, tools: List[BaseTool]) -> None:
        """批量注册工具"""
        for tool in tools:
            self.register_tool(tool)

    def unregister_tool(self, name: str) -> bool:
        """注销工具"""
        return self.registry.unregister(name)

    async def call_tool(
        self, name: str, arguments: Dict[str, Any] = None
    ) -> ToolResult:
        """
        调用工具

        Args:
            name: 工具名称
            arguments: 调用参数

        Returns:
            工具执行结果
        """
        import time
        import uuid

        call_id = f"call_{uuid.uuid4().hex[:8]}"
        start_time = time.time()

        logger.debug(f"Tool call [{call_id}]: {name}")

        try:
            tool = self.registry.get_tool_implementation(name)
            if not tool:
                raise MCPException(
                    message=f"Tool not found: {name}",
                    details={"available": self.registry.list_tool_names()},
                )

            # 执行工具
            result = await tool.execute(**(arguments or {}))

            execution_time = (time.time() - start_time) * 1000

            return ToolResult(
                call_id=call_id,
                tool_name=name,
                success=True,
                result=result,
                execution_time_ms=execution_time,
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Tool call failed [{call_id}]: {str(e)}")

            return ToolResult(
                call_id=call_id,
                tool_name=name,
                success=False,
                error=str(e),
                execution_time_ms=execution_time,
            )

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        列出所有工具

        Returns:
            工具信息列表（MCP 协议格式）
        """
        tools = []
        for name in self.registry.list_tool_names():
            definition = self.registry.get_tool_definition(name)
            if definition:
                tools.append(
                    {
                        "name": definition.name,
                        "description": definition.description,
                        "inputSchema": definition.to_json_schema()["parameters"],
                    }
                )
        return tools

    def get_tool_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """获取工具的 JSON Schema"""
        definition = self.registry.get_tool_definition(name)
        if definition:
            return definition.to_json_schema()
        return None

    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """获取适合 LLM 的工具定义"""
        return self.registry.get_tools_for_llm()

    def get_server_info(self) -> Dict[str, Any]:
        """获取 Server 信息"""
        return {
            "name": self.name,
            "version": self.version,
            "tools_count": len(self.registry),
            "tools": self.registry.list_tool_names(),
        }

    async def initialize(self) -> None:
        """初始化 Server"""
        if self._initialized:
            return

        logger.info(f"Initializing MCP Server: {self.name}")
        self._initialized = True

    async def shutdown(self) -> None:
        """关闭 Server"""
        logger.info(f"Shutting down MCP Server: {self.name}")
        self._initialized = False
