"""
MCP Tools 模块

提供标准化的 MCP 工具集合
"""

from .base import BaseTool
from .train_query import TrainQueryTool
from .weather_query import WeatherQueryTool
from .system_time import SystemTimeTool
from .rag_retriever import RAGRetrieverTool
from .loader import ToolLoader, get_tool_loader, load_all_tools, get_tool

# 所有可用工具类
AVAILABLE_TOOLS = [
    TrainQueryTool,
    WeatherQueryTool,
    SystemTimeTool,
    RAGRetrieverTool,
]

# 工具名称到类的映射
TOOL_REGISTRY = {
    "12306_query": TrainQueryTool,
    "weather_query": WeatherQueryTool,
    "system_time": SystemTimeTool,
    "rag_retriever": RAGRetrieverTool,
}

__all__ = [
    "BaseTool",
    "TrainQueryTool",
    "WeatherQueryTool",
    "SystemTimeTool",
    "RAGRetrieverTool",
    "ToolLoader",
    "get_tool_loader",
    "load_all_tools",
    "get_tool",
    "AVAILABLE_TOOLS",
    "TOOL_REGISTRY",
]
