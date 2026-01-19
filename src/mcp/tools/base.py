"""
MCP 工具基类
所有工具必须继承此类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List

from ..protocol.types import Tool, ToolParameter, ParameterType
from src.core.logging import get_logger

logger = get_logger("mcp.tools.base")


class BaseTool(ABC):
    """
    MCP 工具基类
    
    所有工具实现都必须继承此类并实现 execute 方法
    """
    
    # 子类必须覆盖这些属性
    name: str = "base_tool"
    description: str = "工具描述"
    category: str = "general"
    version: str = "1.0.0"
    
    def __init__(self):
        """初始化工具"""
        logger.debug(f"Tool initialized: {self.name}")
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """
        执行工具
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            执行结果
        """
        pass
    
    def get_parameters(self) -> List[ToolParameter]:
        """
        获取工具参数定义
        
        子类应覆盖此方法定义参数
        
        Returns:
            参数定义列表
        """
        return []
    
    def get_definition(self) -> Tool:
        """
        获取工具定义
        
        Returns:
            Tool 对象
        """
        return Tool(
            name=self.name,
            description=self.description,
            parameters=self.get_parameters(),
            category=self.category,
            version=self.version
        )
    
    def validate_params(self, **kwargs) -> Dict[str, Any]:
        """
        验证并规范化参数
        
        Args:
            **kwargs: 输入参数
            
        Returns:
            处理后的参数字典
        """
        params = self.get_parameters()
        validated = {}
        
        for param in params:
            if param.name in kwargs:
                validated[param.name] = kwargs[param.name]
            elif param.default is not None:
                validated[param.name] = param.default
            elif param.required:
                raise ValueError(f"缺少必填参数: {param.name}")
        
        return validated
    
    def __repr__(self) -> str:
        return f"<Tool: {self.name}>"
