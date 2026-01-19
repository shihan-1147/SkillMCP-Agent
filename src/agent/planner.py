"""
任务规划器
负责将用户输入拆解为可执行的任务步骤
"""

import json
import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from src.core.exceptions import PlanningException
from src.core.logging import get_logger

from .schemas.task import StepStatus, TaskPlan, TaskStep

if TYPE_CHECKING:
    from src.llm.base import BaseLLM

logger = get_logger("agent.planner")


# 规划提示词模板
PLANNER_SYSTEM_PROMPT = """你是一个任务规划专家。你的职责是将用户的请求拆解为具体的执行步骤。

## 可用技能列表
{skills_description}

## 输出要求
请严格按照以下 JSON 格式输出任务规划：

```json
{{
    "goal": "任务目标的简要描述",
    "reasoning": "你的规划思路",
    "steps": [
        {{
            "step_id": 1,
            "description": "步骤描述",
            "skill_name": "使用的技能名称",
            "tool_name": "具体工具名称（可选）",
            "tool_params": {{}},
            "depends_on": []
        }}
    ]
}}
```

## 规划原则
1. 每个步骤必须使用已有的技能
2. 步骤之间的依赖关系要明确
3. 优先使用简单直接的方案
4. 如果任务不需要工具，可以只用一个直接回答的步骤
"""

PLANNER_USER_PROMPT = """## 对话上下文
{context}

## 用户请求
{user_query}

请为这个请求制定执行计划。"""


class Planner:
    """
    任务规划器

    职责：
    - 理解用户意图
    - 将复杂任务拆解为步骤
    - 为每个步骤选择合适的技能
    - 确定步骤间的依赖关系
    """

    def __init__(self, llm: "BaseLLM", available_skills: Dict[str, Any] = None):
        """
        初始化规划器

        Args:
            llm: LLM 实例
            available_skills: 可用技能字典 {skill_name: skill_description}
        """
        self.llm = llm
        self.available_skills = available_skills or {}
        logger.debug(f"Planner initialized with {len(self.available_skills)} skills")

    def update_skills(self, skills: Dict[str, Any]) -> None:
        """更新可用技能列表"""
        self.available_skills = skills
        logger.debug(f"Updated available skills: {list(skills.keys())}")

    def _build_skills_description(self) -> str:
        """构建技能描述文本"""
        if not self.available_skills:
            return "当前没有可用的专门技能，请使用 'direct_answer' 直接回答用户问题。"

        lines = []
        for name, info in self.available_skills.items():
            desc = (
                info.get("description", "无描述")
                if isinstance(info, dict)
                else str(info)
            )
            tools = info.get("tools", []) if isinstance(info, dict) else []
            tools_str = f" (工具: {', '.join(tools)})" if tools else ""
            lines.append(f"- **{name}**: {desc}{tools_str}")

        return "\n".join(lines)

    async def plan(
        self, user_query: str, context: str = "", max_steps: int = 5
    ) -> TaskPlan:
        """
        为用户请求生成执行计划

        Args:
            user_query: 用户查询
            context: 对话上下文
            max_steps: 最大步骤数

        Returns:
            TaskPlan 对象

        Raises:
            PlanningException: 规划失败时抛出
        """
        logger.info(f"Planning for query: {user_query[:50]}...")

        # 构建提示词
        system_prompt = PLANNER_SYSTEM_PROMPT.format(
            skills_description=self._build_skills_description()
        )
        user_prompt = PLANNER_USER_PROMPT.format(
            context=context or "（无历史上下文）", user_query=user_query
        )

        try:
            # 调用 LLM 获取规划
            response = await self.llm.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,  # 低温度以获得更稳定的规划
            )

            # 解析 JSON 响应
            plan_data = self._parse_plan_response(response)

            # 构建 TaskPlan 对象
            plan = self._build_task_plan(
                plan_data=plan_data, original_query=user_query, max_steps=max_steps
            )

            logger.info(f"Plan created with {len(plan.steps)} steps")
            logger.debug(f"Plan details: {plan.to_dict()}")

            return plan

        except Exception as e:
            logger.error(f"Planning failed: {str(e)}")
            raise PlanningException(
                message=f"任务规划失败: {str(e)}", details={"query": user_query}
            )

    def _parse_plan_response(self, response: str) -> Dict[str, Any]:
        """
        解析 LLM 的规划响应

        Args:
            response: LLM 响应文本

        Returns:
            解析后的规划字典
        """
        # 尝试提取 JSON 块
        json_str = response

        # 如果响应包含 markdown 代码块，提取其中的 JSON
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            json_str = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            json_str = response[start:end].strip()

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON: {e}, trying to extract manually")
            # 返回一个默认的直接回答计划
            return {
                "goal": "直接回答用户问题",
                "reasoning": "无法解析规划，使用直接回答",
                "steps": [
                    {
                        "step_id": 1,
                        "description": "直接回答用户的问题",
                        "skill_name": "direct_answer",
                        "tool_name": None,
                        "tool_params": {},
                        "depends_on": [],
                    }
                ],
            }

    def _build_task_plan(
        self, plan_data: Dict[str, Any], original_query: str, max_steps: int
    ) -> TaskPlan:
        """
        构建 TaskPlan 对象

        Args:
            plan_data: 规划数据字典
            original_query: 原始查询
            max_steps: 最大步骤数

        Returns:
            TaskPlan 对象
        """
        steps = []
        raw_steps = plan_data.get("steps", [])[:max_steps]

        for step_data in raw_steps:
            step = TaskStep(
                step_id=step_data.get("step_id", len(steps) + 1),
                description=step_data.get("description", ""),
                skill_name=step_data.get("skill_name", "direct_answer"),
                tool_name=step_data.get("tool_name"),
                tool_params=step_data.get("tool_params", {}),
                depends_on=step_data.get("depends_on", []),
                status=StepStatus.PENDING,
            )
            steps.append(step)

        return TaskPlan(
            plan_id=f"plan_{uuid.uuid4().hex[:8]}",
            original_query=original_query,
            goal=plan_data.get("goal", "完成用户请求"),
            steps=steps,
            reasoning=plan_data.get("reasoning", ""),
        )

    async def replan(
        self, original_plan: TaskPlan, failed_step: TaskStep, error_info: str
    ) -> TaskPlan:
        """
        重新规划（当步骤失败时）

        Args:
            original_plan: 原始计划
            failed_step: 失败的步骤
            error_info: 错误信息

        Returns:
            新的 TaskPlan
        """
        logger.info(f"Replanning after step {failed_step.step_id} failed")

        replan_query = f"""
原始任务: {original_plan.original_query}
失败步骤: {failed_step.description}
错误信息: {error_info}

请提供一个替代方案来完成这个任务。
"""
        return await self.plan(replan_query)
