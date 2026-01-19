"""
RAG 管道

整合文档加载、切分、向量化、存储和检索的完整流程
"""
from typing import List, Optional, Dict, Any, Union
from pathlib import Path

from .document import Document, DocumentChunk, RetrievalResult
from .loader import DocumentLoader
from .chunker import TextChunker, ChunkStrategy
from .embedder import Embedder, get_embedder
from .store import VectorStore, FAISSStore
from .retriever import Retriever, RetrievalConfig
from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger("rag.pipeline")


class RAGPipeline:
    """
    RAG 管道
    
    提供完整的 RAG 工作流：
    1. 加载文档 (load_documents)
    2. 切分文本 (chunk)
    3. 向量化 (embed)
    4. 存储索引 (index)
    5. 检索 (retrieve)
    
    使用示例:
    ```python
    # 初始化
    rag = RAGPipeline()
    
    # 加载并索引文档
    await rag.load_documents("./docs")
    
    # 检索
    results = await rag.retrieve("什么是 AI Agent?")
    
    # 获取上下文
    context = rag.get_context_for_prompt(results)
    
    # 保存/加载索引
    rag.save("./index")
    rag.load("./index")
    ```
    """
    
    def __init__(
        self,
        embedder: Embedder = None,
        store: VectorStore = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        chunk_strategy: ChunkStrategy = ChunkStrategy.FIXED_SIZE
    ):
        """
        初始化 RAG 管道
        
        Args:
            embedder: 向量化器
            store: 向量存储
            chunk_size: 块大小
            chunk_overlap: 块重叠
            chunk_strategy: 分块策略
        """
        settings = get_settings()
        
        # 初始化组件
        self.embedder = embedder or get_embedder()
        self.loader = DocumentLoader()
        self.chunker = TextChunker(
            chunk_size=chunk_size,
            overlap=chunk_overlap,
            strategy=chunk_strategy
        )
        
        # 向量存储
        if store:
            self.store = store
        else:
            self.store = FAISSStore(dimension=self.embedder.dimension)
        
        # 检索器
        self.retriever = Retriever(
            store=self.store,
            embedder=self.embedder,
            config=RetrievalConfig(
                top_k=settings.rag_top_k,
                score_threshold=0.3
            )
        )
        
        # 文档追踪
        self._documents: Dict[str, Document] = {}
        self._initialized = False
    
    async def load_documents(
        self,
        source: Union[str, Path, List[str]],
        recursive: bool = True
    ) -> int:
        """
        加载并索引文档
        
        Args:
            source: 文档路径（文件/目录/路径列表）
            recursive: 是否递归加载子目录
            
        Returns:
            加载的文档数量
        """
        documents = []
        
        if isinstance(source, (str, Path)):
            path = Path(source)
            if path.is_file():
                doc = self.loader.load_file(path)
                if doc:
                    documents.append(doc)
            elif path.is_dir():
                documents = self.loader.load_directory(path, recursive=recursive)
        elif isinstance(source, list):
            for src in source:
                path = Path(src)
                if path.is_file():
                    doc = self.loader.load_file(path)
                    if doc:
                        documents.append(doc)
                elif path.is_dir():
                    documents.extend(self.loader.load_directory(path, recursive=recursive))
        
        if not documents:
            logger.warning(f"No documents loaded from {source}")
            return 0
        
        # 索引文档
        await self.index_documents(documents)
        
        return len(documents)
    
    async def index_documents(self, documents: List[Document]) -> int:
        """
        索引文档列表
        
        Args:
            documents: 文档列表
            
        Returns:
            索引的块数量
        """
        logger.info(f"Indexing {len(documents)} documents...")
        
        # 切分文档
        all_chunks = []
        for doc in documents:
            chunks = self.chunker.chunk_document(doc)
            all_chunks.extend(chunks)
            self._documents[doc.id] = doc
        
        logger.info(f"Created {len(all_chunks)} chunks")
        
        # 向量化
        logger.info("Embedding chunks...")
        embedded_chunks = await self.embedder.embed_chunks(all_chunks)
        
        # 存储
        self.store.add(embedded_chunks)
        
        self._initialized = True
        logger.info(f"Indexed {len(embedded_chunks)} chunks")
        
        return len(embedded_chunks)
    
    async def add_document(
        self,
        content: str,
        source: str = "inline",
        title: str = "Untitled",
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        添加单个文档
        
        Args:
            content: 文档内容
            source: 来源标识
            title: 标题
            metadata: 元数据
            
        Returns:
            文档 ID
        """
        doc = self.loader.load_text(content, source=source, title=title)
        if metadata:
            doc.metadata.update(metadata)
        
        await self.index_documents([doc])
        return doc.id
    
    async def retrieve(
        self,
        query: str,
        top_k: int = None,
        filters: Dict[str, Any] = None
    ) -> List[RetrievalResult]:
        """
        检索相关文档
        
        Args:
            query: 查询文本
            top_k: 返回数量
            filters: 过滤条件
            
        Returns:
            RetrievalResult 列表
        """
        if not self._initialized:
            logger.warning("RAG pipeline not initialized, no documents indexed")
            return []
        
        return await self.retriever.retrieve(query, top_k=top_k, filters=filters)
    
    def get_context_for_prompt(
        self,
        results: List[RetrievalResult],
        max_length: int = 4000
    ) -> str:
        """
        获取用于 Prompt 的上下文
        
        Args:
            results: 检索结果
            max_length: 最大长度
            
        Returns:
            上下文字符串
        """
        return self.retriever.format_context(results, max_length=max_length)
    
    def build_augmented_prompt(
        self,
        query: str,
        results: List[RetrievalResult],
        system_prompt: str = None
    ) -> str:
        """
        构建增强 Prompt
        
        将检索结果注入到 Prompt 中
        
        Args:
            query: 用户查询
            results: 检索结果
            system_prompt: 系统提示
            
        Returns:
            增强后的 Prompt
        """
        context = self.get_context_for_prompt(results)
        
        if not context:
            return query
        
        augmented = f"""请基于以下参考资料回答问题。

## 参考资料

{context}

## 用户问题

{query}

## 回答要求
1. 优先使用参考资料中的信息
2. 如果参考资料不足以回答，可以结合自身知识补充，但需说明
3. 引用资料时请标注来源"""
        
        return augmented
    
    def delete_document(self, doc_id: str) -> bool:
        """
        删除文档
        
        Args:
            doc_id: 文档 ID
            
        Returns:
            是否成功
        """
        if doc_id not in self._documents:
            return False
        
        self.store.delete(doc_id)
        del self._documents[doc_id]
        
        logger.info(f"Deleted document: {doc_id}")
        return True
    
    def save(self, path: str) -> None:
        """
        保存索引到磁盘
        
        Args:
            path: 保存路径
        """
        self.store.save(path)
        
        # 保存文档信息
        import json
        docs_info = {
            doc_id: {
                "id": doc.id,
                "title": doc.title,
                "source": doc.source,
                "doc_type": doc.doc_type,
            }
            for doc_id, doc in self._documents.items()
        }
        
        with open(Path(path) / "documents.json", "w", encoding="utf-8") as f:
            json.dump(docs_info, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved RAG pipeline to {path}")
    
    def load(self, path: str) -> None:
        """
        从磁盘加载索引
        
        Args:
            path: 加载路径
        """
        self.store.load(path)
        
        # 加载文档信息
        import json
        docs_path = Path(path) / "documents.json"
        if docs_path.exists():
            with open(docs_path, "r", encoding="utf-8") as f:
                docs_info = json.load(f)
            # 重建文档对象（仅元信息）
            for doc_id, info in docs_info.items():
                self._documents[doc_id] = Document(
                    content="",  # 内容在 chunks 中
                    source=info["source"],
                    id=info["id"],
                    title=info["title"],
                    doc_type=info["doc_type"]
                )
        
        self._initialized = True
        logger.info(f"Loaded RAG pipeline from {path}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "documents": len(self._documents),
            "chunks": self.store.size,
            "initialized": self._initialized,
            "embedder": type(self.embedder).__name__,
            "store": type(self.store).__name__,
        }


# 全局 RAG Pipeline 实例
_rag_pipeline: Optional[RAGPipeline] = None


def get_rag_pipeline() -> RAGPipeline:
    """
    获取全局 RAG Pipeline 实例
    
    Returns:
        RAGPipeline 实例
    """
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline


async def quick_retrieve(query: str, top_k: int = 5) -> List[RetrievalResult]:
    """
    快速检索
    
    Args:
        query: 查询文本
        top_k: 返回数量
        
    Returns:
        检索结果
    """
    rag = get_rag_pipeline()
    return await rag.retrieve(query, top_k=top_k)
