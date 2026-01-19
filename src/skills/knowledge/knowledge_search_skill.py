"""
知识检索技能
基于 RAG 的知识库检索
"""
from typing import Dict, Any, Optional, List, TYPE_CHECKING

from ..base import BaseSkill
from src.core.logging import get_logger
from src.core.config import settings

if TYPE_CHECKING:
    from src.mcp.client import MCPClient
    from src.rag.retriever import RAGRetriever

logger = get_logger("skills.knowledge")


class KnowledgeSearchSkill(BaseSkill):
    """
    知识检索技能
    
    能力：
    - 语义检索：基于向量相似度搜索
    - 关键词匹配：精确匹配
    - 上下文构建：为 LLM 准备检索结果
    
    依赖的 MCP 工具：
    - rag_retriever: RAG 检索工具
    
    也可以直接使用 RAG 模块（不通过 MCP）
    """
    
    name = "knowledge_search"
    description = "从知识库中检索相关信息，支持语义搜索。适用于问答、信息查询场景。"
    required_tools = ["rag_retriever"]
    
    def __init__(self, retriever: "RAGRetriever" = None):
        """
        初始化技能
        
        Args:
            retriever: RAG 检索器实例（可选，也可通过 MCP 调用）
        """
        super().__init__()
        self._retriever = retriever
        self._top_k = settings.top_k
    
    def set_retriever(self, retriever: "RAGRetriever") -> None:
        """设置检索器"""
        self._retriever = retriever
    
    async def execute(
        self,
        description: str,
        tool_name: Optional[str] = None,
        tool_params: Dict[str, Any] = None,
        context: Dict[str, Any] = None,
        mcp_client: "MCPClient" = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        执行知识检索
        
        Args:
            description: 查询描述
            tool_params: 预解析的参数 (query, top_k, threshold)
            context: 上下文信息
            mcp_client: MCP 客户端
            
        Returns:
            检索结果
        """
        logger.info(f"Executing knowledge search: {description}")
        
        try:
            # 解析参数
            params = self._parse_params(description, tool_params)
            query = params.get("query") or description
            top_k = params.get("top_k", self._top_k)
            threshold = params.get("threshold", 0.7)
            
            # 方式1: 使用内置检索器
            if self._retriever:
                results = await self._search_with_retriever(
                    query, top_k, threshold
                )
            # 方式2: 通过 MCP 调用
            elif mcp_client:
                results = await self._search_via_mcp(
                    mcp_client, query, top_k, threshold
                )
            else:
                return {
                    "success": False,
                    "error": "未配置检索器或 MCP 客户端"
                }
            
            # 格式化结果
            formatted = self._format_results(query, results)
            
            logger.info(f"Knowledge search completed: {len(results)} results")
            return formatted
            
        except Exception as e:
            logger.error(f"Knowledge search failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _parse_params(
        self,
        description: str,
        tool_params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """解析查询参数"""
        params = tool_params.copy() if tool_params else {}
        
        # 如果没有 query，使用 description
        if not params.get("query"):
            params["query"] = description
        
        return params
    
    async def _search_with_retriever(
        self,
        query: str,
        top_k: int,
        threshold: float
    ) -> List[Dict[str, Any]]:
        """使用内置检索器搜索"""
        # 调用 RAG 检索器
        raw_results = await self._retriever.retrieve(
            query=query,
            top_k=top_k
        )
        
        # 过滤低分结果
        filtered = [
            r for r in raw_results
            if r.get("score", 0) >= threshold
        ]
        
        return filtered
    
    async def _search_via_mcp(
        self,
        mcp_client: "MCPClient",
        query: str,
        top_k: int,
        threshold: float
    ) -> List[Dict[str, Any]]:
        """通过 MCP 调用 RAG 工具"""
        result = await mcp_client.call_tool(
            "rag_retriever",
            {
                "query": query,
                "top_k": top_k,
                "threshold": threshold
            }
        )
        
        if isinstance(result, list):
            return result
        elif isinstance(result, dict):
            return result.get("results", [])
        return []
    
    def _format_results(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """格式化检索结果"""
        formatted_results = []
        context_parts = []
        
        for i, r in enumerate(results):
            content = r.get("content", r.get("text", ""))
            source = r.get("source", r.get("metadata", {}).get("source", "unknown"))
            score = r.get("score", 0)
            
            formatted_results.append({
                "content": content,
                "source": source,
                "score": round(score, 3),
                "metadata": r.get("metadata", {})
            })
            
            # 构建 LLM 上下文
            context_parts.append(f"[来源: {source}]\n{content}")
        
        # 拼接上下文
        context_for_llm = "\n\n---\n\n".join(context_parts)
        
        return {
            "success": True,
            "data": {
                "query": query,
                "results": formatted_results,
                "total": len(formatted_results),
                "context_for_llm": context_for_llm
            }
        }
    
    def build_rag_prompt(
        self,
        query: str,
        context: str,
        instruction: str = None
    ) -> str:
        """
        构建 RAG 增强的 Prompt
        
        Args:
            query: 用户查询
            context: 检索到的上下文
            instruction: 额外指令
            
        Returns:
            完整的 Prompt
        """
        default_instruction = "请根据以下参考资料回答问题。如果资料中没有相关信息，请说明。"
        
        prompt = f"""{instruction or default_instruction}

## 参考资料
{context}

## 问题
{query}

## 回答"""
        
        return prompt
