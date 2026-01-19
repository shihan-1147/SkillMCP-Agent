"""
MCP (Model Context Protocol) 模块

提供标准化的工具调用协议和实现

架构：
- client: Agent 调用工具的唯一入口
- server: MCP 服务端，管理和暴露工具
- registry: 工具注册表
- protocol: 协议类型定义
- tools: 具体工具实现

使用示例:
```python
from src.mcp import initialize_mcp, call_tool

# 初始化
mcp = await initialize_mcp()

# 调用工具
result = await call_tool("weather_query", city="北京")
```
"""

from .client import MCPClient
from .server import MCPServer
from .registry import ToolRegistry
from .protocol.types import Tool, ToolCall, ToolResult, ToolParameter, ParameterType
from .init import MCPSystem, get_mcp_system, initialize_mcp, call_tool

__all__ = [
    # 核心组件
    "MCPClient",
    "MCPServer",
    "ToolRegistry",
    "MCPSystem",
    # 便捷函数
    "get_mcp_system",
    "initialize_mcp",
    "call_tool",
    # 协议类型
    "Tool",
    "ToolCall",
    "ToolResult",
    "ToolParameter",
    "ParameterType",
]
