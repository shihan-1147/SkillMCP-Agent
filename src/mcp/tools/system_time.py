"""
系统时间工具
MCP 标准工具实现
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import time

from .base import BaseTool
from ..protocol.types import Tool, ToolParameter, ParameterType
from src.core.logging import get_logger

logger = get_logger("mcp.tools.system_time")


class SystemTimeTool(BaseTool):
    """
    系统时间工具
    
    提供时间相关的查询和计算功能
    
    MCP Tool Schema:
    {
        "name": "system_time",
        "description": "获取系统时间和日期相关信息",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["get_current", "parse_relative", "format", "calculate"]},
                "timezone": {"type": "string", "default": "Asia/Shanghai"},
                "relative_expr": {"type": "string"},
                "timestamp": {"type": "integer"},
                "format": {"type": "string"},
                "date1": {"type": "string"},
                "date2": {"type": "string"}
            },
            "required": ["action"]
        }
    }
    """
    
    name = "system_time"
    description = "获取系统时间，支持当前时间查询、相对日期解析、时间格式化和日期计算"
    category = "system"
    version = "1.0.0"
    
    # 相对日期关键词
    RELATIVE_KEYWORDS = {
        "今天": 0,
        "明天": 1,
        "后天": 2,
        "大后天": 3,
        "昨天": -1,
        "前天": -2,
    }
    
    # 星期关键词
    WEEKDAY_KEYWORDS = {
        "周一": 0, "星期一": 0, "礼拜一": 0,
        "周二": 1, "星期二": 1, "礼拜二": 1,
        "周三": 2, "星期三": 2, "礼拜三": 2,
        "周四": 3, "星期四": 3, "礼拜四": 3,
        "周五": 4, "星期五": 4, "礼拜五": 4,
        "周六": 5, "星期六": 5, "礼拜六": 5,
        "周日": 6, "星期日": 6, "礼拜日": 6, "周天": 6, "星期天": 6,
    }
    
    def get_parameters(self) -> List[ToolParameter]:
        """定义工具参数"""
        return [
            ToolParameter(
                name="action",
                type=ParameterType.STRING,
                description="操作类型: get_current(获取当前时间), parse_relative(解析相对日期), format(格式化时间戳), calculate(日期计算)",
                required=True,
                enum=["get_current", "parse_relative", "format", "calculate"]
            ),
            ToolParameter(
                name="timezone",
                type=ParameterType.STRING,
                description="时区，默认 Asia/Shanghai",
                required=False,
                default="Asia/Shanghai"
            ),
            ToolParameter(
                name="relative_expr",
                type=ParameterType.STRING,
                description="相对日期表达式，如'明天'、'下周三'、'3天后'",
                required=False
            ),
            ToolParameter(
                name="timestamp",
                type=ParameterType.INTEGER,
                description="Unix 时间戳（秒）",
                required=False
            ),
            ToolParameter(
                name="format",
                type=ParameterType.STRING,
                description="日期格式字符串，如 '%Y-%m-%d %H:%M:%S'",
                required=False,
                default="%Y-%m-%d %H:%M:%S"
            ),
            ToolParameter(
                name="date1",
                type=ParameterType.STRING,
                description="第一个日期（用于计算）",
                required=False
            ),
            ToolParameter(
                name="date2",
                type=ParameterType.STRING,
                description="第二个日期（用于计算）",
                required=False
            ),
        ]
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行时间操作
        
        Args:
            action: 操作类型
            timezone: 时区
            relative_expr: 相对日期表达式
            timestamp: 时间戳
            format: 日期格式
            date1, date2: 用于计算的日期
            
        Returns:
            时间数据
        """
        action = kwargs.get("action", "get_current")
        
        logger.info(f"System time action: {action}")
        
        if action == "get_current":
            return self._get_current_time(kwargs.get("timezone", "Asia/Shanghai"))
        
        elif action == "parse_relative":
            expr = kwargs.get("relative_expr", "")
            return self._parse_relative_date(expr)
        
        elif action == "format":
            timestamp = kwargs.get("timestamp")
            fmt = kwargs.get("format", "%Y-%m-%d %H:%M:%S")
            return self._format_timestamp(timestamp, fmt)
        
        elif action == "calculate":
            date1 = kwargs.get("date1")
            date2 = kwargs.get("date2")
            return self._calculate_date_diff(date1, date2)
        
        else:
            return {"success": False, "error": f"未知操作: {action}"}
    
    def _get_current_time(self, timezone: str = "Asia/Shanghai") -> Dict[str, Any]:
        """获取当前时间"""
        now = datetime.now()
        
        return {
            "success": True,
            "data": {
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S"),
                "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp": int(time.time()),
                "timestamp_ms": int(time.time() * 1000),
                "weekday": now.weekday(),
                "weekday_name": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][now.weekday()],
                "year": now.year,
                "month": now.month,
                "day": now.day,
                "hour": now.hour,
                "minute": now.minute,
                "second": now.second,
                "timezone": timezone,
                "is_weekend": now.weekday() >= 5
            }
        }
    
    def _parse_relative_date(self, expr: str) -> Dict[str, Any]:
        """解析相对日期表达式"""
        if not expr:
            return {"success": False, "error": "请提供相对日期表达式"}
        
        now = datetime.now()
        target_date = None
        
        # 1. 检查直接关键词
        if expr in self.RELATIVE_KEYWORDS:
            days = self.RELATIVE_KEYWORDS[expr]
            target_date = now + timedelta(days=days)
        
        # 2. 检查星期关键词
        elif expr in self.WEEKDAY_KEYWORDS:
            target_weekday = self.WEEKDAY_KEYWORDS[expr]
            current_weekday = now.weekday()
            days_ahead = target_weekday - current_weekday
            if days_ahead <= 0:
                days_ahead += 7
            target_date = now + timedelta(days=days_ahead)
        
        # 3. 检查"下周X"模式
        elif expr.startswith("下周") or expr.startswith("下星期"):
            weekday_part = expr[2:] if expr.startswith("下周") else expr[3:]
            full_weekday = "周" + weekday_part if len(weekday_part) == 1 else weekday_part
            if full_weekday in self.WEEKDAY_KEYWORDS:
                target_weekday = self.WEEKDAY_KEYWORDS[full_weekday]
                current_weekday = now.weekday()
                days_ahead = 7 - current_weekday + target_weekday
                target_date = now + timedelta(days=days_ahead)
        
        # 4. 检查"X天后"模式
        elif "天后" in expr:
            try:
                days = int(expr.replace("天后", "").strip())
                target_date = now + timedelta(days=days)
            except ValueError:
                pass
        
        # 5. 检查"X天前"模式
        elif "天前" in expr:
            try:
                days = int(expr.replace("天前", "").strip())
                target_date = now - timedelta(days=days)
            except ValueError:
                pass
        
        if target_date:
            return {
                "success": True,
                "data": {
                    "expression": expr,
                    "parsed_date": target_date.strftime("%Y-%m-%d"),
                    "weekday": target_date.weekday(),
                    "weekday_name": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][target_date.weekday()],
                    "days_from_today": (target_date.date() - now.date()).days
                }
            }
        else:
            return {
                "success": False,
                "error": f"无法解析日期表达式: {expr}"
            }
    
    def _format_timestamp(self, timestamp: int, fmt: str) -> Dict[str, Any]:
        """格式化时间戳"""
        if timestamp is None:
            timestamp = int(time.time())
        
        try:
            dt = datetime.fromtimestamp(timestamp)
            formatted = dt.strftime(fmt)
            
            return {
                "success": True,
                "data": {
                    "timestamp": timestamp,
                    "format": fmt,
                    "formatted": formatted
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _calculate_date_diff(self, date1: str, date2: str) -> Dict[str, Any]:
        """计算两个日期之间的差值"""
        if not date1:
            date1 = datetime.now().strftime("%Y-%m-%d")
        if not date2:
            date2 = datetime.now().strftime("%Y-%m-%d")
        
        try:
            d1 = datetime.strptime(date1, "%Y-%m-%d")
            d2 = datetime.strptime(date2, "%Y-%m-%d")
            
            diff = d2 - d1
            
            return {
                "success": True,
                "data": {
                    "date1": date1,
                    "date2": date2,
                    "days": diff.days,
                    "weeks": diff.days // 7,
                    "months_approx": diff.days // 30,
                    "years_approx": diff.days // 365
                }
            }
        except ValueError as e:
            return {"success": False, "error": f"日期格式错误: {e}"}
