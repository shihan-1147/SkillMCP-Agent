"""
测试 Agent 追踪器和工具记录器

验证执行流程日志和工具调用记录功能
"""

import asyncio
import sys

sys.path.insert(0, "E:\\SkillMCP-Agent")

from src.agent.tool_recorder import (ToolRecorder, get_tool_recorder,
                                     record_tool_call)
from src.agent.tracer import (AgentTracer, TraceEventType, create_tracer,
                              get_tracer)


def test_tracer():
    """测试追踪器"""
    print("\n" + "=" * 60)
    print("测试 1: Agent 追踪器")
    print("=" * 60 + "\n")

    # 创建追踪器
    tracer = create_tracer(enable_console=True)

    # 模拟完整的 Agent 执行流程
    tracer.start(query="北京今天天气怎么样？")

    # 规划阶段
    with tracer.trace(TraceEventType.PLANNER_START):
        tracer.log_intent("weather")
        tracer.log_plan(["解析城市", "调用天气API", "格式化结果"])

    # 技能选择
    tracer.log_skill_selected("weather_skill", "检测到天气关键词")

    # MCP 工具调用
    tracer.log_event(TraceEventType.MCP_CALL_START, {"tool": "weather_query"})
    tracer.log_tool_call(
        tool_name="weather_query",
        arguments={"city": "北京", "type": "live"},
        result={"success": True, "temperature": 25},
        success=True,
        duration_ms=150.5,
    )

    # 结束
    tracer.end(success=True, result="北京当前天气晴，温度25℃")

    # 获取报告
    print("\n--- 追踪报告 ---")
    report = tracer.get_report()
    print(f"追踪 ID: {report['trace_id']}")
    print(f"总耗时: {report['total_duration_ms']:.1f}ms")
    print(f"事件数: {report['event_count']}")
    print(f"工具调用数: {report['tool_call_count']}")

    print("\n--- 时间线 ---")
    for item in tracer.get_timeline():
        print(f"  {item['time']} | {item['type']} | {item['summary']}")

    print("\n✅ 追踪器测试完成")


def test_tool_recorder():
    """测试工具记录器"""
    print("\n" + "=" * 60)
    print("测试 2: 工具调用记录器")
    print("=" * 60 + "\n")

    # 创建记录器（不持久化）
    recorder = ToolRecorder(max_entries=100)

    # 模拟多次工具调用
    print("记录工具调用...")

    # 调用 1
    entry1 = recorder.start_call(
        tool_name="weather_query",
        arguments={"city": "北京"},
        session_id="sess_001",
        skill_name="weather_skill",
    )
    recorder.end_call(entry1.id, result={"temp": 25})

    # 调用 2
    entry2 = recorder.start_call(
        tool_name="12306_query",
        arguments={"origin": "北京", "destination": "上海"},
        session_id="sess_001",
        skill_name="train_skill",
    )
    recorder.end_call(entry2.id, result={"trains": []})

    # 调用 3 (失败)
    entry3 = recorder.start_call(
        tool_name="weather_query",
        arguments={"city": "火星"},
        session_id="sess_002",
        skill_name="weather_skill",
    )
    recorder.end_call(entry3.id, error="城市不存在")

    # 一次性记录
    recorder.record_call(
        tool_name="system_time",
        arguments={"action": "get_current"},
        result={"date": "2024-01-15"},
        duration_ms=5.0,
        session_id="sess_001",
    )

    # 统计信息
    print("\n--- 统计信息 ---")
    stats = recorder.get_statistics()
    print(f"总调用次数: {stats['total_calls']}")
    print(f"成功次数: {stats['successful_calls']}")
    print(f"失败次数: {stats['failed_calls']}")
    print(f"成功率: {stats['success_rate']:.1f}%")
    print(f"平均耗时: {stats['avg_duration_ms']:.1f}ms")
    print(f"使用的工具数: {stats['unique_tools']}")

    print("\n--- 工具分布 ---")
    for tool, tool_stats in stats["tool_stats"].items():
        print(
            f"  {tool}: {tool_stats['count']}次, 成功率 {tool_stats['success_rate']:.1f}%"
        )

    # 查询功能
    print("\n--- 查询示例 ---")
    print(f"按会话查询 (sess_001): {len(recorder.get_calls_by_session('sess_001'))} 条")
    print(
        f"按工具查询 (weather_query): {len(recorder.get_calls_by_tool('weather_query'))} 条"
    )
    print(f"失败的调用: {len(recorder.get_failed_calls())} 条")

    # Markdown 报告
    print("\n--- Markdown 报告 ---")
    md_report = recorder.export_report(format="markdown")
    print(md_report[:500] + "...\n")

    print("✅ 工具记录器测试完成")


