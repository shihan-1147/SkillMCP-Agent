"""
MCP 系统初始化模块

负责初始化整个 MCP 系统：
- 加载工具
- 注册到服务器
- 创建客户端
"""
from typing import Optional

from .client import MCPClient
from .server import MCPServer
from .registry import ToolRegistry
from .tools.loader import get_tool_loader
from src.core.logging import get_logger

logger = get_logger("mcp.init")


class MCPSystem:
    """
    MCP 系统统一入口
    
    整合 MCPClient、MCPServer、ToolRegistry 的完整 MCP 系统
    
    使用示例:
    ```python
    # 初始化
    mcp = MCPSystem()
    await mcp.initialize()
    
    # 通过 client 调用工具
    result = await mcp.client.call_tool("weather_query", {"city": "北京"})
    
    # 获取工具定义供 LLM 使用
    tools = mcp.client.get_tools_for_llm()
    ```
    """
    
    def __init__(self):
        self.server = MCPServer(name="SkillMCP-Server")
        self.registry = self.server.registry  # 使用 server 的 registry
        self.client = MCPClient(registry=self.registry)
        self._initialized = False
    
    async def initialize(self) -> None:
        """
        初始化 MCP 系统
        
        加载所有工具并注册到系统中
        """
        if self._initialized:
            logger.debug("MCP system already initialized")
            return
        
        logger.info("Initializing MCP system...")
        
        # 加载所有工具
        loader = get_tool_loader()
        tools = loader.load_all_tools()
        
        # 注册到服务器
        for name, tool in tools.items():
            self.server.register_tool(tool)
        
        self._initialized = True
        logger.info(f"MCP system initialized with {len(tools)} tools")
    
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._initialized
    
    def get_client(self) -> MCPClient:
        """获取 MCP 客户端"""
        return self.client
    
    def get_server(self) -> MCPServer:
        """获取 MCP 服务器"""
        return self.server
    
    def list_tools(self):
        """列出所有工具"""
        return self.server.list_tools()
    
    def get_tools_for_llm(self):
        """获取 LLM 格式的工具定义"""
        return self.client.get_tools_for_llm()


# 全局 MCP 系统实例
_mcp_system: Optional[MCPSystem] = None


def get_mcp_system() -> MCPSystem:
    """
    获取全局 MCP 系统实例
    
    Returns:
        MCPSystem 实例
    """
    global _mcp_system
    if _mcp_system is None:
        _mcp_system = MCPSystem()
    return _mcp_system


async def initialize_mcp() -> MCPSystem:
    """
    初始化全局 MCP 系统
    
    Returns:
        初始化后的 MCPSystem 实例
    """
    mcp = get_mcp_system()
    await mcp.initialize()
    return mcp


async def call_tool(tool_name: str, **kwargs):
    """
    便捷函数：调用工具
    
    Args:
        tool_name: 工具名称
        **kwargs: 工具参数
        
    Returns:
        工具执行结果
    """
    mcp = get_mcp_system()
    if not mcp.is_initialized():
        await mcp.initialize()
    return await mcp.client.call_tool(tool_name, kwargs)
