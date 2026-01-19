"""
MCP 工具层测试脚本

验证 MCP 工具的功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_tools():
    """测试各个 MCP 工具"""
    print("=" * 60)
    print("MCP 工具层测试")
    print("=" * 60)
    
    # 导入工具
    from src.mcp.tools import TrainQueryTool, WeatherQueryTool, SystemTimeTool, RAGRetrieverTool
    
    # 1. 测试系统时间工具
    print("\n[1] 测试 SystemTimeTool")
    print("-" * 40)
    
    time_tool = SystemTimeTool()
    print(f"工具名称: {time_tool.name}")
    print(f"工具描述: {time_tool.description}")
    
    # 获取当前时间
    result = await time_tool.execute(action="get_current")
    print(f"当前时间: {result['data']['datetime']}")
    print(f"星期: {result['data']['weekday_name']}")
    
    # 解析相对日期
    result = await time_tool.execute(action="parse_relative", relative_expr="明天")
    print(f"明天是: {result['data']['parsed_date']}")
    
    result = await time_tool.execute(action="parse_relative", relative_expr="下周五")
    print(f"下周五是: {result['data']['parsed_date']}")
    
    # 2. 测试天气查询工具
    print("\n[2] 测试 WeatherQueryTool")
    print("-" * 40)
    
    weather_tool = WeatherQueryTool()
    print(f"工具名称: {weather_tool.name}")
    
    # 实时天气
    result = await weather_tool.execute(city="北京", type="live")
    if result["success"]:
        data = result["data"]
        print(f"北京天气: {data['weather']} {data['weather_icon']}")
        print(f"温度: {data['temperature']}℃")
        print(f"空气质量: {data['air_quality']['level']} (AQI: {data['air_quality']['aqi']})")
        print(f"建议: {data['suggestion']}")
    
    # 天气预报
    result = await weather_tool.execute(city="上海", type="forecast")
    if result["success"]:
        print(f"\n上海未来三天天气:")
        for forecast in result["data"]["forecasts"][:3]:
            print(f"  {forecast['date']} ({forecast['weekday']}): "
                  f"{forecast['weather_day']}, {forecast['temperature_low']}~{forecast['temperature_high']}℃")
    
    # 3. 测试火车票查询工具
    print("\n[3] 测试 TrainQueryTool (12306)")
    print("-" * 40)
    
    train_tool = TrainQueryTool()
    print(f"工具名称: {train_tool.name}")
    
    # 获取站点代码
    result = await train_tool.execute(action="get_station_code", station_names="北京,上海,广州")
    print(f"站点代码: {result['data']}")
    
    # 查询余票
    result = await train_tool.execute(
        action="query_tickets",
        origin="北京",
        destination="上海",
        date="2025-01-20"
    )
    if result["success"]:
        print(f"\n{result['data']['origin']} → {result['data']['destination']} ({result['data']['date']})")
        print(f"共 {result['data']['total']} 个车次:\n")
        for train in result["data"]["trains"][:5]:
            print(f"  {train['train_no']} ({train['train_type']})")
            print(f"    {train['departure_time']} → {train['arrival_time']} ({train['duration']})")
            print(f"    座位: {train['seats']}")
            print()
    
    # 4. 测试 RAG 检索工具
    print("\n[4] 测试 RAGRetrieverTool")
    print("-" * 40)
    
    rag_tool = RAGRetrieverTool()
    print(f"工具名称: {rag_tool.name}")
    
    # 检索
    result = await rag_tool.execute(query="AI Agent 架构", top_k=3)
    if result["success"]:
        print(f"查询: '{result['data']['query']}'")
        print(f"找到 {result['data']['total']} 个相关文档:\n")
        for doc in result["data"]["documents"]:
            print(f"  [{doc['score']:.2f}] {doc['title']}")
            print(f"       {doc['content'][:80]}...")
            print()
    
    # 5. 测试 MCP 系统整体
    print("\n[5] 测试 MCP 系统整合")
    print("-" * 40)
    
    from src.mcp import initialize_mcp, call_tool
    
    # 初始化 MCP 系统
    mcp = await initialize_mcp()
    print(f"已加载工具: {mcp.list_tools()}")
    
    # 通过系统调用工具
    result = await call_tool("system_time", action="get_current")
    print(f"通过 MCP 系统获取时间: {result['data']['datetime']}")
    
    # 获取 LLM 格式的工具定义
    tools_for_llm = mcp.get_tools_for_llm()
    print(f"\nLLM 工具定义 ({len(tools_for_llm)} 个):")
    for tool in tools_for_llm:
        print(f"  - {tool['function']['name']}: {tool['function']['description'][:50]}...")
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_tools())
