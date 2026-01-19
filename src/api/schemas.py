"""
API 请求响应模型

定义所有 API 端点的数据结构
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

# ============================================================
# 基础模型
# ============================================================


class ResponseStatus(str, Enum):
    """响应状态"""

    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"


class BaseResponse(BaseModel):
    """基础响应模型"""

    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str = "OK"
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# ============================================================
# Chat 相关模型
# ============================================================


class ChatMessage(BaseModel):
    """聊天消息"""

    role: str = Field(..., description="消息角色: user/assistant/system")
    content: str = Field(..., description="消息内容")
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {"role": "user", "content": "北京明天天气怎么样？"}
        }


class ChatRequest(BaseModel):
    """
    聊天请求

    前端只需要发送 message 和 session_id，
    无需感知 MCP / RAG / Agent 内部细节
    """

    message: str = Field(..., description="用户消息", min_length=1, max_length=4000)
    session_id: Optional[str] = Field(
        default=None, description="会话 ID，用于多轮对话。不传则创建新会话"
    )
    stream: bool = Field(default=False, description="是否使用流式响应")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "帮我查一下北京到上海的高铁票",
                "session_id": "sess_abc123",
                "stream": False,
            }
        }


class ToolCallInfo(BaseModel):
    """工具调用信息（供调试使用）"""

    tool_name: str = Field(..., description="工具名称")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="调用参数")
    result_summary: Optional[str] = Field(None, description="结果摘要")
    success: bool = Field(True, description="是否成功")


class StructuredData(BaseModel):
    """结构化数据"""

    type: str = Field(..., description="数据类型: weather/train/knowledge/etc")
    data: Dict[str, Any] = Field(default_factory=dict, description="结构化数据内容")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "weather",
                "data": {
                    "city": "北京",
                    "weather": "晴",
                    "temperature": "25℃",
                    "suggestion": "天气晴好，适合户外活动",
                },
            }
        }


class ChatResponse(BaseResponse):
    """
    聊天响应

    包含：
    - reply: 自然语言回复
    - structured_data: 结构化数据（可选）
    - session_id: 会话 ID
    - debug_info: 调试信息（可选）
    """

    reply: str = Field(..., description="自然语言回复")
    session_id: str = Field(..., description="会话 ID")
    structured_data: Optional[List[StructuredData]] = Field(
        default=None, description="结构化数据列表"
    )
    sources: Optional[List[str]] = Field(
        default=None, description="信息来源（RAG 检索结果）"
    )
    debug_info: Optional[Dict[str, Any]] = Field(
        default=None, description="调试信息（仅在 debug 模式下返回）"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "OK",
                "reply": "北京明天天气晴朗，气温25℃左右，非常适合户外活动。",
                "session_id": "sess_abc123",
                "structured_data": [
                    {
                        "type": "weather",
                        "data": {"city": "北京", "weather": "晴", "temperature": "25"},
                    }
                ],
                "sources": ["weather_api"],
                "timestamp": "2026-01-19T10:00:00",
            }
        }


# ============================================================
# Session 相关模型
# ============================================================


class SessionInfo(BaseModel):
    """会话信息"""

    session_id: str = Field(..., description="会话 ID")
    created_at: datetime = Field(..., description="创建时间")
    last_active: datetime = Field(..., description="最后活跃时间")
    message_count: int = Field(0, description="消息数量")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_abc123",
                "created_at": "2026-01-19T09:00:00",
                "last_active": "2026-01-19T10:30:00",
                "message_count": 5,
            }
        }


class SessionListResponse(BaseResponse):
    """会话列表响应"""

    sessions: List[SessionInfo] = Field(default_factory=list)
    total: int = Field(0, description="总数")


class SessionHistoryResponse(BaseResponse):
    """会话历史响应"""

    session_id: str = Field(..., description="会话 ID")
    messages: List[ChatMessage] = Field(default_factory=list)
    total: int = Field(0, description="消息总数")


# ============================================================
# 系统相关模型
# ============================================================


class HealthResponse(BaseModel):
    """健康检查响应"""

    status: str = "healthy"
    version: str = "0.1.0"
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    components: Dict[str, Any] = Field(default_factory=dict)


class SystemInfoResponse(BaseResponse):
    """系统信息响应"""

    app_name: str
    version: str
    available_skills: List[str] = Field(default_factory=list)
    available_tools: List[str] = Field(default_factory=list)
    rag_status: Dict[str, Any] = Field(default_factory=dict)


# ============================================================
# 错误模型
# ============================================================


class ErrorDetail(BaseModel):
    """错误详情"""

    code: str = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    field: Optional[str] = Field(None, description="相关字段")


class ErrorResponse(BaseResponse):
    """错误响应"""

    status: ResponseStatus = ResponseStatus.ERROR
    error_code: str = Field(..., description="错误代码")
    details: Optional[List[ErrorDetail]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "message": "请求参数错误",
                "error_code": "VALIDATION_ERROR",
                "details": [
                    {
                        "code": "required",
                        "message": "message 字段不能为空",
                        "field": "message",
                    }
                ],
            }
        }
