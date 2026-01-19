"""
pytest 配置文件
"""
import pytest
import asyncio
import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_llm():
    """模拟 LLM"""
    from unittest.mock import AsyncMock
    llm = AsyncMock()
    llm.chat.return_value = "这是模拟的 LLM 响应"
    return llm


@pytest.fixture
def mock_mcp_client():
    """模拟 MCP Client"""
    from unittest.mock import AsyncMock, MagicMock
    client = MagicMock()
    client.call_tool = AsyncMock(return_value="工具执行结果")
    client.list_tools.return_value = []
    return client
