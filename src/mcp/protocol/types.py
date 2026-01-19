"""
MCP 协议类型定义
定义工具调用的标准数据结构
"""

from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from pydantic import BaseModel, Field


class ParameterType(str, Enum):
    """参数类型枚举"""

    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


class ToolParameter(BaseModel):
    """工具参数定义"""

    name: str = Field(..., description="参数名称")
    type: ParameterType = Field(..., description="参数类型")
    description: str = Field(default="", description="参数描述")
    required: bool = Field(default=False, description="是否必填")
    default: Any = Field(default=None, description="默认值")
    enum: Optional[List[Any]] = Field(default=None, description="枚举值列表")


class Tool(BaseModel):
    """
    MCP 工具定义

    遵循 MCP 协议的工具描述格式
    """

    name: str = Field(..., description="工具唯一标识符")
    description: str = Field(..., description="工具功能描述")
    parameters: List[ToolParameter] = Field(
        default_factory=list, description="工具参数列表"
    )
    category: str = Field(default="general", description="工具分类")
    version: str = Field(default="1.0.0", description="工具版本")

    def to_openai_format(self) -> Dict[str, Any]:
        """
        转换为 OpenAI function calling 格式

        Returns:
            OpenAI 工具格式字典
        """
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = {
                "type": param.type.value,
                "description": param.description,
            }
            if param.enum:
                properties[param.name]["enum"] = param.enum
            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    def to_json_schema(self) -> Dict[str, Any]:
        """
        转换为 JSON Schema 格式

        Returns:
            JSON Schema 字典
        """
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = {
                "type": param.type.value,
                "description": param.description,
            }
            if param.default is not None:
                properties[param.name]["default"] = param.default
            if param.enum:
                properties[param.name]["enum"] = param.enum
            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }


class ToolCall(BaseModel):
    """
    工具调用请求
    """

    call_id: str = Field(..., description="调用唯一ID")
    tool_name: str = Field(..., description="工具名称")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="调用参数")

    class Config:
        extra = "allow"


class ToolResult(BaseModel):
    """
    工具调用结果
    """

    call_id: str = Field(..., description="对应的调用ID")
    tool_name: str = Field(..., description="工具名称")
    success: bool = Field(..., description="是否执行成功")
    result: Any = Field(default=None, description="执行结果")
    error: Optional[str] = Field(default=None, description="错误信息")
    execution_time_ms: Optional[float] = Field(
        default=None, description="执行耗时（毫秒）"
    )

    def to_message_format(self) -> Dict[str, Any]:
        """转换为可用于对话的消息格式"""
        return {
            "role": "tool",
            "tool_call_id": self.call_id,
            "name": self.tool_name,
            "content": str(self.result) if self.success else f"Error: {self.error}",
        }
