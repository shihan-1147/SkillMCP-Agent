"""
Skills 层单元测试
"""

# 添加项目路径
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from skills.base import BaseSkill
from skills.direct_answer import DirectAnswerSkill
from skills.knowledge import KnowledgeSearchSkill
from skills.loader import SkillLoader
from skills.registry import SkillRegistry
from skills.summarize import SummarizeSkill
from skills.travel import TravelQuerySkill
from skills.weather import WeatherQuerySkill


class TestSkillRegistry:
    """测试技能注册中心"""

    def test_register_and_get(self):
        """测试技能注册和获取"""
        registry = SkillRegistry()
        skill = DirectAnswerSkill()

        registry.register(skill)

        assert registry.has_skill("direct_answer")
        assert registry.get("direct_answer") == skill

    def test_list_skills(self):
        """测试列出技能"""
        registry = SkillRegistry()
        registry.register(DirectAnswerSkill())
        registry.register(TravelQuerySkill())

        skills = registry.list_skills()
        assert len(skills) == 2

    def test_get_skills_for_planner(self):
        """测试获取 Planner 使用的技能描述"""
        registry = SkillRegistry()
        registry.register(WeatherQuerySkill())

        skills = registry.get_skills_for_planner()
        assert "weather_query" in skills
        assert "description" in skills["weather_query"]


class TestTravelQuerySkill:
    """测试火车票查询技能"""

    def test_skill_metadata(self):
        """测试技能元数据"""
        skill = TravelQuerySkill()

        assert skill.name == "travel_query"
        assert len(skill.required_tools) > 0
        assert "12306" in skill.required_tools[0]

    def test_parse_query_params(self):
        """测试查询参数解析"""
        skill = TravelQuerySkill()

        # 测试 "从X到Y" 模式
        params = skill._parse_query_params("从北京到上海的高铁", {}, {})
        assert params["origin"] == "北京"
        assert params["destination"] == "上海"
        assert params.get("train_type") == "G"

    @pytest.mark.asyncio
    async def test_execute_without_client(self):
        """测试无客户端时的执行"""
        skill = TravelQuerySkill()
        result = await skill.execute("查询火车票", mcp_client=None)

        assert result["success"] == False
        assert "MCP" in result["error"]


class TestWeatherQuerySkill:
    """测试天气查询技能"""

    def test_skill_metadata(self):
        """测试技能元数据"""
        skill = WeatherQuerySkill()

        assert skill.name == "weather_query"
        assert "amap" in skill.required_tools[0].lower()

    def test_parse_city(self):
        """测试城市解析"""
        skill = WeatherQuerySkill()

        params = skill._parse_query_params("北京天气怎么样", {}, {})
        assert params["city"] == "北京"

        params = skill._parse_query_params("上海的天气", {}, {})
        assert params["city"] == "上海"

    def test_weather_suggestions(self):
        """测试天气建议生成"""
        skill = WeatherQuerySkill()

        suggestion = skill._generate_suggestion("晴", "25")
        assert "晴" in suggestion or "防晒" in suggestion

        suggestion = skill._generate_suggestion("小雨", "18")
        assert "雨" in suggestion


class TestKnowledgeSearchSkill:
    """测试知识检索技能"""

    def test_skill_metadata(self):
        """测试技能元数据"""
        skill = KnowledgeSearchSkill()

        assert skill.name == "knowledge_search"
        assert "rag" in skill.required_tools[0].lower()

    def test_build_rag_prompt(self):
        """测试 RAG Prompt 构建"""
        skill = KnowledgeSearchSkill()

        prompt = skill.build_rag_prompt(
            query="什么是机器学习", context="机器学习是一种人工智能技术..."
        )

        assert "机器学习" in prompt
        assert "参考资料" in prompt


class TestSummarizeSkill:
    """测试结果整合技能"""

    def test_skill_metadata(self):
        """测试技能元数据"""
        skill = SummarizeSkill()

        assert skill.name == "summarize"
        assert len(skill.required_tools) == 0  # 不需要外部工具

    def test_extract_content(self):
        """测试内容提取"""
        skill = SummarizeSkill()

        # 字符串
        assert skill._extract_content("hello") == "hello"

        # 字典
        result = skill._extract_content({"content": "world"})
        assert result == "world"

        # 列表
        result = skill._extract_content(["a", "b"])
        assert "a" in result and "b" in result

    @pytest.mark.asyncio
    async def test_simple_summarize(self):
        """测试简单整合（无 LLM）"""
        skill = SummarizeSkill()

        result = await skill.execute(
            description="整合结果",
            tool_params={
                "inputs": [
                    {"source": "天气", "content": "今天晴天"},
                    {"source": "交通", "content": "有高铁"},
                ],
                "format": "markdown",
            },
        )

        assert result["success"] == True
        assert "天气" in result["data"]["summary"]


class TestSkillLoader:
    """测试技能加载器"""

    def test_load_all_skills(self):
        """测试加载所有技能"""
        registry = SkillRegistry()
        loader = SkillLoader(registry=registry)

        loaded = loader.load_all()

        assert len(loaded) == len(loader.BUILTIN_SKILLS)
        assert "direct_answer" in loaded
        assert "travel_query" in loaded

    def test_load_single_skill(self):
        """测试加载单个技能"""
        registry = SkillRegistry()
        loader = SkillLoader(registry=registry)

        skill = loader.load_skill("weather_query")

        assert skill is not None
        assert skill.name == "weather_query"

    def test_list_available_skills(self):
        """测试列出可用技能"""
        loader = SkillLoader()

        available = loader.list_available_skills()

        assert "direct_answer" in available
        assert "travel_query" in available
        assert "weather_query" in available
        assert "knowledge_search" in available
        assert "summarize" in available


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
