"""
RAG 检索工具
MCP 标准工具实现

与 RAG Pipeline 集成，提供真正的向量检索能力
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.core.logging import get_logger

from ..protocol.types import ParameterType, Tool, ToolParameter
from .base import BaseTool

logger = get_logger("mcp.tools.rag_retriever")


class RAGRetrieverTool(BaseTool):
    """
    RAG 检索工具

    从知识库中检索相关文档

    与 src.rag.RAGPipeline 集成，支持：
    - 真实向量检索（当 RAG Pipeline 已初始化时）
    - Mock 检索（用于演示和测试）

    MCP Tool Schema:
    {
        "name": "rag_retriever",
        "description": "从知识库检索相关文档",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "检索查询"},
                "top_k": {"type": "integer", "default": 5},
                "collection": {"type": "string", "default": "default"},
                "filters": {"type": "object"}
            },
            "required": ["query"]
        }
    }
    """

    name = "rag_retriever"
    description = "从知识库中检索与查询相关的文档片段"
    category = "knowledge"
    version = "1.0.0"

    def __init__(self):
        super().__init__()
        self._rag_pipeline = None

    # Mock 知识库数据
    MOCK_DOCUMENTS = [
        {
            "id": "doc_001",
            "title": "Python 编程入门",
            "content": "Python 是一种高级编程语言，以其简洁清晰的语法著称。它支持多种编程范式，包括面向对象、函数式和过程式编程。Python 广泛应用于 Web 开发、数据科学、人工智能等领域。",
            "source": "programming_guide.md",
            "tags": ["python", "programming", "beginner"],
        },
        {
            "id": "doc_002",
            "title": "机器学习基础",
            "content": "机器学习是人工智能的一个分支，它使计算机能够从数据中学习而不需要明确编程。常见的机器学习算法包括线性回归、决策树、随机森林和神经网络。",
            "source": "ml_basics.md",
            "tags": ["machine-learning", "ai", "algorithm"],
        },
        {
            "id": "doc_003",
            "title": "FastAPI 框架介绍",
            "content": "FastAPI 是一个现代、快速的 Python Web 框架，用于构建 API。它基于 Python 3.6+ 类型提示，提供自动 API 文档生成、高性能和简单易用的特点。",
            "source": "fastapi_guide.md",
            "tags": ["fastapi", "python", "web", "api"],
        },
        {
            "id": "doc_004",
            "title": "向量数据库概述",
            "content": "向量数据库专门用于存储和检索向量嵌入。常见的向量数据库包括 FAISS、Milvus、Pinecone 和 Weaviate。它们在语义搜索和推荐系统中发挥重要作用。",
            "source": "vector_db.md",
            "tags": ["vector-database", "embedding", "search"],
        },
        {
            "id": "doc_005",
            "title": "大语言模型应用",
            "content": "大语言模型（LLM）如 GPT、Claude 等正在改变人工智能应用的方式。通过提示工程和微调，LLM 可以执行各种自然语言处理任务，包括文本生成、问答和代码补全。",
            "source": "llm_applications.md",
            "tags": ["llm", "ai", "nlp", "gpt"],
        },
        {
            "id": "doc_006",
            "title": "AI Agent 架构设计",
            "content": "AI Agent 是能够自主执行任务的智能系统。一个完整的 Agent 架构通常包括规划器、执行器、记忆系统和工具调用能力。Agent 可以分解复杂任务并逐步完成。",
            "source": "agent_design.md",
            "tags": ["agent", "ai", "architecture"],
        },
        {
            "id": "doc_007",
            "title": "RAG 技术详解",
            "content": "检索增强生成（RAG）是一种结合检索和生成的 AI 技术。它首先从知识库检索相关文档，然后将检索结果作为上下文提供给语言模型，从而生成更准确和具有事实依据的回答。",
            "source": "rag_explained.md",
            "tags": ["rag", "retrieval", "generation", "ai"],
        },
        {
            "id": "doc_008",
            "title": "MCP 协议规范",
            "content": "Model Context Protocol (MCP) 是一种标准化的工具调用协议。它定义了工具的输入输出格式、错误处理和元数据结构，使 AI 系统能够以统一的方式调用外部工具和服务。",
            "source": "mcp_spec.md",
            "tags": ["mcp", "protocol", "tool-calling"],
        },
    ]

    def get_parameters(self) -> List[ToolParameter]:
        """定义工具参数"""
        return [
            ToolParameter(
                name="query",
                type=ParameterType.STRING,
                description="检索查询文本",
                required=True,
            ),
            ToolParameter(
                name="top_k",
                type=ParameterType.INTEGER,
                description="返回结果数量",
                required=False,
                default=5,
            ),
            ToolParameter(
                name="collection",
                type=ParameterType.STRING,
                description="知识库集合名称",
                required=False,
                default="default",
            ),
            ToolParameter(
                name="filters",
                type=ParameterType.OBJECT,
                description="过滤条件",
                required=False,
            ),
        ]

    def set_rag_pipeline(self, pipeline) -> None:
        """
        设置 RAG Pipeline

        Args:
            pipeline: RAGPipeline 实例
        """
        self._rag_pipeline = pipeline
        logger.info("RAG Pipeline connected to RAGRetrieverTool")

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行检索

        优先使用真实的 RAG Pipeline，如果未配置则使用 Mock

        Args:
            query: 检索查询
            top_k: 返回数量
            collection: 集合名称
            filters: 过滤条件

        Returns:
            检索结果
        """
        query = kwargs.get("query")
        top_k = kwargs.get("top_k", 5)
        collection = kwargs.get("collection", "default")
        filters = kwargs.get("filters", {})

        if not query:
            return {"success": False, "error": "请提供检索查询"}

        logger.info(f"RAG retrieval: query='{query}', top_k={top_k}")

        # 尝试使用真实的 RAG Pipeline
        if self._rag_pipeline is not None:
            try:
                results = await self._retrieve_from_pipeline(query, top_k, filters)
                return {
                    "success": True,
                    "data": {
                        "query": query,
                        "collection": collection,
                        "total": len(results),
                        "documents": results,
                        "retrieval_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "source": "rag_pipeline",
                    },
                }
            except Exception as e:
                logger.warning(
                    f"RAG Pipeline retrieval failed, falling back to mock: {e}"
                )

        # 回退到 Mock 检索
        results = self._mock_retrieve(query, top_k, filters)

        return {
            "success": True,
            "data": {
                "query": query,
                "collection": collection,
                "total": len(results),
                "documents": results,
                "retrieval_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": "mock",
            },
        }

    async def _retrieve_from_pipeline(
        self, query: str, top_k: int, filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        从 RAG Pipeline 检索
        """
        results = await self._rag_pipeline.retrieve(query, top_k=top_k, filters=filters)

        return [
            {
                "id": r.chunk.id,
                "title": r.chunk.metadata.get("title", ""),
                "content": r.chunk.content,
                "source": r.chunk.metadata.get("source", ""),
                "score": round(r.score, 4),
                "metadata": r.chunk.metadata,
            }
            for r in results
        ]

    def _mock_retrieve(
        self, query: str, top_k: int, filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Mock 检索实现

        使用简单的关键词匹配模拟向量相似度检索
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())

        scored_docs = []

        for doc in self.MOCK_DOCUMENTS:
            # 计算相似度分数
            score = self._calculate_score(query_lower, query_words, doc)

            # 应用过滤器
            if filters:
                if not self._apply_filters(doc, filters):
                    continue

            if score > 0:
                scored_docs.append(
                    {
                        "id": doc["id"],
                        "title": doc["title"],
                        "content": doc["content"],
                        "source": doc["source"],
                        "score": round(score, 4),
                        "metadata": {"tags": doc["tags"]},
                    }
                )

        # 按分数排序
        scored_docs.sort(key=lambda x: x["score"], reverse=True)

        return scored_docs[:top_k]

    def _calculate_score(
        self, query_lower: str, query_words: set, doc: Dict[str, Any]
    ) -> float:
        """计算文档相似度分数"""
        score = 0.0

        # 标题匹配
        title_lower = doc["title"].lower()
        for word in query_words:
            if word in title_lower:
                score += 0.3

        # 内容匹配
        content_lower = doc["content"].lower()
        for word in query_words:
            if word in content_lower:
                score += 0.2

        # 标签匹配
        for tag in doc["tags"]:
            if tag in query_lower or any(word in tag for word in query_words):
                score += 0.25

        # 完整短语匹配加分
        if len(query_lower) >= 3 and query_lower in content_lower:
            score += 0.5

        return min(score, 1.0)  # 最高分 1.0

    def _apply_filters(self, doc: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """应用过滤条件"""
        for key, value in filters.items():
            if key == "tags":
                if isinstance(value, list):
                    if not any(tag in doc["tags"] for tag in value):
                        return False
                elif value not in doc["tags"]:
                    return False
            elif key == "source":
                if doc["source"] != value:
                    return False
        return True
