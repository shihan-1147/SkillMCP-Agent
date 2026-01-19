"""
RAG (Retrieval-Augmented Generation) 子系统

提供文档加载、切分、向量化、检索功能

架构:
- loader: 文档加载器 (Markdown/TXT)
- chunker: 文本分块器 (Chunk + Overlap)
- embedder: 向量化 (Embedding)
- store: 向量存储 (FAISS)
- retriever: 检索器
- pipeline: RAG 管道

使用示例:
```python
from src.rag import RAGPipeline

rag = RAGPipeline()
await rag.load_documents("./docs")
results = await rag.retrieve("什么是 AI Agent?", top_k=5)
```
"""

from .chunker import ChunkStrategy, TextChunker
from .document import Document, DocumentChunk, RetrievalResult
from .embedder import Embedder, get_embedder
from .loader import DocumentLoader
from .pipeline import RAGPipeline, get_rag_pipeline
from .retriever import Retriever
from .store import FAISSStore, VectorStore

__all__ = [
    "Document",
    "DocumentChunk",
    "RetrievalResult",
    "DocumentLoader",
    "TextChunker",
    "ChunkStrategy",
    "Embedder",
    "get_embedder",
    "VectorStore",
    "FAISSStore",
    "Retriever",
    "RAGPipeline",
    "get_rag_pipeline",
]
