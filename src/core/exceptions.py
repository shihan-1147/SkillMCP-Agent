"""
自定义异常定义
"""


class SkillMCPException(Exception):
    """基础异常类"""
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class AgentException(SkillMCPException):
    """Agent 相关异常"""
    pass


class PlanningException(AgentException):
    """规划阶段异常"""
    pass


class ExecutionException(AgentException):
    """执行阶段异常"""
    pass


class ToolCallException(SkillMCPException):
    """工具调用异常"""
    pass


class MCPException(SkillMCPException):
    """MCP 协议异常"""
    pass


class RAGException(SkillMCPException):
    """RAG 相关异常"""
    pass


class SkillNotFoundException(SkillMCPException):
    """技能未找到异常"""
    pass


class LLMException(SkillMCPException):
    """LLM 调用异常"""
    pass
