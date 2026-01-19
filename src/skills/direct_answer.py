"""
直接回答技能
用于不需要工具调用的简单问答场景
"""
from typing import Dict, Any, Optional, TYPE_CHECKING

from .base import BaseSkill
from src.core.logging import get_logger

if TYPE_CHECKING:
    from src.mcp.client import MCPClient
    from src.llm.base import BaseLLM

logger = get_logger("skills.direct_answer")


class DirectAnswerSkill(BaseSkill):
    """
    直接回答技能
    
    用于直接回答用户问题，不需要调用任何外部工具
    这是 Agent 的默认后备技能
    """
    
    name = "direct_answer"
    description = "直接回答用户问题，不调用外部工具。适用于常识性问题、解释说明、建议等。"
    required_tools = []
    
    def __init__(self, llm: "BaseLLM" = None):
        """
        初始化技能
        
        Args:
            llm: LLM 实例
        """
        super().__init__()
        self.llm = llm
    
    async def execute(
        self,
        description: str,
        tool_name: Optional[str] = None,
        tool_params: Dict[str, Any] = None,
        context: Dict[str, Any] = None,
        mcp_client: "MCPClient" = None,
        **kwargs
    ) -> str:
        """
        执行直接回答
        
        Args:
            description: 步骤描述/问题
            context: 上下文信息
            **kwargs: 其他参数
            
        Returns:
            回答文本
        """
        logger.info(f"Executing direct answer for: {description[:50]}...")
        context = context or {}
        
        # 构建提示词
        prompt = self._build_prompt(description, context)
        
        if self.llm:
            response = await self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return response
        else:
            # 无 LLM 时的后备响应
            return f"收到您的问题：{description}。由于系统限制，暂时无法生成完整回答。"
    
    def _build_prompt(self, description: str, context: Dict[str, Any]) -> str:
        """构建回答提示词"""
        parts = []
        
        # 添加上下文
        if context.get("original_query"):
            parts.append(f"用户原始问题：{context['original_query']}")
        
        if context.get("previous_results"):
            parts.append(f"之前步骤的结果：{context['previous_results']}")
        
        parts.append(f"当前需要回答：{description}")
        parts.append("\n请提供清晰、有帮助的回答。")
        
        return "\n\n".join(parts)
