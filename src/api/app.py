"""
FastAPI 应用工厂

创建并配置 FastAPI 应用
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from src.core.config import get_settings
from src.core.logging import get_logger
from src.api.routes import api_router
from src.api.chat_service import get_chat_service

logger = get_logger("api.app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    应用生命周期管理
    
    - startup: 初始化服务
    - shutdown: 清理资源
    """
    # ========== Startup ==========
    logger.info("🚀 Starting SkillMCP-Agent API...")
    
    settings = get_settings()
    
    # 初始化 MCP Client Manager（连接外部 MCP Server）
    try:
        from src.mcp.mcp_client import initialize_mcp_client, get_mcp_client_manager
        mcp_manager = await initialize_mcp_client()
        app.state.mcp_client = mcp_manager
        servers = mcp_manager.list_available_servers()
        logger.info(f"✅ MCP Client initialized, connected servers: {servers}")
    except Exception as e:
        logger.warning(f"⚠️ MCP Client initialization failed: {e}")
        app.state.mcp_client = None
    
    # 初始化聊天服务（会自动初始化 MCP 和 RAG）
    try:
        chat_service = get_chat_service()
        await chat_service.initialize()
        logger.info("✅ ChatService initialized")
    except Exception as e:
        logger.error(f"❌ ChatService initialization failed: {e}")
    
    logger.info(f"🌐 API ready at http://{settings.api_host}:{settings.api_port}")
    logger.info(f"📚 Docs available at http://{settings.api_host}:{settings.api_port}/docs")
    
    yield
    
    # ========== Shutdown ==========
    logger.info("🛑 Shutting down SkillMCP-Agent API...")
    
    # 关闭 MCP Client
    if hasattr(app.state, 'mcp_client') and app.state.mcp_client:
        await app.state.mcp_client.close()
        logger.info("✅ MCP Client closed")
    
    # 清理会话
    from src.api.session import get_session_manager
    session_manager = get_session_manager()
    await session_manager.clear_all()
    
    logger.info("👋 Goodbye!")


def create_app() -> FastAPI:
    """
    创建 FastAPI 应用
    
    Returns:
        配置完成的 FastAPI 应用实例
    """
    settings = get_settings()
    
    # 创建应用
    app = FastAPI(
        title=settings.project_name,
        description="""
# SkillMCP-Agent API

🤖 一个基于 MCP 协议的智能 Agent 系统

## 功能特性

- **智能对话**: 支持多轮对话，自动维护上下文
- **技能路由**: 自动识别用户意图，路由到合适的技能
- **MCP 协议**: 标准化的工具调用接口
- **RAG 增强**: 基于知识库的检索增强生成
- **结构化输出**: 同时返回自然语言和结构化数据

## 支持的技能

| 技能 | 描述 |
|------|------|
| 🌤️ 天气查询 | 查询城市天气信息 |
| 🚄 火车票查询 | 查询火车票信息 |
| 📚 知识问答 | 基于知识库的问答 |

## 快速开始

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/chat",
    json={"message": "北京今天天气怎么样？"}
)
print(response.json())
```
        """,
        version=settings.version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )
    
    # 配置 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    app.include_router(api_router, prefix="/api/v1")
    
    # 根路由
    @app.get("/", tags=["Root"])
    async def root():
        """根路由，返回 API 信息"""
        return {
            "name": settings.project_name,
            "version": settings.version,
            "docs": "/docs",
            "health": "/api/v1/health",
            "chat": "/api/v1/chat",
        }
    
    return app


def custom_openapi(app: FastAPI):
    """自定义 OpenAPI Schema"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # 添加自定义标签
    openapi_schema["tags"] = [
        {
            "name": "对话",
            "description": "聊天相关接口，支持多轮对话"
        },
        {
            "name": "健康检查",
            "description": "服务状态检查接口"
        },
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


# 创建应用实例
app = create_app()

# 获取应用实例的便捷函数
def get_app() -> FastAPI:
    """获取应用实例"""
    return app
