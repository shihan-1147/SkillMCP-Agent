"""
Agent 模块单元测试
"""

import asyncio
# 添加项目路径
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent.executor import Executor
from agent.memory.long_term import LongTermMemory
from agent.memory.manager import MemoryManager
from agent.memory.short_term import ShortTermMemory
from agent.planner import Planner
from agent.schemas.message import Message, MessageRole
from agent.schemas.task import StepStatus, Task, TaskPlan, TaskStep
from agent.skill_selector import SkillSelector


class TestTaskSchemas:
    """测试任务数据结构"""

    def test_task_step_creation(self):
        """测试 TaskStep 创建"""
        step = TaskStep(step_id=1, description="测试步骤", skill_name="test_skill")
        assert step.step_id == 1
        assert step.status == StepStatus.PENDING
        assert step.result is None

    def test_task_plan_creation(self):
        """测试 TaskPlan 创建"""
        steps = [
            TaskStep(step_id=1, description="步骤1", skill_name="skill1"),
            TaskStep(
                step_id=2, description="步骤2", skill_name="skill2", depends_on=[1]
            ),
        ]
        plan = TaskPlan(
            plan_id="test_plan", original_query="测试查询", goal="测试目标", steps=steps
        )
        assert len(plan.steps) == 2
        assert not plan.is_completed()

    def test_plan_get_next_step(self):
        """测试获取下一个待执行步骤"""
        steps = [
            TaskStep(step_id=1, description="步骤1", skill_name="skill1"),
            TaskStep(
                step_id=2, description="步骤2", skill_name="skill2", depends_on=[1]
            ),
        ]
        plan = TaskPlan(
            plan_id="test", original_query="query", goal="goal", steps=steps
        )

        # 应该返回第一个步骤
        next_step = plan.get_next_step()
        assert next_step.step_id == 1

        # 标记第一个完成后，应该返回第二个
        steps[0].status = StepStatus.COMPLETED
        next_step = plan.get_next_step()
        assert next_step.step_id == 2


class TestMemory:
    """测试记忆模块"""

    def test_short_term_memory(self):
        """测试短期记忆"""
        memory = ShortTermMemory(max_messages=5)

        # 添加消息
        memory.add_user_message("你好")
        memory.add_assistant_message("你好！有什么可以帮助你的？")

        assert len(memory) == 2

        messages = memory.get_messages(include_system=False)
        assert len(messages) == 2
        assert messages[0].role == MessageRole.USER

    def test_short_term_memory_sliding_window(self):
        """测试短期记忆滑动窗口"""
        memory = ShortTermMemory(max_messages=3)

        for i in range(5):
            memory.add_user_message(f"消息 {i}")

        # 应该只保留最后 3 条
        assert len(memory) == 3

    def test_long_term_memory(self):
        """测试长期记忆"""
        memory = LongTermMemory()

        # 存储记忆
        entry_id = memory.store("测试记忆", category="fact", importance=0.8)
        assert entry_id is not None

        # 检索记忆
        entries = memory.retrieve(category="fact")
        assert len(entries) == 1
        assert entries[0].content == "测试记忆"

    def test_memory_manager(self):
        """测试记忆管理器"""
        manager = MemoryManager()

        manager.add_user_input("测试输入")
        manager.add_agent_response("测试响应")

        context = manager.get_conversation_context()
        # 应该有 2 条消息（不含系统消息）
        assert len(context) >= 2


class TestSkillSelector:
    """测试技能选择器"""

    def test_register_and_get_skill(self):
        """测试技能注册和获取"""
        selector = SkillSelector()

        # 创建模拟技能
        mock_skill = MagicMock()
        mock_skill.description = "测试技能"

        selector.register_skill("test_skill", mock_skill)

        # 获取技能
        skill = selector.get_skill("test_skill")
        assert skill is not None

        # 列出技能
        skills = selector.list_skills()
        assert len(skills) == 1

    def test_skill_selection_with_fallback(self):
        """测试技能选择（带后备）"""
        selector = SkillSelector()

        mock_fallback = MagicMock()
        selector.register_skill("direct_answer", mock_fallback)

        # 请求不存在的技能，应该返回后备
        skill = selector.select_skill("nonexistent_skill", fallback=True)
        assert skill == mock_fallback


class TestPlanner:
    """测试规划器"""

    @pytest.mark.asyncio
    async def test_planner_basic(self):
        """测试基本规划功能"""
        # 创建模拟 LLM
        mock_llm = AsyncMock()
        mock_llm.chat.return_value = """```json
{
    "goal": "回答用户问题",
    "reasoning": "这是一个简单问题",
    "steps": [
        {
            "step_id": 1,
            "description": "直接回答",
            "skill_name": "direct_answer",
            "tool_name": null,
            "tool_params": {},
            "depends_on": []
        }
    ]
}
```"""

        planner = Planner(llm=mock_llm)
        plan = await planner.plan("什么是 Python？")

        assert plan is not None
        assert len(plan.steps) == 1
        assert plan.steps[0].skill_name == "direct_answer"


class TestMessage:
    """测试消息结构"""

    def test_message_to_llm_format(self):
        """测试消息转换为 LLM 格式"""
        msg = Message(role=MessageRole.USER, content="测试消息")

        llm_format = msg.to_llm_format()
        assert llm_format["role"] == "user"
        assert llm_format["content"] == "测试消息"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
