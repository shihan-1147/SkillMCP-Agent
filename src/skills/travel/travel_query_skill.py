"""
火车票务查询技能
查询火车、高铁、动车的票务信息
"""
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from datetime import datetime, timedelta
import re

from ..base import BaseSkill
from src.core.logging import get_logger

if TYPE_CHECKING:
    from src.mcp.client import MCPClient

logger = get_logger("skills.travel")


class TravelQuerySkill(BaseSkill):
    """
    火车票务查询技能
    
    能力：
    - 查询两站之间的车次
    - 查询余票信息
    - 获取站点代码
    - 处理日期解析
    
    依赖的 MCP 工具：
    - 12306_get_tickets: 查询余票
    - 12306_get_station_code: 获取站点代码
    - 12306_get_current_date: 获取当前日期
    """
    
    name = "travel_query"
    description = "查询火车、高铁、动车票务信息，包括车次、余票、时刻表等。适用于出行规划场景。"
    required_tools = [
        "mcp_12306-mcp_get-tickets",
        "mcp_12306-mcp_get-station-code-by-names",
        "mcp_12306-mcp_get-current-date"
    ]
    
    # 日期关键词映射
    DATE_KEYWORDS = {
        "今天": 0,
        "明天": 1,
        "后天": 2,
        "大后天": 3,
    }
    
    # 车型映射
    TRAIN_TYPES = {
        "高铁": "G",
        "动车": "D",
        "快速": "K",
        "特快": "T",
        "直达": "Z",
    }
    
    def __init__(self):
        """初始化技能"""
        super().__init__()
        self._current_date: Optional[str] = None
    
    async def execute(
        self,
        description: str,
        tool_name: Optional[str] = None,
        tool_params: Dict[str, Any] = None,
        context: Dict[str, Any] = None,
        mcp_client: "MCPClient" = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        执行火车票查询
        
        Args:
            description: 查询描述
            tool_params: 预解析的参数 (origin, destination, date)
            context: 上下文信息
            mcp_client: MCP 客户端
            
        Returns:
            查询结果
        """
        logger.info(f"Executing travel query: {description}")
        
        if mcp_client is None:
            return {"success": False, "error": "MCP 客户端未提供"}
        
        try:
            # 步骤1: 获取当前日期
            current_date = await self._get_current_date(mcp_client)
            
            # 步骤2: 解析查询参数
            params = self._parse_query_params(description, tool_params, context)
            
            # 步骤3: 获取站点代码
            origin_code = await self._get_station_code(
                mcp_client, params["origin"]
            )
            dest_code = await self._get_station_code(
                mcp_client, params["destination"]
            )
            
            if not origin_code or not dest_code:
                return {
                    "success": False,
                    "error": f"无法识别站点: {params['origin']} 或 {params['destination']}"
                }
            
            # 步骤4: 查询车次
            travel_date = params.get("date") or current_date
            tickets = await self._query_tickets(
                mcp_client,
                origin_code,
                dest_code,
                travel_date
            )
            
            # 步骤5: 格式化结果
            result = self._format_result(
                origin=params["origin"],
                destination=params["destination"],
                date=travel_date,
                tickets=tickets,
                train_type=params.get("train_type")
            )
            
            logger.info(f"Travel query completed: found {len(result.get('trains', []))} trains")
            return result
            
        except Exception as e:
            logger.error(f"Travel query failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _get_current_date(self, mcp_client: "MCPClient") -> str:
        """获取当前日期"""
        if self._current_date:
            return self._current_date
        
        try:
            result = await mcp_client.call_tool(
                "mcp_12306-mcp_get-current-date",
                {}
            )
            self._current_date = result
            return result
        except Exception:
            # 后备：使用本地日期
            return datetime.now().strftime("%Y-%m-%d")
    
    async def _get_station_code(
        self,
        mcp_client: "MCPClient",
        station_name: str
    ) -> Optional[str]:
        """获取站点代码"""
        try:
            result = await mcp_client.call_tool(
                "mcp_12306-mcp_get-station-code-by-names",
                {"names": station_name}
            )
            # 解析结果获取代码
            if isinstance(result, dict):
                return result.get(station_name) or result.get("code")
            return result
        except Exception as e:
            logger.warning(f"Failed to get station code for {station_name}: {e}")
            return None
    
    async def _query_tickets(
        self,
        mcp_client: "MCPClient",
        origin_code: str,
        dest_code: str,
        date: str
    ) -> Any:
        """查询余票"""
        return await mcp_client.call_tool(
            "mcp_12306-mcp_get-tickets",
            {
                "origin": origin_code,
                "destination": dest_code,
                "date": date
            }
        )
    
    def _parse_query_params(
        self,
        description: str,
        tool_params: Dict[str, Any] = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        解析查询参数
        
        从描述文本中提取：出发地、目的地、日期、车型
        """
        params = tool_params.copy() if tool_params else {}
        
        # 如果已有完整参数，直接返回
        if params.get("origin") and params.get("destination"):
            return params
        
        # 尝试从描述中解析
        # 模式: "从X到Y" 或 "X到Y"
        pattern = r"(?:从)?([^\s到]+)到([^\s的]+)"
        match = re.search(pattern, description)
        if match:
            params["origin"] = params.get("origin") or match.group(1)
            params["destination"] = params.get("destination") or match.group(2)
        
        # 解析日期
        if not params.get("date"):
            for keyword, days in self.DATE_KEYWORDS.items():
                if keyword in description:
                    target_date = datetime.now() + timedelta(days=days)
                    params["date"] = target_date.strftime("%Y-%m-%d")
                    break
        
        # 解析车型
        for type_name, type_code in self.TRAIN_TYPES.items():
            if type_name in description:
                params["train_type"] = type_code
                break
        
        return params
    
    def _format_result(
        self,
        origin: str,
        destination: str,
        date: str,
        tickets: Any,
        train_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """格式化查询结果"""
        result = {
            "success": True,
            "data": {
                "origin": origin,
                "destination": destination,
                "date": date,
                "trains": []
            }
        }
        
        # 解析票务数据
        if isinstance(tickets, list):
            for ticket in tickets:
                train_info = self._parse_ticket_info(ticket)
                if train_info:
                    # 车型筛选
                    if train_type and not train_info.get("train_no", "").startswith(train_type):
                        continue
                    result["data"]["trains"].append(train_info)
        elif isinstance(tickets, dict):
            result["data"]["raw"] = tickets
        else:
            result["data"]["raw"] = str(tickets)
        
        result["data"]["total"] = len(result["data"]["trains"])
        return result
    
    def _parse_ticket_info(self, ticket: Any) -> Optional[Dict[str, Any]]:
        """解析单条票务信息"""
        if isinstance(ticket, dict):
            return {
                "train_no": ticket.get("train_no") or ticket.get("trainNo"),
                "departure_time": ticket.get("departure_time") or ticket.get("startTime"),
                "arrival_time": ticket.get("arrival_time") or ticket.get("arriveTime"),
                "duration": ticket.get("duration") or ticket.get("costTime"),
                "seats": ticket.get("seats") or ticket.get("tickets", {})
            }
        return None
