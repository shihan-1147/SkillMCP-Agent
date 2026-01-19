"""
任务与规划的数据结构定义
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class StepStatus(str, Enum):
    """步骤执行状态"""

    PENDING = "pending"  # 待执行
    RUNNING = "running"  # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    SKIPPED = "skipped"  # 跳过


class TaskStep(BaseModel):
    """
    任务步骤
    表示规划后的单个执行步骤
    """

    step_id: int = Field(..., description="步骤序号")
    description: str = Field(..., description="步骤描述")
    skill_name: str = Field(..., description="需要使用的技能名称")
    tool_name: Optional[str] = Field(None, description="需要调用的工具名称")
    tool_params: Dict[str, Any] = Field(default_factory=dict, description="工具参数")
    depends_on: List[int] = Field(default_factory=list, description="依赖的步骤ID列表")
    status: StepStatus = Field(default=StepStatus.PENDING, description="执行状态")
    result: Optional[Any] = Field(None, description="执行结果")
    error: Optional[str] = Field(None, description="错误信息")

    class Config:
        use_enum_values = True


class TaskPlan(BaseModel):
    """
    任务规划
    包含多个有序步骤的执行计划
    """

    plan_id: str = Field(..., description="规划ID")
    original_query: str = Field(..., description="原始用户查询")
    goal: str = Field(..., description="任务目标总结")
    steps: List[TaskStep] = Field(default_factory=list, description="执行步骤列表")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    reasoning: str = Field(default="", description="规划推理过程")

    def get_next_step(self) -> Optional[TaskStep]:
        """获取下一个待执行的步骤"""
        for step in self.steps:
            if step.status == StepStatus.PENDING:
                # 检查依赖是否完成
                deps_completed = all(
                    self.steps[dep_id - 1].status == StepStatus.COMPLETED
                    for dep_id in step.depends_on
                    if dep_id <= len(self.steps)
                )
                if deps_completed:
                    return step
        return None

    def is_completed(self) -> bool:
        """检查计划是否全部完成"""
        return all(
            step.status in (StepStatus.COMPLETED, StepStatus.SKIPPED)
            for step in self.steps
        )

    def has_failed(self) -> bool:
        """检查是否有失败的步骤"""
        return any(step.status == StepStatus.FAILED for step in self.steps)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "plan_id": self.plan_id,
            "goal": self.goal,
            "original_query": self.original_query,
            "reasoning": self.reasoning,
            "steps": [
                {
                    "step_id": s.step_id,
                    "description": s.description,
                    "skill_name": s.skill_name,
                    "tool_name": s.tool_name,
                    "status": s.status,
                    "result": str(s.result)[:200] if s.result else None,
                }
                for s in self.steps
            ],
        }


class Task(BaseModel):
    """
    任务对象
    表示一个完整的用户任务
    """

    task_id: str = Field(..., description="任务ID")
    user_query: str = Field(..., description="用户原始输入")
    plan: Optional[TaskPlan] = Field(None, description="任务规划")
    final_answer: Optional[str] = Field(None, description="最终回答")
    status: str = Field(default="created", description="任务状态")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
