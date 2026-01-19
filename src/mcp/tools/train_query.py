"""
12306 火车票查询工具
MCP 标准工具实现 - 通过 MCP Client 调用真实的 12306 MCP Server
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import re

from .base import BaseTool
from ..protocol.types import Tool, ToolParameter, ParameterType
from src.core.logging import get_logger
from src.core.config import get_settings

logger = get_logger("mcp.tools.train_query")


class TrainQueryTool(BaseTool):
    """
    12306 火车票查询工具
    
    通过 MCP Client 连接 12306-mcp Server 获取真实的火车票信息
    """
    
    name = "12306_query"
    description = "查询 12306 火车票信息（通过 MCP 协议调用 12306-mcp）"
    category = "travel"
    version = "3.0.0"
    
    # 城市到站点代码的映射（用于快速查询，可选）
    CITY_STATION_CODES = {
        "北京": "BJP", "北京南": "VNP", "北京西": "BXP", "北京北": "VAP",
        "上海": "SHH", "上海虹桥": "AOH", "上海南": "SNH",
        "广州": "GZQ", "广州南": "IZQ", "广州东": "GGQ",
        "深圳": "SZQ", "深圳北": "IOQ",
        "杭州": "HZH", "杭州东": "HGH",
        "南京": "NJH", "南京南": "NKH",
        "苏州": "SZH", "苏州北": "OHH",
        "武汉": "WHN", "汉口": "HKN",
        "长沙": "CSQ", "长沙南": "CWQ",
        "郑州": "ZZF", "郑州东": "ZAF",
        "成都": "CDW", "成都东": "ICW",
        "西安": "XAY", "西安北": "EAY",
        "重庆": "CQW", "重庆北": "CUW", "重庆西": "CXW",
        "天津": "TJP", "天津南": "TIP", "天津西": "TXP",
        "石家庄": "SJP", "太原": "TYV", "太原南": "TNV",
        "济南": "JNK", "济南西": "JGK",
        "青岛": "QDK", "青岛北": "QHK",
        "沈阳": "SYT", "沈阳北": "SBT",
        "大连": "DLT", "大连北": "DFT",
        "哈尔滨": "HBB", "哈尔滨西": "VAB",
        "长春": "CCT", "长春西": "CET",
        "合肥": "HFH", "合肥南": "ENH",
        "南昌": "NCG", "南昌西": "NXG",
        "福州": "FZS", "福州南": "FYS",
        "厦门": "XMS", "厦门北": "XKS",
        "昆明": "KMM", "昆明南": "KOM",
        "贵阳": "GIW", "贵阳北": "KQW",
        "南宁": "NNZ", "南宁东": "NFZ",
        "海口": "VUQ", "三亚": "SEQ",
        "兰州": "LZJ", "兰州西": "LNJ",
        "西宁": "XNO", "银川": "YIJ",
        "乌鲁木齐": "WMR", "拉萨": "LSO",
        "呼和浩特": "HHC",
        "保定": "BDP", "保定东": "BMP",
        "唐山": "TSP", "秦皇岛": "QTP",
        "邯郸": "HDP", "廊坊": "LJP", "沧州": "COP",
    }
    
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self._mcp_client = None
    
    def get_parameters(self) -> List[ToolParameter]:
        """定义工具参数"""
        return [
            ToolParameter(
                name="action",
                type=ParameterType.STRING,
                description="操作类型: query_tickets(查询余票), get_station_code(获取站点代码), get_current_date(获取当前日期)",
                required=True
            ),
            ToolParameter(
                name="origin",
                type=ParameterType.STRING,
                description="出发站（query_tickets 时必填）",
                required=False
            ),
            ToolParameter(
                name="destination",
                type=ParameterType.STRING,
                description="到达站（query_tickets 时必填）",
                required=False
            ),
            ToolParameter(
                name="date",
                type=ParameterType.STRING,
                description="出发日期，格式 YYYY-MM-DD",
                required=False
            ),
            ToolParameter(
                name="train_type",
                type=ParameterType.STRING,
                description="车次类型过滤: G(高铁), D(动车), GD(高铁+动车), 空=全部",
                required=False
            ),
        ]
    
    async def _get_mcp_client(self):
        """获取 MCP Client Manager"""
        if self._mcp_client is None:
            from ..mcp_client import get_mcp_client_manager, initialize_mcp_client
            self._mcp_client = get_mcp_client_manager()
            if not self._mcp_client._initialized:
                await initialize_mcp_client()
        return self._mcp_client
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """执行查询"""
        action = kwargs.get("action", "query_tickets")
        
        logger.info(f"12306 query action: {action}")
        
        if action == "get_current_date":
            return self._get_current_date()
        
        elif action == "get_station_code":
            station_names = kwargs.get("station_names", "")
            return await self._get_station_codes_via_mcp(station_names)
        
        elif action == "query_tickets":
            origin = kwargs.get("origin")
            destination = kwargs.get("destination")
            date = kwargs.get("date")
            train_type = kwargs.get("train_type", "GD")
            
            if not origin or not destination:
                return {
                    "success": False,
                    "error": "缺少出发站或到达站参数"
                }
            
            return await self._query_tickets_via_mcp(origin, destination, date, train_type)
        
        else:
            return {"success": False, "error": f"未知操作: {action}"}
    
    def _get_current_date(self) -> Dict[str, Any]:
        """获取当前日期"""
        now = datetime.now()
        return {
            "success": True,
            "data": {
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S"),
                "weekday": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][now.weekday()]
            }
        }
    
    async def _get_station_codes_via_mcp(self, city_names: str) -> Dict[str, Any]:
        """通过 MCP 获取站点代码"""
        try:
            mcp = await self._get_mcp_client()
            
            # 检查 12306-mcp 是否可用
            if "12306-mcp" not in mcp.list_available_servers():
                # 使用本地缓存
                return self._get_station_codes_local(city_names)
            
            # 调用 MCP 工具
            result = await mcp.call_tool(
                "12306-mcp",
                "get-station-code-of-citys",
                {"citys": city_names}
            )
            
            if result.get("success"):
                return {
                    "success": True,
                    "data": result.get("data"),
                    "source": "12306-mcp"
                }
            else:
                # fallback 到本地
                return self._get_station_codes_local(city_names)
                
        except Exception as e:
            logger.warning(f"MCP call failed, using local cache: {e}")
            return self._get_station_codes_local(city_names)
    
    def _get_station_codes_local(self, names: str) -> Dict[str, Any]:
        """从本地缓存获取站点代码"""
        if not names:
            return {"success": False, "error": "请提供站点名称"}
        
        station_list = [n.strip() for n in names.replace("|", ",").split(",")]
        result = {}
        
        for name in station_list:
            if name in self.CITY_STATION_CODES:
                result[name] = {"station_code": self.CITY_STATION_CODES[name]}
            else:
                for station, code in self.CITY_STATION_CODES.items():
                    if name in station or station in name:
                        result[name] = {"station_code": code}
                        break
                else:
                    result[name] = {"station_code": None}
        
        return {"success": True, "data": result, "source": "local_cache"}
    
    def _get_station_code(self, city: str) -> Optional[str]:
        """获取单个城市的站点代码"""
        if city in self.CITY_STATION_CODES:
            return self.CITY_STATION_CODES[city]
        
        for station, code in self.CITY_STATION_CODES.items():
            if city in station or station in city:
                return code
        
        return None
    
    async def _query_tickets_via_mcp(
        self,
        origin: str,
        destination: str,
        date: str = None,
        train_type: str = "GD"
    ) -> Dict[str, Any]:
        """
        通过 MCP 查询火车票
        
        使用 12306-mcp Server 获取真实的火车票信息
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # 获取站点代码
        origin_code = self._get_station_code(origin)
        dest_code = self._get_station_code(destination)
        
        query_info = {
            "origin": origin,
            "origin_code": origin_code,
            "destination": destination,
            "destination_code": dest_code,
            "date": date,
            "query_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        try:
            mcp = await self._get_mcp_client()
            
            # 检查 12306-mcp 是否可用
            available_servers = mcp.list_available_servers()
            logger.info(f"Available MCP servers: {available_servers}")
            
            if "12306-mcp" not in available_servers:
                return {
                    "success": False,
                    "error": "12306-mcp 服务未连接",
                    "query_info": query_info,
                    "suggestion": [
                        "请确保已安装 12306-mcp: npm install -g 12306-mcp",
                        "或直接访问 12306 官网查询"
                    ]
                }
            
            # 先获取站点代码（如果本地没有的话）
            if not origin_code:
                code_result = await mcp.call_tool(
                    "12306-mcp",
                    "get-station-code-of-citys",
                    {"citys": origin}
                )
                if code_result.get("success"):
                    # 解析返回的 JSON
                    try:
                        data = code_result.get("data", "")
                        if isinstance(data, str):
                            import json
                            data = json.loads(data)
                        origin_code = data.get(origin, {}).get("station_code")
                        query_info["origin_code"] = origin_code
                    except:
                        pass
            
            if not dest_code:
                code_result = await mcp.call_tool(
                    "12306-mcp",
                    "get-station-code-of-citys",
                    {"citys": destination}
                )
                if code_result.get("success"):
                    try:
                        data = code_result.get("data", "")
                        if isinstance(data, str):
                            import json
                            data = json.loads(data)
                        dest_code = data.get(destination, {}).get("station_code")
                        query_info["destination_code"] = dest_code
                    except:
                        pass
            
            if not origin_code or not dest_code:
                return {
                    "success": False,
                    "error": f"无法获取站点代码: {origin}({origin_code}) -> {destination}({dest_code})",
                    "query_info": query_info,
                    "suggestion": ["请使用标准城市名称，如：北京、上海"]
                }
            
            # 调用 12306-mcp 查询余票
            logger.info(f"Calling 12306-mcp: {origin}({origin_code}) -> {destination}({dest_code}) on {date}")
            
            result = await mcp.call_tool(
                "12306-mcp",
                "get-tickets",
                {
                    "date": date,
                    "fromStation": origin_code,
                    "toStation": dest_code,
                    "trainFilterFlags": train_type if train_type else "",
                    "limitedNum": 10,
                    "format": "text"
                }
            )
            
            if result.get("success"):
                # 解析 MCP 返回的数据
                raw_data = result.get("data", "")
                trains = self._parse_mcp_train_data(raw_data)
                
                return {
                    "success": True,
                    "data": {
                        "origin": origin,
                        "origin_code": origin_code,
                        "destination": destination,
                        "destination_code": dest_code,
                        "date": date,
                        "query_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "trains": trains,
                        "total": len(trains),
                        "raw_data": raw_data,
                        "data_source": "12306-mcp (真实数据)"
                    }
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "查询失败"),
                    "query_info": query_info,
                    "suggestion": ["请稍后重试或访问 12306 官网"]
                }
                
        except Exception as e:
            logger.error(f"12306 MCP query error: {e}")
            return {
                "success": False,
                "error": f"查询失败: {str(e)}",
                "query_info": query_info,
                "suggestion": [
                    "请确保 12306-mcp 服务正常运行",
                    "或直接访问 12306 官网查询"
                ]
            }
    
    def _parse_mcp_train_data(self, raw_data: str) -> List[Dict[str, Any]]:
        """
        解析 12306-mcp 返回的文本数据
        
        格式示例:
        G6701 北京西(telecode:BXP) -> 石家庄(telecode:SJP) 05:34 -> 06:52 历时：01:18
        - 商务座: 剩余7张票 407元
        - 一等座: 剩余14张票 163元
        - 二等座: 有票 102元
        """
        trains = []
        current_train = None
        
        for line in raw_data.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            
            # 匹配车次行
            train_match = re.match(
                r'^([GDCZTK]\d+)\s+(.+?)\(telecode:(\w+)\)\s*->\s*(.+?)\(telecode:(\w+)\)\s+(\d{2}:\d{2})\s*->\s*(\d{2}:\d{2})\s+历时[：:](\d{2}:\d{2})',
                line
            )
            
            if train_match:
                # 保存之前的车次
                if current_train:
                    trains.append(current_train)
                
                # 开始新车次
                current_train = {
                    "train_no": train_match.group(1),
                    "train_type": self._get_train_type(train_match.group(1)),
                    "origin_station": train_match.group(2),
                    "origin_code": train_match.group(3),
                    "destination_station": train_match.group(4),
                    "destination_code": train_match.group(5),
                    "departure_time": train_match.group(6),
                    "arrival_time": train_match.group(7),
                    "duration": train_match.group(8),
                    "seats": {}
                }
            
            # 匹配座位行
            elif current_train and line.startswith("-"):
                seat_match = re.match(
                    r'^-\s*(.+?):\s*(剩余(\d+)张票|有票|无票)\s*(\d+)元?',
                    line
                )
                if seat_match:
                    seat_type = seat_match.group(1)
                    availability = seat_match.group(2)
                    price = seat_match.group(4) + "元" if seat_match.group(4) else ""
                    
                    if "有票" in availability:
                        current_train["seats"][seat_type] = f"有票 {price}"
                    elif "剩余" in availability:
                        count = seat_match.group(3)
                        current_train["seats"][seat_type] = f"{count}张 {price}"
                    # 无票的不添加
        
        # 别忘了最后一个车次
        if current_train:
            trains.append(current_train)
        
        return trains
    
    def _get_train_type(self, train_no: str) -> str:
        """根据车次号获取类型"""
        if train_no.startswith("G"):
            return "高铁"
        elif train_no.startswith("D"):
            return "动车"
        elif train_no.startswith("C"):
            return "城际"
        elif train_no.startswith("Z"):
            return "直达"
        elif train_no.startswith("T"):
            return "特快"
        elif train_no.startswith("K"):
            return "快速"
        else:
            return "普通"
