"""
MCP 客户端
Agent 调用工具的唯一入口
"""

import time
import uuid
from typing import Any, Dict, List, Optional

from src.core.exceptions import MCPException, ToolCallException
from src.core.logging import get_logger

from .protocol.types import Tool, ToolCall, ToolResult
from .registry import ToolRegistry

logger = get_logger("mcp.client")


class MCPClient:
    """
    MCP 客户端

    职责：
    - 作为 Agent 调用工具的唯一入口
    - 管理工具注册表
    - 封装工具调用过程
    - 统一错误处理

    重要：Agent 不能直接调用工具实现，必须通过 MCPClient
    """

    def __init__(self, registry: ToolRegistry = None):
        """
        初始化 MCP 客户端

        Args:
            registry: 工具注册表实例
        """
        self.registry = registry if registry is not None else ToolRegistry()
        self._call_history: List[ToolResult] = []
        logger.debug("MCPClient initialized")

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Any:
        """
        调用工具

        这是调用工具的主要方法

        Args:
            tool_name: 工具名称
            arguments: 调用参数

        Returns:
            工具执行结果

        Raises:
            ToolCallException: 工具调用失败
        """
        call_id = f"call_{uuid.uuid4().hex[:8]}"
        arguments = arguments or {}

        logger.info(f"Calling tool: {tool_name} (call_id: {call_id})")
        logger.debug(f"Arguments: {arguments}")

        start_time = time.time()

        try:
            # 获取工具
            tool_impl = self.registry.get_tool_implementation(tool_name)
            if not tool_impl:
                raise ToolCallException(
                    message=f"工具 '{tool_name}' 未注册",
                    details={"available_tools": self.registry.list_tool_names()},
                )

            # 验证参数
            self._validate_arguments(tool_name, arguments)

            # 执行工具
            result = await tool_impl.execute(**arguments)

            execution_time = (time.time() - start_time) * 1000

            # 记录结果
            tool_result = ToolResult(
                call_id=call_id,
                tool_name=tool_name,
                success=True,
                result=result,
                execution_time_ms=execution_time,
            )
            self._call_history.append(tool_result)

            logger.info(f"Tool {tool_name} completed in {execution_time:.2f}ms")
            return result

        except ToolCallException:
            raise
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000

            tool_result = ToolResult(
                call_id=call_id,
                tool_name=tool_name,
                success=False,
                error=str(e),
                execution_time_ms=execution_time,
            )
            self._call_history.append(tool_result)

            logger.error(f"Tool {tool_name} failed: {str(e)}")
            raise ToolCallException(
                message=f"工具 '{tool_name}' 执行失败: {str(e)}",
                details={"call_id": call_id, "arguments": arguments},
            )

    async def call_tool_batch(self, calls: List[ToolCall]) -> List[ToolResult]:
        """
        批量调用工具

        Args:
            calls: 工具调用列表

        Returns:
            工具结果列表
        """
        results = []
        for call in calls:
            try:
                result = await self.call_tool(call.tool_name, call.arguments)
                results.append(
                    ToolResult(
                        call_id=call.call_id,
                        tool_name=call.tool_name,
                        success=True,
                        result=result,
                    )
                )
            except Exception as e:
                results.append(
                    ToolResult(
                        call_id=call.call_id,
                        tool_name=call.tool_name,
                        success=False,
                        error=str(e),
                    )
                )
        return results

    def _validate_arguments(self, tool_name: str, arguments: Dict[str, Any]) -> None:
        """
        验证工具参数

        Args:
            tool_name: 工具名称
            arguments: 参数字典

        Raises:
            ToolCallException: 参数验证失败
        """
        tool_def = self.registry.get_tool_definition(tool_name)
        if not tool_def:
            return  # 没有定义则跳过验证

        # 检查必填参数
        for param in tool_def.parameters:
            if param.required and param.name not in arguments:
                raise ToolCallException(
                    message=f"缺少必填参数: {param.name}",
                    details={"tool": tool_name, "parameter": param.name},
                )

    def register_tool(self, name: str, implementation, definition: Tool = None) -> None:
        """
        注册工具

        Args:
            name: 工具名称
            implementation: 工具实现实例
            definition: 工具定义
        """
        self.registry.register(name, implementation, definition)
        logger.info(f"Tool registered via client: {name}")

    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """
        获取适合 LLM 的工具定义

        Returns:
            OpenAI 格式的工具定义列表
        """
        return self.registry.get_tools_for_llm()

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        列出所有工具

        Returns:
            工具信息列表
        """
        return self.registry.list_tools()

    def get_call_history(self, limit: int = 10) -> List[ToolResult]:
        """
        获取调用历史

        Args:
            limit: 返回数量限制

        Returns:
            调用结果列表
        """
        return self._call_history[-limit:]

    def clear_history(self) -> None:
        """清空调用历史"""
        self._call_history.clear()
