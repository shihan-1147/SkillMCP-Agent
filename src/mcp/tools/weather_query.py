"""
天气查询工具
MCP 标准工具实现 - 调用真实的高德天气 API
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx

from .base import BaseTool
from ..protocol.types import Tool, ToolParameter, ParameterType
from src.core.logging import get_logger
from src.core.config import get_settings

logger = get_logger("mcp.tools.weather_query")


class WeatherQueryTool(BaseTool):
    """
    天气查询工具 - 使用高德地图天气 API
    
    高德天气 API 文档: https://lbs.amap.com/api/webservice/guide/api/weatherinfo
    """
    
    name = "weather_query"
    description = "查询城市天气信息（调用高德地图真实 API）"
    category = "weather"
    version = "2.0.0"
    
    # 高德天气 API 地址
    AMAP_WEATHER_URL = "https://restapi.amap.com/v3/weather/weatherInfo"
    
    # 城市编码表（部分常用城市）
    CITY_CODES = {
        "北京": "110000", "上海": "310000", "广州": "440100", "深圳": "440300",
        "杭州": "330100", "成都": "510100", "武汉": "420100", "西安": "610100",
        "南京": "320100", "重庆": "500000", "天津": "120000", "苏州": "320500",
        "青岛": "370200", "厦门": "350200", "大连": "210200", "哈尔滨": "230100",
        "长沙": "430100", "郑州": "410100", "济南": "370100", "沈阳": "210100",
        "石家庄": "130100", "太原": "140100", "合肥": "340100", "南昌": "360100",
        "福州": "350100", "昆明": "530100", "贵阳": "520100", "南宁": "450100",
        "海口": "460100", "兰州": "620100", "西宁": "630100", "银川": "640100",
        "乌鲁木齐": "650100", "拉萨": "540100", "呼和浩特": "150100",
        "长春": "220100", "无锡": "320200", "宁波": "330200", "温州": "330300",
        "东莞": "441900", "佛山": "440600", "珠海": "440400", "中山": "442000",
        "保定": "130600", "唐山": "130200", "秦皇岛": "130300", "邯郸": "130400",
        "廊坊": "131000", "沧州": "130900",
    }
    
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.api_key = self.settings.amap_api_key
    
    def get_parameters(self) -> List[ToolParameter]:
        """定义工具参数"""
        return [
            ToolParameter(
                name="city",
                type=ParameterType.STRING,
                description="城市名称（中文）",
                required=True
            ),
            ToolParameter(
                name="type",
                type=ParameterType.STRING,
                description="查询类型: live(实时天气) 或 forecast(天气预报)",
                required=False,
                default="live",
                enum=["live", "forecast"]
            ),
        ]
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行天气查询 - 调用高德真实 API
        
        Args:
            city: 城市名称
            type: 查询类型 (live/forecast)
            
        Returns:
            天气数据或错误信息
        """
        city = kwargs.get("city")
        query_type = kwargs.get("type", "live")
        
        if not city:
            return {"success": False, "error": "请提供城市名称"}
        
        # 获取城市编码
        city_code = self._get_city_code(city)
        if not city_code:
            return {
                "success": False, 
                "error": f"未找到城市 '{city}' 的编码，请检查城市名称是否正确"
            }
        
        # 检查 API Key
        if not self.api_key:
            return {
                "success": False,
                "error": "未配置高德地图 API Key，请在 .env 中设置 AMAP_API_KEY"
            }
        
        # 调用高德天气 API
        try:
            extensions = "all" if query_type == "forecast" else "base"
            
            logger.info(f"Calling AMAP Weather API for {city} ({city_code})")
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.AMAP_WEATHER_URL,
                    params={
                        "key": self.api_key,
                        "city": city_code,
                        "extensions": extensions,
                        "output": "JSON"
                    }
                )
                
                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"高德 API 请求失败，HTTP {response.status_code}"
                    }
                
                data = response.json()
                logger.info(f"AMAP API response status: {data.get('status')}, info: {data.get('info')}")
                
                # 检查 API 返回状态
                if data.get("status") != "1":
                    error_info = data.get("info", "未知错误")
                    infocode = data.get("infocode", "")
                    return {
                        "success": False,
                        "error": f"高德 API 返回错误: {error_info} (code: {infocode})"
                    }
                
                # 解析天气数据
                if query_type == "live":
                    return self._parse_live_weather(data, city)
                else:
                    return self._parse_forecast_weather(data, city)
                    
        except httpx.TimeoutException:
            return {"success": False, "error": "高德 API 请求超时，请稍后重试"}
        except httpx.RequestError as e:
            return {"success": False, "error": f"网络请求错误: {str(e)}"}
        except Exception as e:
            logger.error(f"Weather query error: {e}")
            return {"success": False, "error": f"查询失败: {str(e)}"}
    
    def _get_city_code(self, city: str) -> Optional[str]:
        """获取城市编码"""
        # 精确匹配
        if city in self.CITY_CODES:
            return self.CITY_CODES[city]
        
        # 模糊匹配（去掉"市"后缀）
        city_name = city.rstrip("市")
        if city_name in self.CITY_CODES:
            return self.CITY_CODES[city_name]
        
        # 尝试包含匹配
        for name, code in self.CITY_CODES.items():
            if city in name or name in city:
                return code
        
        return None
    
    def _parse_live_weather(self, data: Dict, city: str) -> Dict[str, Any]:
        """解析实时天气数据"""
        lives = data.get("lives", [])
        if not lives:
            return {"success": False, "error": "未获取到天气数据"}
        
        live = lives[0]
        
        # 获取天气图标
        weather = live.get("weather", "未知")
        weather_icon = self._get_weather_icon(weather)
        
        # 生成建议
        suggestion = self._generate_suggestion(
            weather, 
            live.get("temperature", "0"),
            live.get("humidity", "50")
        )
        
        return {
            "success": True,
            "data": {
                "city": live.get("city", city),
                "province": live.get("province", ""),
                "weather": weather,
                "weather_icon": weather_icon,
                "temperature": live.get("temperature", "N/A"),
                "temperature_unit": "℃",
                "humidity": live.get("humidity", "N/A") + "%",
                "wind_direction": live.get("winddirection", "N/A"),
                "wind_power": live.get("windpower", "N/A") + "级",
                "report_time": live.get("reporttime", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                "suggestion": suggestion,
                "data_source": "高德地图天气 API (真实数据)"
            }
        }
    
    def _parse_forecast_weather(self, data: Dict, city: str) -> Dict[str, Any]:
        """解析天气预报数据"""
        forecasts = data.get("forecasts", [])
        if not forecasts:
            return {"success": False, "error": "未获取到预报数据"}
        
        forecast = forecasts[0]
        casts = forecast.get("casts", [])
        
        forecast_list = []
        for cast in casts:
            forecast_list.append({
                "date": cast.get("date", ""),
                "week": cast.get("week", ""),
                "day_weather": cast.get("dayweather", ""),
                "night_weather": cast.get("nightweather", ""),
                "day_temp": cast.get("daytemp", "") + "℃",
                "night_temp": cast.get("nighttemp", "") + "℃",
                "day_wind": cast.get("daywind", "") + " " + cast.get("daypower", "") + "级",
                "night_wind": cast.get("nightwind", "") + " " + cast.get("nightpower", "") + "级",
            })
        
        return {
            "success": True,
            "data": {
                "city": forecast.get("city", city),
                "province": forecast.get("province", ""),
                "report_time": forecast.get("reporttime", ""),
                "forecasts": forecast_list,
                "data_source": "高德地图天气 API (真实数据)"
            }
        }
    
    def _get_weather_icon(self, weather: str) -> str:
        """根据天气返回图标"""
        icon_map = {
            "晴": "☀️", "多云": "⛅", "阴": "☁️",
            "小雨": "🌧️", "中雨": "🌧️", "大雨": "🌧️", "暴雨": "⛈️",
            "雷阵雨": "⛈️", "阵雨": "🌦️",
            "小雪": "🌨️", "中雪": "❄️", "大雪": "❄️", "暴雪": "❄️",
            "雨夹雪": "🌨️", "冻雨": "🌨️",
            "雾": "🌫️", "霾": "🌫️", "沙尘": "🌪️",
        }
        
        for key, icon in icon_map.items():
            if key in weather:
                return icon
        return "🌡️"
    
    def _generate_suggestion(self, weather: str, temp: str, humidity: str) -> str:
        """生成天气建议"""
        suggestions = []
        
        try:
            temp_val = int(temp)
            humidity_val = int(humidity.rstrip("%"))
        except:
            temp_val = 20
            humidity_val = 50
        
        # 温度建议
        if temp_val < 5:
            suggestions.append("气温较低，请注意保暖，穿厚外套")
        elif temp_val < 15:
            suggestions.append("天气微凉，建议穿长袖外套")
        elif temp_val > 30:
            suggestions.append("天气炎热，注意防暑降温")
        
        # 天气建议
        if "雨" in weather:
            suggestions.append("有雨，外出请携带雨具")
        if "雪" in weather:
            suggestions.append("有雪，注意路面湿滑")
        if "霾" in weather or "雾" in weather:
            suggestions.append("能见度低，建议佩戴口罩，减少外出")
        if "晴" in weather and temp_val > 25:
            suggestions.append("阳光充足，注意防晒")
        
        return "；".join(suggestions) if suggestions else "天气适宜，适合外出"
