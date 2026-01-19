"""
执行器模块
负责执行任务步骤，调用技能和工具
"""
from typing import Dict, Any, Optional, TYPE_CHECKING
import asyncio

from .schemas.task import TaskStep, TaskPlan, StepStatus
from .skill_selector import SkillSelector
from src.core.logging import get_logger
from src.core.exceptions import ExecutionException

if TYPE_CHECKING:
    from src.mcp.client import MCPClient
    from src.skills.base import BaseSkill

logger = get_logger("agent.executor")


class Executor:
    """
    任务执行器
    
    职责：
    - 按照规划执行每个步骤
    - 通过 SkillSelector 选择技能
    - 通过 MCP Client 调用工具
    - 收集和整合执行结果
    """
    
    def __init__(
        self,
        skill_selector: SkillSelector,
        mcp_client: "MCPClient"
    ):
        """
        初始化执行器
        
        Args:
            skill_selector: 技能选择器
            mcp_client: MCP 客户端
        """
        self.skill_selector = skill_selector
        self.mcp_client = mcp_client
        self._execution_context: Dict[str, Any] = {}
        logger.debug("Executor initialized")
    
    async def execute_plan(
        self,
        plan: TaskPlan,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        执行完整的任务规划
        
        Args:
            plan: 任务规划
            context: 执行上下文（包含对话历史等）
            
        Returns:
            执行结果字典
        """
        logger.info(f"Executing plan: {plan.plan_id} with {len(plan.steps)} steps")
        
        self._execution_context = context or {}
        results = []
        
        while not plan.is_completed() and not plan.has_failed():
            next_step = plan.get_next_step()
            if not next_step:
                logger.warning("No executable step found, breaking loop")
                break
            
            try:
                result = await self.execute_step(next_step, plan)
                results.append({
                    "step_id": next_step.step_id,
                    "description": next_step.description,
                    "result": result,
                    "status": "completed"
                })
            except Exception as e:
                logger.error(f"Step {next_step.step_id} failed: {str(e)}")
                results.append({
                    "step_id": next_step.step_id,
                    "description": next_step.description,
                    "error": str(e),
                    "status": "failed"
                })
                # 失败后不再继续执行后续步骤
                break
        
        return {
            "plan_id": plan.plan_id,
            "goal": plan.goal,
            "completed": plan.is_completed(),
            "steps_results": results,
            "final_result": results[-1] if results else None
        }
    
    async def execute_step(
        self,
        step: TaskStep,
        plan: TaskPlan
    ) -> Any:
        """
        执行单个步骤
        
        Args:
            step: 任务步骤
            plan: 所属的任务规划
            
        Returns:
            步骤执行结果
        """
        logger.info(f"Executing step {step.step_id}: {step.description}")
        step.status = StepStatus.RUNNING
        
        try:
            # 获取前置步骤的结果作为上下文
            step_context = self._get_step_context(step, plan)
            
            # 选择技能
            skill = self.skill_selector.select_skill(step.skill_name)
            
            # 执行技能
            result = await self._execute_skill(
                skill=skill,
                step=step,
                context=step_context
            )
            
            # 更新步骤状态
            step.status = StepStatus.COMPLETED
            step.result = result
            
            logger.info(f"Step {step.step_id} completed successfully")
            return result
            
        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = str(e)
            logger.error(f"Step {step.step_id} failed: {str(e)}")
            raise ExecutionException(
                message=f"步骤 {step.step_id} 执行失败: {str(e)}",
                details={"step": step.dict()}
            )
    
    async def _execute_skill(
        self,
        skill: "BaseSkill",
        step: TaskStep,
        context: Dict[str, Any]
    ) -> Any:
        """
        执行技能
        
        Args:
            skill: 技能实例
            step: 任务步骤
            context: 执行上下文
            
        Returns:
            技能执行结果
        """
        # 准备技能执行参数
        execution_params = {
            "description": step.description,
            "tool_name": step.tool_name,
            "tool_params": step.tool_params,
            "context": context,
            "mcp_client": self.mcp_client
        }
        
        # 调用技能的 execute 方法
        result = await skill.execute(**execution_params)
        
        return result
    
    def _get_step_context(
        self,
        step: TaskStep,
        plan: TaskPlan
    ) -> Dict[str, Any]:
        """
        获取步骤执行上下文
        
        Args:
            step: 当前步骤
            plan: 任务规划
            
        Returns:
            上下文字典
        """
        context = {
            "original_query": plan.original_query,
            "goal": plan.goal,
            "current_step_id": step.step_id,
            "total_steps": len(plan.steps),
            "previous_results": {}
        }
        
        # 添加依赖步骤的结果
        for dep_id in step.depends_on:
            if dep_id <= len(plan.steps):
                dep_step = plan.steps[dep_id - 1]
                if dep_step.status == StepStatus.COMPLETED:
                    context["previous_results"][dep_id] = dep_step.result
        
        # 合并全局执行上下文
        context.update(self._execution_context)
        
        return context
    
    async def call_tool(
        self,
        tool_name: str,
        params: Dict[str, Any]
    ) -> Any:
        """
        直接调用 MCP 工具
        
        Args:
            tool_name: 工具名称
            params: 工具参数
            
        Returns:
            工具执行结果
        """
        logger.debug(f"Calling tool: {tool_name} with params: {params}")
        return await self.mcp_client.call_tool(tool_name, params)
    
    def reset_context(self) -> None:
        """重置执行上下文"""
        self._execution_context = {}
        logger.debug("Execution context reset")
