"""
推理引擎
负责结果整合和最终回答生成
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from src.core.logging import get_logger

if TYPE_CHECKING:
    from src.llm.base import BaseLLM

logger = get_logger("agent.reasoner")


# 结果整合提示词
SYNTHESIZE_PROMPT = """你是一个智能助手，需要根据任务执行结果生成最终回答。

## 原始问题
{original_query}

## 任务目标
{goal}

## 执行结果
{execution_results}

## 要求
1. 综合所有步骤的结果
2. 生成清晰、有条理的回答
3. 如果有步骤失败，说明原因并提供可能的解决方案
4. 回答应该直接解决用户的原始问题

请生成最终回答："""


class Reasoner:
    """
    推理引擎

    职责：
    - 分析执行结果
    - 整合多步骤输出
    - 生成最终回答
    - 处理异常情况
    """

    def __init__(self, llm: "BaseLLM"):
        """
        初始化推理引擎

        Args:
            llm: LLM 实例
        """
        self.llm = llm
        logger.debug("Reasoner initialized")

    async def synthesize(
        self, original_query: str, goal: str, execution_results: Dict[str, Any]
    ) -> str:
        """
        综合执行结果生成最终回答

        Args:
            original_query: 原始用户查询
            goal: 任务目标
            execution_results: 执行结果

        Returns:
            最终回答文本
        """
        logger.info("Synthesizing final answer from execution results")

        # 格式化执行结果
        results_text = self._format_results(execution_results)

        # 如果只有一个步骤且成功，可以直接返回结果
        if self._can_use_direct_result(execution_results):
            final_result = execution_results.get("final_result", {})
            result_content = final_result.get("result", "")
            if isinstance(result_content, str) and len(result_content) > 10:
                logger.debug("Using direct result without LLM synthesis")
                return result_content

        # 使用 LLM 综合结果
        prompt = SYNTHESIZE_PROMPT.format(
            original_query=original_query, goal=goal, execution_results=results_text
        )

        response = await self.llm.chat(
            messages=[{"role": "user", "content": prompt}], temperature=0.5
        )

        logger.debug("Final answer synthesized successfully")
        return response

    def _format_results(self, execution_results: Dict[str, Any]) -> str:
        """格式化执行结果为文本"""
        lines = []
        steps_results = execution_results.get("steps_results", [])

        for step_result in steps_results:
            step_id = step_result.get("step_id", "?")
            description = step_result.get("description", "")
            status = step_result.get("status", "unknown")

            lines.append(f"\n### 步骤 {step_id}: {description}")
            lines.append(f"状态: {status}")

            if status == "completed":
                result = step_result.get("result", "")
                # 截断过长的结果
                result_str = str(result)
                if len(result_str) > 1000:
                    result_str = result_str[:1000] + "...(已截断)"
                lines.append(f"结果: {result_str}")
            else:
                error = step_result.get("error", "未知错误")
                lines.append(f"错误: {error}")

        return "\n".join(lines)

    def _can_use_direct_result(self, execution_results: Dict[str, Any]) -> bool:
        """判断是否可以直接使用结果而无需 LLM 综合"""
        steps_results = execution_results.get("steps_results", [])

        # 只有一个步骤且成功
        if len(steps_results) == 1:
            return steps_results[0].get("status") == "completed"

        return False

    async def handle_error(
        self,
        original_query: str,
        error_info: str,
        partial_results: Dict[str, Any] = None,
    ) -> str:
        """
        处理执行错误，生成友好的错误响应

        Args:
            original_query: 原始查询
            error_info: 错误信息
            partial_results: 部分执行结果

        Returns:
            错误响应文本
        """
        logger.warning(f"Handling error: {error_info}")

        prompt = f"""用户的问题是：{original_query}

执行过程中遇到了问题：{error_info}

{f"已完成的部分结果：{partial_results}" if partial_results else ""}

请生成一个友好的响应，告知用户发生了什么问题，并提供可能的解决建议。"""

        response = await self.llm.chat(
            messages=[{"role": "user", "content": prompt}], temperature=0.5
        )

        return response

    async def decide_next_action(
        self, current_state: Dict[str, Any], available_actions: List[str]
    ) -> str:
        """
        决定下一步行动（用于复杂推理场景）

        Args:
            current_state: 当前状态
            available_actions: 可用行动列表

        Returns:
            选择的行动
        """
        prompt = f"""当前状态：
{current_state}

可选行动：
{', '.join(available_actions)}

请选择最合适的下一步行动，只返回行动名称。"""

        response = await self.llm.chat(
            messages=[{"role": "user", "content": prompt}], temperature=0.2
        )

        # 提取行动名称
        action = response.strip().lower()
        for available in available_actions:
            if available.lower() in action:
                return available

        # 默认返回第一个行动
        return available_actions[0] if available_actions else "stop"
