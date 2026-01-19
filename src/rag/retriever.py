"""
检索器

从向量存储中检索相关文档
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.core.logging import get_logger

from .document import DocumentChunk, RetrievalResult
from .embedder import Embedder, get_embedder
from .store import FAISSStore, VectorStore

logger = get_logger("rag.retriever")


@dataclass
class RetrievalConfig:
    """检索配置"""

    top_k: int = 5
    score_threshold: float = 0.3
    rerank: bool = False
    expand_context: bool = False


class Retriever:
    """
    检索器

    从向量存储中检索与查询相关的文档块

    使用示例:
    ```python
    retriever = Retriever(store, embedder)

    results = await retriever.retrieve("什么是机器学习?")

    # 获取上下文字符串
    context = retriever.format_context(results)
    ```
    """

    def __init__(
        self,
        store: VectorStore,
        embedder: Embedder = None,
        config: RetrievalConfig = None,
    ):
        """
        初始化检索器

        Args:
            store: 向量存储
            embedder: 向量化器
            config: 检索配置
        """
        self.store = store
        self.embedder = embedder or get_embedder()
        self.config = config or RetrievalConfig()

    async def retrieve(
        self,
        query: str,
        top_k: int = None,
        score_threshold: float = None,
        filters: Dict[str, Any] = None,
    ) -> List[RetrievalResult]:
        """
        检索相关文档

        Args:
            query: 查询文本
            top_k: 返回数量
            score_threshold: 分数阈值
            filters: 过滤条件

        Returns:
            RetrievalResult 列表
        """
        top_k = top_k or self.config.top_k
        score_threshold = score_threshold or self.config.score_threshold

        logger.info(f"Retrieving for query: {query[:50]}...")

        # 向量化查询
        query_embedding = await self.embedder.embed_text(query)

        # 从向量存储搜索
        results = self.store.search(
            query_embedding, top_k=top_k * 2
        )  # 多取一些用于过滤

        # 过滤低分结果
        filtered_results = [r for r in results if r.score >= score_threshold]

        # 应用自定义过滤器
        if filters:
            filtered_results = self._apply_filters(filtered_results, filters)

        # 截取 top_k
        filtered_results = filtered_results[:top_k]

        # 更新排名
        for i, result in enumerate(filtered_results):
            result.rank = i

        logger.info(f"Retrieved {len(filtered_results)} results")
        return filtered_results

    async def retrieve_with_context(
        self, query: str, top_k: int = None, context_window: int = 1
    ) -> List[RetrievalResult]:
        """
        检索并扩展上下文

        获取匹配块的前后相邻块，提供更完整的上下文

        Args:
            query: 查询文本
            top_k: 返回数量
            context_window: 上下文窗口大小

        Returns:
            RetrievalResult 列表
        """
        results = await self.retrieve(query, top_k=top_k)

        if not context_window or context_window == 0:
            return results

        # TODO: 实现上下文扩展
        # 需要存储相邻块的关系

        return results

    def _apply_filters(
        self, results: List[RetrievalResult], filters: Dict[str, Any]
    ) -> List[RetrievalResult]:
        """应用过滤条件"""
        filtered = []

        for result in results:
            chunk = result.chunk
            match = True

            for key, value in filters.items():
                if key == "doc_id":
                    if chunk.doc_id != value:
                        match = False
                        break
                elif key == "source":
                    if chunk.metadata.get("source") != value:
                        match = False
                        break
                elif key in chunk.metadata:
                    if chunk.metadata[key] != value:
                        match = False
                        break

            if match:
                filtered.append(result)

        return filtered

    def format_context(
        self,
        results: List[RetrievalResult],
        max_length: int = 4000,
        include_metadata: bool = True,
    ) -> str:
        """
        格式化检索结果为上下文字符串

        用于注入到 Agent Prompt 中

        Args:
            results: 检索结果
            max_length: 最大长度
            include_metadata: 是否包含元数据

        Returns:
            格式化的上下文字符串
        """
        if not results:
            return ""

        context_parts = []
        current_length = 0

        for result in results:
            chunk = result.chunk

            if include_metadata:
                source = chunk.metadata.get("source", "unknown")
                title = chunk.metadata.get("title", "")
                header = f"[来源: {source}]" if not title else f"[{title}]"
                part = f"{header}\n{chunk.content}"
            else:
                part = chunk.content

            # 检查长度限制
            if current_length + len(part) > max_length:
                # 截断当前部分
                remaining = max_length - current_length - 50
                if remaining > 100:
                    part = part[:remaining] + "..."
                    context_parts.append(part)
                break

            context_parts.append(part)
            current_length += len(part) + 10  # 10 for separator

        return "\n\n---\n\n".join(context_parts)

    def format_for_prompt(
        self, results: List[RetrievalResult], prompt_template: str = None
    ) -> str:
        """
        格式化为完整的 RAG Prompt

        Args:
            results: 检索结果
            prompt_template: Prompt 模板

        Returns:
            完整的 Prompt 字符串
        """
        context = self.format_context(results)

        if not prompt_template:
            prompt_template = """基于以下参考资料回答问题。如果资料中没有相关信息，请说明。

## 参考资料

{context}

## 注意事项
- 优先使用参考资料中的信息
- 如果需要补充，请明确标注
- 引用来源时请标注出处"""

        return prompt_template.format(context=context)
