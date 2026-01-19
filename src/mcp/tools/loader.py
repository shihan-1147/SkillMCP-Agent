"""
MCP 工具加载器

负责自动发现、加载和初始化 MCP 工具
"""

import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import Dict, List, Optional, Type

from src.core.logging import get_logger

from .base import BaseTool

logger = get_logger("mcp.tools.loader")


class ToolLoader:
    """
    MCP 工具加载器

    功能：
    - 自动发现工具模块
    - 动态加载工具类
    - 实例化并注册工具

    使用示例:
    ```python
    loader = ToolLoader()
    tools = loader.load_all_tools()

    # 或者按需加载
    train_tool = loader.load_tool("12306_query")
    ```
    """

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._tool_classes: Dict[str, Type[BaseTool]] = {}
        self._loaded = False

    def discover_tools(self) -> List[Type[BaseTool]]:
        """
        自动发现所有工具类

        扫描 tools 目录下的所有模块，找出继承自 BaseTool 的类

        Returns:
            工具类列表
        """
        tool_classes = []
        tools_package = "src.mcp.tools"
        tools_path = Path(__file__).parent

        logger.info(f"Discovering tools in: {tools_path}")

        # 遍历 tools 目录
        for module_info in pkgutil.iter_modules([str(tools_path)]):
            if module_info.name.startswith("_") or module_info.name in (
                "base",
                "loader",
            ):
                continue

            try:
                module_name = f"{tools_package}.{module_info.name}"
                module = importlib.import_module(module_name)

                # 查找模块中的工具类
                for name, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, BaseTool)
                        and obj is not BaseTool
                        and hasattr(obj, "name")
                    ):
                        tool_classes.append(obj)
                        logger.debug(f"Discovered tool: {obj.name}")

            except Exception as e:
                logger.error(f"Failed to import module {module_info.name}: {e}")

        logger.info(f"Discovered {len(tool_classes)} tools")
        return tool_classes

    def load_all_tools(self) -> Dict[str, BaseTool]:
        """
        加载所有发现的工具

        Returns:
            工具名称到工具实例的映射
        """
        if self._loaded:
            return self._tools

        tool_classes = self.discover_tools()

        for tool_class in tool_classes:
            try:
                tool = tool_class()
                self._tools[tool.name] = tool
                self._tool_classes[tool.name] = tool_class
                logger.info(f"Loaded tool: {tool.name} (v{tool.version})")
            except Exception as e:
                logger.error(f"Failed to instantiate tool {tool_class}: {e}")

        self._loaded = True
        return self._tools

    def load_tool(self, name: str) -> Optional[BaseTool]:
        """
        按名称加载单个工具

        Args:
            name: 工具名称

        Returns:
            工具实例，未找到返回 None
        """
        # 确保已加载
        if not self._loaded:
            self.load_all_tools()

        return self._tools.get(name)

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        获取已加载的工具

        Args:
            name: 工具名称

        Returns:
            工具实例
        """
        return self._tools.get(name)

    def get_all_tools(self) -> Dict[str, BaseTool]:
        """
        获取所有已加载的工具

        Returns:
            工具字典
        """
        if not self._loaded:
            self.load_all_tools()
        return self._tools

    def list_tools(self) -> List[str]:
        """
        列出所有工具名称

        Returns:
            工具名称列表
        """
        if not self._loaded:
            self.load_all_tools()
        return list(self._tools.keys())

    def reload_tool(self, name: str) -> Optional[BaseTool]:
        """
        重新加载指定工具

        用于开发期间热更新工具

        Args:
            name: 工具名称

        Returns:
            新的工具实例
        """
        if name not in self._tool_classes:
            logger.warning(f"Tool not found for reload: {name}")
            return None

        try:
            tool_class = self._tool_classes[name]
            new_tool = tool_class()
            self._tools[name] = new_tool
            logger.info(f"Reloaded tool: {name}")
            return new_tool
        except Exception as e:
            logger.error(f"Failed to reload tool {name}: {e}")
            return None

    def get_tools_by_category(self, category: str) -> List[BaseTool]:
        """
        按类别获取工具

        Args:
            category: 工具类别

        Returns:
            该类别的工具列表
        """
        if not self._loaded:
            self.load_all_tools()

        return [tool for tool in self._tools.values() if tool.category == category]


# 全局工具加载器实例
_global_loader: Optional[ToolLoader] = None


def get_tool_loader() -> ToolLoader:
    """
    获取全局工具加载器实例

    Returns:
        ToolLoader 实例
    """
    global _global_loader
    if _global_loader is None:
        _global_loader = ToolLoader()
    return _global_loader


def load_all_tools() -> Dict[str, BaseTool]:
    """
    便捷函数：加载所有工具

    Returns:
        工具字典
    """
    return get_tool_loader().load_all_tools()


def get_tool(name: str) -> Optional[BaseTool]:
    """
    便捷函数：获取指定工具

    Args:
        name: 工具名称

    Returns:
        工具实例
    """
    return get_tool_loader().get_tool(name)
