"""
工具注册表
管理所有 MCP 工具的注册和查询
"""
from typing import Dict, Any, List, Optional, TYPE_CHECKING

from .protocol.types import Tool
from src.core.logging import get_logger

if TYPE_CHECKING:
    from .tools.base import BaseTool

logger = get_logger("mcp.registry")


class ToolRegistry:
    """
    工具注册表
    
    职责：
    - 存储工具定义和实现
    - 提供工具查询
    - 输出 LLM 所需的工具格式
    """
    
    def __init__(self):
        """初始化注册表"""
        self._definitions: Dict[str, Tool] = {}
        self._implementations: Dict[str, "BaseTool"] = {}
        logger.debug("ToolRegistry initialized")
    
    def register(
        self,
        name: str,
        implementation: "BaseTool",
        definition: Tool = None
    ) -> None:
        """
        注册工具
        
        Args:
            name: 工具名称
            implementation: 工具实现实例
            definition: 工具定义（可选，可从实现中提取）
        """
        self._implementations[name] = implementation
        
        # 如果没有提供定义，尝试从实现中获取
        if definition:
            self._definitions[name] = definition
        elif hasattr(implementation, "get_definition"):
            self._definitions[name] = implementation.get_definition()
        else:
            # 创建基础定义
            self._definitions[name] = Tool(
                name=name,
                description=getattr(implementation, "description", ""),
                parameters=[]
            )
        
        logger.info(f"Tool registered: {name}")
    
    def unregister(self, name: str) -> bool:
        """
        注销工具
        
        Args:
            name: 工具名称
            
        Returns:
            是否成功注销
        """
        if name in self._implementations:
            del self._implementations[name]
            if name in self._definitions:
                del self._definitions[name]
            logger.info(f"Tool unregistered: {name}")
            return True
        return False
    
    def get_tool_implementation(self, name: str) -> Optional["BaseTool"]:
        """
        获取工具实现
        
        Args:
            name: 工具名称
            
        Returns:
            工具实现实例
        """
        return self._implementations.get(name)
    
    def get_tool_definition(self, name: str) -> Optional[Tool]:
        """
        获取工具定义
        
        Args:
            name: 工具名称
            
        Returns:
            工具定义
        """
        return self._definitions.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """
        列出所有工具
        
        Returns:
            工具信息列表
        """
        tools = []
        for name, definition in self._definitions.items():
            tools.append({
                "name": name,
                "description": definition.description,
                "category": definition.category,
                "parameters": [p.dict() for p in definition.parameters]
            })
        return tools
    
    def list_tool_names(self) -> List[str]:
        """
        列出所有工具名称
        
        Returns:
            工具名称列表
        """
        return list(self._implementations.keys())
    
    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """
        获取适合 LLM 的工具定义（OpenAI 格式）
        
        Returns:
            OpenAI 格式的工具定义列表
        """
        return [
            definition.to_openai_format()
            for definition in self._definitions.values()
        ]
    
    def get_tools_by_category(self, category: str) -> List[Tool]:
        """
        按分类获取工具
        
        Args:
            category: 工具分类
            
        Returns:
            工具定义列表
        """
        return [
            tool for tool in self._definitions.values()
            if tool.category == category
        ]
    
    def has_tool(self, name: str) -> bool:
        """检查工具是否已注册"""
        return name in self._implementations
    
    def __contains__(self, name: str) -> bool:
        return self.has_tool(name)
    
    def __len__(self) -> int:
        return len(self._implementations)
