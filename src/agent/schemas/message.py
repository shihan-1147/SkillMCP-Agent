"""
消息数据结构定义
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """消息角色"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ToolCall(BaseModel):
    """工具调用信息"""

    tool_name: str = Field(..., description="工具名称")
    tool_params: Dict[str, Any] = Field(default_factory=dict, description="调用参数")
    call_id: Optional[str] = Field(None, description="调用ID")


class ToolResult(BaseModel):
    """工具执行结果"""

    call_id: str = Field(..., description="对应的调用ID")
    tool_name: str = Field(..., description="工具名称")
    success: bool = Field(..., description="是否成功")
    result: Any = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息")


class Message(BaseModel):
    """
    对话消息
    """

    role: MessageRole = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    tool_calls: List[ToolCall] = Field(default_factory=list, description="工具调用列表")
    tool_result: Optional[ToolResult] = Field(None, description="工具执行结果")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

    def to_llm_format(self) -> Dict[str, Any]:
        """转换为 LLM API 格式"""
        msg = {"role": self.role.value, "content": self.content}
        if self.tool_calls:
            msg["tool_calls"] = [
                {
                    "id": tc.call_id,
                    "type": "function",
                    "function": {
                        "name": tc.tool_name,
                        "arguments": str(tc.tool_params),
                    },
                }
                for tc in self.tool_calls
            ]
        if self.tool_result:
            msg["tool_call_id"] = self.tool_result.call_id
            msg["name"] = self.tool_result.tool_name
        return msg

    class Config:
        use_enum_values = True
