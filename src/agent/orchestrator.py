"""
Agent 编排器
核心控制模块，协调所有组件完成任务
"""
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from .planner import Planner
from .executor import Executor
from .reasoner import Reasoner
from .skill_selector import SkillSelector
from .memory.manager import MemoryManager
from .schemas.task import Task, TaskPlan
from .schemas.message import Message, MessageRole
from src.core.logging import get_logger
from src.core.config import settings
from src.core.exceptions import AgentException

logger = get_logger("agent.orchestrator")


# Agent 系统提示词
AGENT_SYSTEM_PROMPT = """你是 SkillMCP-Agent，一个强大的智能助手。

你具备以下能力：
{skills_description}

你的工作流程：
1. 理解用户意图
2. 制定执行计划
3. 调用合适的技能和工具
4. 整合结果并回答用户

请始终保持专业、准确、有帮助的态度。"""


class AgentOrchestrator:
    """
    Agent 编排器
    
    这是 Agent 的核心控制器，负责：
    - 协调 Planner、Executor、Reasoner 的工作流程
    - 管理对话记忆
    - 处理多轮对话
    - 输出结构化的执行过程
    
    核心思维循环：理解 → 规划 → 执行 → 推理 → 回答
    """
    
    def __init__(
        self,
        llm,
        mcp_client,
        memory_manager: MemoryManager = None
    ):
        """
        初始化 Agent 编排器
        
        Args:
            llm: LLM 实例
            mcp_client: MCP 客户端实例
            memory_manager: 记忆管理器实例
        """
        self.llm = llm
        self.mcp_client = mcp_client
        
        # 初始化各组件
        self.memory = memory_manager or MemoryManager()
        self.skill_selector = SkillSelector()
        self.planner = Planner(llm=llm)
        self.executor = Executor(
            skill_selector=self.skill_selector,
            mcp_client=mcp_client
        )
        self.reasoner = Reasoner(llm=llm)
        
        # 状态追踪
        self._current_task: Optional[Task] = None
        self._iteration_count = 0
        self._max_iterations = settings.max_iterations
        
        logger.info("AgentOrchestrator initialized")
    
    def register_skill(self, name: str, skill, metadata: Dict[str, Any] = None) -> None:
        """
        注册技能
        
        Args:
            name: 技能名称
            skill: 技能实例
            metadata: 技能元数据
        """
        self.skill_selector.register_skill(name, skill, metadata)
        # 更新 Planner 的技能列表
        self.planner.update_skills(self.skill_selector.get_skills_for_planner())
        logger.info(f"Skill registered: {name}")
    
    def _update_system_prompt(self) -> None:
        """更新系统提示词"""
        skills_list = self.skill_selector.list_skills()
        skills_desc = "\n".join([
            f"- {s['name']}: {s['description']}"
            for s in skills_list
        ]) or "- 直接对话：回答用户问题"
        
        system_prompt = AGENT_SYSTEM_PROMPT.format(
            skills_description=skills_desc
        )
        self.memory.set_system_prompt(system_prompt)
    
    async def chat(
        self,
        user_input: str,
        session_id: str = None
    ) -> Dict[str, Any]:
        """
        处理用户输入的主入口
        
        这是 Agent 的核心方法，实现了完整的思维循环：
        1. 理解：分析用户意图
        2. 规划：制定执行计划
        3. 执行：调用技能和工具
        4. 推理：整合结果
        5. 回答：生成最终响应
        
        Args:
            user_input: 用户输入
            session_id: 会话ID（用于多轮对话）
            
        Returns:
            包含回答和执行详情的字典
        """
        logger.info(f"Processing user input: {user_input[:50]}...")
        
        # 更新系统提示词
        self._update_system_prompt()
        
        # 创建任务
        task = self._create_task(user_input, session_id)
        self._current_task = task
        
        # 添加用户消息到记忆
        self.memory.add_user_input(user_input)
        
        try:
            # ===== 阶段1: 规划 =====
            logger.info("Phase 1: Planning")
            context = self.memory.get_enhanced_context(user_input)
            
            plan = await self.planner.plan(
                user_query=user_input,
                context=context.get("conversation_history", "")
            )
            task.plan = plan
            task.status = "planning_completed"
            
            # ===== 阶段2: 执行 =====
            logger.info("Phase 2: Executing")
            task.status = "executing"
            
            execution_results = await self.executor.execute_plan(
                plan=plan,
                context=context
            )
            
            task.status = "execution_completed"
            
            # ===== 阶段3: 推理与整合 =====
            logger.info("Phase 3: Reasoning")
            
            if execution_results.get("completed"):
                final_answer = await self.reasoner.synthesize(
                    original_query=user_input,
                    goal=plan.goal,
                    execution_results=execution_results
                )
            else:
                # 执行未完成，处理错误
                final_answer = await self.reasoner.handle_error(
                    original_query=user_input,
                    error_info="任务执行未能完成",
                    partial_results=execution_results
                )
            
            # 更新任务状态
            task.final_answer = final_answer
            task.status = "completed"
            task.completed_at = datetime.now()
            
            # 添加助手回复到记忆
            self.memory.add_agent_response(final_answer)
            
            # 保存到长期记忆
            self.memory.save_task_result(
                task_id=task.task_id,
                query=user_input,
                result=final_answer[:500]
            )
            
            # 构建响应
            response = self._build_response(task, plan, execution_results, final_answer)
            
            logger.info(f"Task {task.task_id} completed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Task failed: {str(e)}")
            task.status = "failed"
            
            # 尝试生成错误响应
            error_answer = f"抱歉，处理您的请求时遇到了问题：{str(e)}"
            self.memory.add_agent_response(error_answer)
            
            return {
                "success": False,
                "answer": error_answer,
                "error": str(e),
                "task_id": task.task_id
            }
    
    def _create_task(self, user_input: str, session_id: str = None) -> Task:
        """创建任务对象"""
        return Task(
            task_id=f"task_{uuid.uuid4().hex[:8]}",
            user_query=user_input,
            metadata={"session_id": session_id}
        )
    
    def _build_response(
        self,
        task: Task,
        plan: TaskPlan,
        execution_results: Dict[str, Any],
        final_answer: str
    ) -> Dict[str, Any]:
        """构建标准响应格式"""
        return {
            "success": True,
            "answer": final_answer,
            "task_id": task.task_id,
            "plan": {
                "plan_id": plan.plan_id,
                "goal": plan.goal,
                "reasoning": plan.reasoning,
                "steps": [
                    {
                        "step_id": s.step_id,
                        "description": s.description,
                        "skill": s.skill_name,
                        "tool": s.tool_name,
                        "status": s.status
                    }
                    for s in plan.steps
                ]
            },
            "execution": {
                "completed": execution_results.get("completed", False),
                "steps_count": len(execution_results.get("steps_results", []))
            },
            "metadata": {
                "created_at": task.created_at.isoformat(),
                "completed_at": task.completed_at.isoformat() if task.completed_at else None
            }
        }
    
    async def handle_followup(self, user_input: str) -> Dict[str, Any]:
        """
        处理追问（多轮对话）
        
        Args:
            user_input: 用户追问内容
            
        Returns:
            响应字典
        """
        # 追问直接复用 chat 方法，记忆会自动保留上下文
        return await self.chat(user_input)
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """获取对话历史"""
        messages = self.memory.short_term.get_messages(include_system=False)
        return [
            {"role": m.role.value, "content": m.content}
            for m in messages
        ]
    
    def clear_conversation(self) -> None:
        """清空当前对话"""
        self.memory.clear_conversation()
        self._current_task = None
        self._iteration_count = 0
        logger.info("Conversation cleared")
    
    def get_current_task(self) -> Optional[Task]:
        """获取当前任务"""
        return self._current_task
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计"""
        return self.memory.get_memory_stats()
    
    def list_skills(self) -> List[Dict[str, Any]]:
        """列出所有可用技能"""
        return self.skill_selector.list_skills()
