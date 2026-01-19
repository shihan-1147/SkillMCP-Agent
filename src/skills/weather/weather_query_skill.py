"""
天气查询技能
查询城市天气信息
"""
from typing import Dict, Any, Optional, TYPE_CHECKING
import re

from ..base import BaseSkill
from src.core.logging import get_logger

if TYPE_CHECKING:
    from src.mcp.client import MCPClient

logger = get_logger("skills.weather")


class WeatherQuerySkill(BaseSkill):
    """
    天气查询技能
    
    能力：
    - 查询城市实时天气
    - 查询天气预报
    - 生成出行建议
    
    依赖的 MCP 工具：
    - amap_weather: 高德天气查询
    """
    
    name = "weather_query"
    description = "查询城市天气信息，包括实时天气、预报、穿衣建议。适用于出行规划场景。"
    required_tools = ["mcp_amap_amap_maps_weather"]
    
    # 天气与建议的映射
    WEATHER_SUGGESTIONS = {
        "晴": "天气晴好，适合户外活动，注意防晒。",
        "多云": "多云天气，温度适宜，可以外出。",
        "阴": "阴天，可能较凉，建议携带外套。",
        "小雨": "有小雨，建议携带雨具。",
        "中雨": "中雨天气，出行请携带雨伞，注意路滑。",
        "大雨": "大雨天气，建议减少外出，注意安全。",
        "暴雨": "暴雨预警，请尽量避免外出。",
        "雪": "下雪天气，注意保暖和路面湿滑。",
        "雾": "有雾，能见度低，驾车请注意安全。",
        "霾": "有霾，空气质量较差，建议佩戴口罩。",
    }
    
    def __init__(self):
        """初始化技能"""
        super().__init__()
    
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
        执行天气查询
        
        Args:
            description: 查询描述
            tool_params: 预解析的参数 (city)
            context: 上下文信息
            mcp_client: MCP 客户端
            
        Returns:
            天气查询结果
        """
        logger.info(f"Executing weather query: {description}")
        
        if mcp_client is None:
            return {"success": False, "error": "MCP 客户端未提供"}
        
        try:
            # 步骤1: 解析查询参数
            params = self._parse_query_params(description, tool_params, context)
            city = params.get("city")
            
            if not city:
                return {"success": False, "error": "未能识别城市名称"}
            
            # 步骤2: 调用天气查询工具
            weather_data = await mcp_client.call_tool(
                "mcp_amap_amap_maps_weather",
                {"city": city}
            )
            
            # 步骤3: 格式化结果
            result = self._format_result(city, weather_data)
            
            logger.info(f"Weather query completed for {city}")
            return result
            
        except Exception as e:
            logger.error(f"Weather query failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _parse_query_params(
        self,
        description: str,
        tool_params: Dict[str, Any] = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        解析查询参数
        
        从描述文本中提取城市名
        """
        params = tool_params.copy() if tool_params else {}
        
        # 如果已有城市参数，直接返回
        if params.get("city"):
            return params
        
        # 尝试从描述中提取城市
        # 模式1: "X的天气" 或 "X天气"
        pattern1 = r"([^\s]+?)(?:的)?天气"
        match = re.search(pattern1, description)
        if match:
            params["city"] = match.group(1)
            return params
        
        # 模式2: 常见城市名直接匹配
        common_cities = [
            "北京", "上海", "广州", "深圳", "杭州", "成都", "武汉",
            "南京", "西安", "重庆", "苏州", "天津", "青岛", "厦门"
        ]
        for city in common_cities:
            if city in description:
                params["city"] = city
                return params
        
        # 模式3: 从上下文获取
        if context and context.get("city"):
            params["city"] = context["city"]
        
        return params
    
    def _format_result(
        self,
        city: str,
        weather_data: Any
    ) -> Dict[str, Any]:
        """格式化天气查询结果"""
        result = {
            "success": True,
            "data": {
                "city": city,
                "weather": None,
                "temperature": None,
                "humidity": None,
                "wind": None,
                "suggestion": None
            }
        }
        
        # 解析天气数据
        if isinstance(weather_data, dict):
            # 提取天气信息
            weather = weather_data.get("weather") or weather_data.get("condition")
            temperature = weather_data.get("temperature") or weather_data.get("temp")
            humidity = weather_data.get("humidity")
            wind = weather_data.get("wind") or weather_data.get("winddirection")
            wind_power = weather_data.get("windpower") or weather_data.get("wind_power")
            
            result["data"]["weather"] = weather
            result["data"]["temperature"] = f"{temperature}°C" if temperature else None
            result["data"]["humidity"] = f"{humidity}%" if humidity else None
            result["data"]["wind"] = f"{wind} {wind_power}级" if wind and wind_power else wind
            result["data"]["update_time"] = weather_data.get("reporttime")
            
            # 生成建议
            result["data"]["suggestion"] = self._generate_suggestion(weather, temperature)
            
            # 保留原始数据
            result["data"]["raw"] = weather_data
        elif isinstance(weather_data, str):
            result["data"]["raw"] = weather_data
        else:
            result["data"]["raw"] = str(weather_data)
        
        return result
    
    def _generate_suggestion(
        self,
        weather: Optional[str],
        temperature: Optional[str]
    ) -> str:
        """根据天气生成建议"""
        if not weather:
            return "无法获取天气信息，请稍后重试。"
        
        # 查找匹配的建议
        for key, suggestion in self.WEATHER_SUGGESTIONS.items():
            if key in weather:
                return suggestion
        
        # 默认建议
        return f"当前天气{weather}，请根据实际情况安排出行。"
