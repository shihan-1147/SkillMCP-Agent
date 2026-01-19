"""
Routes 模块

汇总所有 API 路由
"""

from fastapi import APIRouter

from .chat import router as chat_router
from .health import router as health_router

# 创建主路由
api_router = APIRouter()

# 注册子路由
api_router.include_router(health_router, prefix="/health", tags=["健康检查"])

api_router.include_router(chat_router, prefix="/chat", tags=["对话"])

__all__ = ["api_router"]
