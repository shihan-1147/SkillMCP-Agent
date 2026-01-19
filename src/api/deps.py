"""
API 依赖注入
"""
from typing import Optional
from fastapi import Depends, Header, HTTPException, status

from .session import SessionManager, get_session_manager
from .chat_service import ChatService, get_chat_service
from src.core.config import get_settings, Settings
from src.core.logging import get_logger

logger = get_logger("api.deps")


async def get_settings_dep() -> Settings:
    """获取配置"""
    return get_settings()


async def get_session_manager_dep() -> SessionManager:
    """获取会话管理器"""
    return get_session_manager()


async def get_chat_service_dep() -> ChatService:
    """获取聊天服务"""
    return get_chat_service()


async def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> bool:
    """
    验证 API Key（可选）
    
    如果配置了 API Key，则需要验证
    """
    settings = get_settings()
    
    # 如果没有配置 API Key，跳过验证
    if not hasattr(settings, "api_key") or not settings.api_key:
        return True
    
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key"
        )
    
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    
    return True


async def get_debug_mode(
    debug: bool = False,
    x_debug: Optional[str] = Header(None, alias="X-Debug")
) -> bool:
    """
    获取调试模式
    
    可以通过查询参数或 Header 启用
    """
    if debug:
        return True
    if x_debug and x_debug.lower() in ("true", "1", "yes"):
        return True
    return get_settings().debug
