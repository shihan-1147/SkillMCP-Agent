"""
MCP 协议 JSON Schema 定义
定义工具的输入输出规范
"""
from typing import Dict, Any, List, Optional
from enum import Enum


class JSONSchemaType(str, Enum):
    """JSON Schema 类型"""
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    NULL = "null"


def create_schema(
    type_: str,
    description: str = "",
    properties: Dict[str, Any] = None,
    required: List[str] = None,
    items: Dict[str, Any] = None,
    enum: List[Any] = None,
    default: Any = None,
    **kwargs
) -> Dict[str, Any]:
    """
    创建 JSON Schema 对象
    
    Args:
        type_: 数据类型
        description: 描述
        properties: 对象属性（type=object 时）
        required: 必填字段列表
        items: 数组元素定义（type=array 时）
        enum: 枚举值列表
        default: 默认值
        **kwargs: 其他 Schema 属性
        
    Returns:
        JSON Schema 字典
    """
    schema = {"type": type_}
    
    if description:
        schema["description"] = description
    if properties:
        schema["properties"] = properties
    if required:
        schema["required"] = required
    if items:
        schema["items"] = items
    if enum:
        schema["enum"] = enum
    if default is not None:
        schema["default"] = default
    
    schema.update(kwargs)
    return schema


def create_tool_schema(
    name: str,
    description: str,
    parameters: Dict[str, Any],
    returns: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    创建 MCP 工具 Schema
    
    Args:
        name: 工具名称
        description: 工具描述
        parameters: 输入参数 Schema
        returns: 返回值 Schema
        
    Returns:
        完整的工具 Schema
    """
    schema = {
        "name": name,
        "description": description,
        "inputSchema": {
            "type": "object",
            **parameters
        }
    }
    
    if returns:
        schema["outputSchema"] = returns
    
    return schema


# 预定义的常用 Schema
STRING_SCHEMA = {"type": "string"}
INTEGER_SCHEMA = {"type": "integer"}
NUMBER_SCHEMA = {"type": "number"}
BOOLEAN_SCHEMA = {"type": "boolean"}

DATE_SCHEMA = {
    "type": "string",
    "pattern": r"^\d{4}-\d{2}-\d{2}$",
    "description": "日期格式: YYYY-MM-DD"
}

DATETIME_SCHEMA = {
    "type": "string",
    "pattern": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
    "description": "ISO 8601 日期时间格式"
}

CITY_SCHEMA = {
    "type": "string",
    "description": "城市名称（中文）",
    "minLength": 2,
    "maxLength": 20
}

STATION_SCHEMA = {
    "type": "string",
    "description": "火车站名称",
    "minLength": 2,
    "maxLength": 20
}
