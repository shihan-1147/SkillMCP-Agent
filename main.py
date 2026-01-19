"""
SkillMCP-Agent 主入口

启动 FastAPI 服务
"""
import asyncio
import sys
from pathlib import Path

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import uvicorn

from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger("main")


def main():
    """
    主函数
    
    启动 FastAPI 服务器
    """
    settings = get_settings()
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🤖 SkillMCP-Agent                                       ║
    ║                                                           ║
    ║   A Production-Grade AI Agent with MCP & RAG              ║
    ║                                                           ║
    ╠═══════════════════════════════════════════════════════════╣
    ║                                                           ║
    ║   📡 API Server: http://{host}:{port}             ║
    ║   📚 API Docs:   http://{host}:{port}/docs        ║
    ║   📖 ReDoc:      http://{host}:{port}/redoc       ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """.format(
        host=settings.api_host,
        port=settings.api_port
    ))
    
    logger.info(f"Starting server on {settings.api_host}:{settings.api_port}")
    
    uvicorn.run(
        "src.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning",
        access_log=settings.debug,
    )


if __name__ == "__main__":
    main()
