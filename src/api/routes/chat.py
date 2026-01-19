"""
聊天路由

核心 /chat 接口
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
import json

from src.api.schemas import (
    ChatRequest,
    ChatResponse,
    SessionInfo,
    ResponseStatus,
)
from src.api.deps import (
    get_chat_service_dep,
    get_session_manager_dep,
    get_debug_mode,
)
from src.api.chat_service import ChatService
from src.api.session import SessionManager
from src.core.logging import get_logger

logger = get_logger("api.routes.chat")

router = APIRouter()


@router.post(
    "",
    response_model=ChatResponse,
    summary="发送消息",
    description="发送消息并获取智能回复，支持多轮对话"
)
async def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service_dep),
    debug: bool = Depends(get_debug_mode)
) -> ChatResponse:
    """
    聊天接口
    
    ## 功能
    - 支持多轮对话（通过 session_id）
    - 自动路由到合适的处理器（天气、火车票、知识库等）
    - 返回结构化数据 + 自然语言回复
    
    ## 使用示例
    
    ```json
    {
        "message": "北京今天天气怎么样？",
        "session_id": "user-123"
    }
    ```
    
    ## 响应示例
    
    ```json
    {
        "status": "success",
        "reply": "北京当前天气晴 ☀️，温度25℃...",
        "session_id": "user-123",
        "structured_data": [{
            "type": "weather",
            "data": {"city": "北京", "temperature": 25, ...}
        }]
    }
    ```
    """
    logger.info(f"Chat request: message={request.message[:50]}...")
    
    try:
        response = await chat_service.chat(request, debug=debug)
        return response
        
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/stream",
    summary="流式对话",
    description="发送消息并获取流式响应"
)
async def chat_stream(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service_dep),
) -> StreamingResponse:
    """
    流式聊天接口
    
    以 Server-Sent Events (SSE) 格式返回响应
    """
    async def generate():
        try:
            # 获取完整响应
            response = await chat_service.chat(request)
            
            # 模拟流式输出（按字符）
            for i, char in enumerate(response.reply):
                chunk = {
                    "event": "token",
                    "data": char,
                    "index": i
                }
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            
            # 发送完成事件
            final = {
                "event": "done",
                "session_id": response.session_id,
                "structured_data": [
                    sd.model_dump() for sd in (response.structured_data or [])
                ],
                "sources": response.sources
            }
            yield f"data: {json.dumps(final, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            error = {
                "event": "error",
                "message": str(e)
            }
            yield f"data: {json.dumps(error, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get(
    "/session/{session_id}",
    response_model=SessionInfo,
    summary="获取会话信息",
    description="获取指定会话的详细信息"
)
async def get_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager_dep)
) -> SessionInfo:
    """
    获取会话信息
    
    包括会话创建时间、消息数量、最后活跃时间等
    """
    session = await session_manager.get(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found"
        )
    
    return SessionInfo(
        session_id=session.session_id,
        created_at=session.created_at.isoformat(),
        last_active=session.last_active.isoformat(),
        message_count=len(session.messages),
        metadata=session.metadata
    )


@router.delete(
    "/session/{session_id}",
    summary="删除会话",
    description="删除指定会话及其历史记录"
)
async def delete_session(
    session_id: str,
    session_manager: SessionManager = Depends(get_session_manager_dep)
) -> dict:
    """
    删除会话
    """
    deleted = await session_manager.delete(session_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found"
        )
    
    return {"status": "success", "message": f"Session '{session_id}' deleted"}


@router.get(
    "/sessions",
    summary="列出所有会话",
    description="获取所有活跃会话的列表"
)
async def list_sessions(
    session_manager: SessionManager = Depends(get_session_manager_dep)
) -> dict:
    """
    列出所有会话
    """
    stats = session_manager.get_stats()
    sessions = []
    
    for session_id in list(session_manager._sessions.keys()):
        session = session_manager._sessions.get(session_id)
        if session:
            sessions.append({
                "session_id": session.session_id,
                "created_at": session.created_at.isoformat(),
                "last_active": session.last_active.isoformat(),
                "message_count": len(session.messages),
            })
    
    return {
        "total": stats["active_sessions"],
        "max_sessions": stats["max_sessions"],
        "sessions": sessions
    }
