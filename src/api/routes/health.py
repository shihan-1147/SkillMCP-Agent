"""
健康检查路由
"""

from datetime import datetime

from fastapi import APIRouter, Depends

from src.api.schemas import HealthResponse
from src.api.session import get_session_manager
from src.core.config import get_settings

router = APIRouter()


@router.get(
    "",
    response_model=HealthResponse,
    summary="健康检查",
    description="检查服务是否正常运行",
)
async def health_check() -> HealthResponse:
    """
    健康检查接口

    返回服务状态和版本信息
    """
    settings = get_settings()
    session_manager = get_session_manager()

    return HealthResponse(
        status="healthy",
        version=settings.version,
        timestamp=datetime.now().isoformat(),
        components={
            "api": "ok",
            "session_manager": "ok",
            "active_sessions": session_manager.get_stats()["active_sessions"],
        },
    )


@router.get(
    "/ready",
    response_model=HealthResponse,
    summary="就绪检查",
    description="检查服务是否就绪",
)
async def readiness_check() -> HealthResponse:
    """
    就绪检查

    检查所有组件是否就绪
    """
    settings = get_settings()
    components = {}
    overall_status = "healthy"

    # 检查会话管理器
    try:
        session_manager = get_session_manager()
        components["session_manager"] = "ok"
    except Exception as e:
        components["session_manager"] = f"error: {str(e)}"
        overall_status = "degraded"

    # 检查 MCP
    try:
        from src.mcp import get_registry

        registry = get_registry()
        components["mcp_tools"] = len(registry.list_tools())
    except Exception as e:
        components["mcp"] = f"error: {str(e)}"
        overall_status = "degraded"

    # 检查 RAG
    try:
        from src.rag import get_rag_pipeline

        rag = get_rag_pipeline()
        components["rag_documents"] = rag.stats.get("total_chunks", 0)
    except Exception as e:
        components["rag"] = f"error: {str(e)}"
        overall_status = "degraded"

    return HealthResponse(
        status=overall_status,
        version=settings.version,
        timestamp=datetime.now().isoformat(),
        components=components,
    )
