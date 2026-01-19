"""
技能基类
所有技能必须继承此类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TYPE_CHECKING

from src.core.logging import get_logger

if TYPE_CHECKING:
    from src.mcp.client import MCPClient

logger = get_logger("skills.base")


class BaseSkill(ABC):
    """
    技能基类
    
    技能是对一组相关工具的高级封装，提供更抽象的能力
    
    职责：
    - 封装复杂的多工具调用逻辑
    - 提供领域特定的能力
    - 处理工具调用的编排
    """
    
    # 子类必须覆盖这些属性
    name: str = "base_skill"
    description: str = "技能描述"
    required_tools: List[str] = []  # 这个技能依赖的工具列表
    
    def __init__(self):
        """初始化技能"""
        logger.debug(f"Skill initialized: {self.name}")
    
    @abstractmethod
    async def execute(
        self,
        description: str,
        tool_name: Optional[str] = None,
        tool_params: Dict[str, Any] = None,
        context: Dict[str, Any] = None,
        mcp_client: "MCPClient" = None,
        **kwargs
    ) -> Any:
        """
        执行技能
        
        Args:
            description: 步骤描述
            tool_name: 需要调用的工具名称（可选）
            tool_params: 工具参数
            context: 执行上下文
            mcp_client: MCP 客户端（用于调用工具）
            **kwargs: 其他参数
            
        Returns:
            执行结果
        """
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        获取技能元数据
        
        Returns:
            元数据字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "required_tools": self.required_tools
        }
    
    async def call_tool(
        self,
        mcp_client: "MCPClient",
        tool_name: str,
        **kwargs
    ) -> Any:
        """
        调用工具的便捷方法
        
        Args:
            mcp_client: MCP 客户端
            tool_name: 工具名称
            **kwargs: 工具参数
            
        Returns:
            工具执行结果
        """
        if mcp_client is None:
            raise ValueError("需要提供 MCP Client 才能调用工具")
        return await mcp_client.call_tool(tool_name, kwargs)
    
    def __repr__(self) -> str:
        return f"<Skill: {self.name}>"