def test_global_recorder():
    """测试全局记录器"""
    print("\n" + "=" * 60)
    print("测试 3: 全局记录器 (便捷函数)")
    print("=" * 60 + "\n")

    # 使用便捷函数
    entry = record_tool_call(
        tool_name="test_tool",
        arguments={"param": "value"},
        result={"status": "ok"},
        session_id="global_test",
    )

    print(f"记录成功: {entry.id}")
    print(f"工具: {entry.tool_name}")
    print(f"成功: {entry.success}")

    # 获取全局记录器
    global_recorder = get_tool_recorder()
    print(f"\n全局记录器中的记录数: {len(global_recorder.get_all_calls())}")

    print("\n✅ 全局记录器测试完成")


async def test_integration():
    """集成测试：模拟完整的 Chat 处理流程"""
    print("\n" + "=" * 60)
    print("测试 4: 集成测试 (模拟 Chat 流程)")
    print("=" * 60 + "\n")

    tracer = create_tracer(enable_console=True)
    recorder = ToolRecorder()

    query = "明天从北京到上海的高铁票"
    tracer.start(query=query)

    # 1. 规划阶段
    with tracer.trace(TraceEventType.PLANNER_START):
        await asyncio.sleep(0.01)  # 模拟处理时间
        tracer.log_intent("train")
        tracer.log_plan(
            ["解析出发地和目的地", "解析日期", "调用 12306 API", "格式化结果"]
        )

    # 2. 技能选择
    tracer.log_skill_selected("train_skill", "检测到火车票关键词")

    # 3. 工具调用：获取时间
    tracer.log_event(TraceEventType.MCP_CALL_START, {"tool": "system_time"})
    await asyncio.sleep(0.005)
    tracer.log_tool_call(
        "system_time",
        {"action": "parse_relative", "relative_expr": "明天"},
        {"parsed_date": "2024-01-16"},
        True,
        duration_ms=5.2,
    )
    recorder.record_call(
        "system_time",
        {"action": "parse_relative"},
        {"parsed_date": "2024-01-16"},
        duration_ms=5.2,
        skill_name="train_skill",
    )

    # 4. 工具调用：查询车票
    tracer.log_event(TraceEventType.MCP_CALL_START, {"tool": "12306_query"})
    await asyncio.sleep(0.15)
    tracer.log_tool_call(
        "12306_query",
        {"origin": "北京", "destination": "上海", "date": "2024-01-16"},
        {"trains": [{"train_no": "G1", "departure": "06:36"}]},
        True,
        duration_ms=152.3,
    )
    recorder.record_call(
        "12306_query",
        {"origin": "北京", "destination": "上海"},
        {"trains": [{"train_no": "G1"}]},
        duration_ms=152.3,
        skill_name="train_skill",
    )

    # 5. 结束
    tracer.end(success=True)

    # 输出结果
    print("\n--- 执行摘要 ---")
    report = tracer.get_report()
    print(f"查询: {query}")
    print(f"总耗时: {report['total_duration_ms']:.1f}ms")
    print(f"工具调用: {report['tool_call_count']}次")

    print("\n--- 工具统计 ---")
    stats = recorder.get_statistics()
    for tool, s in stats["tool_stats"].items():
        print(f"  {tool}: {s['count']}次, 平均 {s.get('avg_duration_ms', 0):.1f}ms")

    print("\n✅ 集成测试完成")


def main():
    """运行所有测试"""
    print("\n" + "🔍" * 30)
    print("\n  SkillMCP-Agent 追踪系统测试")
    print("\n" + "🔍" * 30)

    # 同步测试
    test_tracer()
    test_tool_recorder()
    test_global_recorder()

    # 异步测试
    asyncio.run(test_integration())

    print("\n" + "=" * 60)
    print("🎉 所有测试完成！")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
