"""
向量存储

使用 FAISS 进行向量存储和相似度检索
"""
from typing import List, Optional, Dict, Any, Tuple
from abc import ABC, abstractmethod
from pathlib import Path
import json
import pickle
import numpy as np

from .document import DocumentChunk, RetrievalResult
from src.core.logging import get_logger

logger = get_logger("rag.store")


class VectorStore(ABC):
    """
    向量存储基类
    
    定义向量存储和检索接口
    """
    
    @abstractmethod
    def add(self, chunks: List[DocumentChunk]) -> None:
        """添加文档块"""
        pass
    
    @abstractmethod
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[RetrievalResult]:
        """搜索相似向量"""
        pass
    
    @abstractmethod
    def delete(self, doc_id: str) -> None:
        """删除指定文档的所有块"""
        pass
    
    @abstractmethod
    def save(self, path: str) -> None:
        """保存到磁盘"""
        pass
    
    @abstractmethod
    def load(self, path: str) -> None:
        """从磁盘加载"""
        pass
    
    @property
    @abstractmethod
    def size(self) -> int:
        """存储的向量数量"""
        pass


class FAISSStore(VectorStore):
    """
    FAISS 向量存储
    
    使用 Facebook 的 FAISS 库进行高效向量检索
    
    使用示例:
    ```python
    store = FAISSStore(dimension=384)
    store.add(chunks)
    
    results = store.search(query_embedding, top_k=5)
    
    store.save("./index")
    store.load("./index")
    ```
    """
    
    def __init__(
        self,
        dimension: int = 384,
        index_type: str = "flat"
    ):
        """
        初始化 FAISS 存储
        
        Args:
            dimension: 向量维度
            index_type: 索引类型 (flat/ivf/hnsw)
        """
        self.dimension = dimension
        self.index_type = index_type
        
        # 存储元数据
        self._chunks: Dict[int, DocumentChunk] = {}  # faiss_id -> chunk
        self._doc_chunks: Dict[str, List[int]] = {}  # doc_id -> [faiss_ids]
        self._next_id = 0
        
        # 初始化 FAISS 索引
        self._index = None
        self._init_index()
    
    def _init_index(self):
        """初始化 FAISS 索引"""
        try:
            import faiss
            
            if self.index_type == "flat":
                # 精确搜索（适合小规模数据）
                self._index = faiss.IndexFlatIP(self.dimension)  # 内积相似度
            elif self.index_type == "ivf":
                # IVF 索引（适合大规模数据）
                quantizer = faiss.IndexFlatIP(self.dimension)
                self._index = faiss.IndexIVFFlat(quantizer, self.dimension, 100)
            elif self.index_type == "hnsw":
                # HNSW 索引（高性能近似搜索）
                self._index = faiss.IndexHNSWFlat(self.dimension, 32)
            else:
                self._index = faiss.IndexFlatIP(self.dimension)
            
            logger.info(f"Initialized FAISS {self.index_type} index with dimension {self.dimension}")
            
        except ImportError:
            logger.warning("FAISS not installed, using mock index")
            self._index = MockFAISSIndex(self.dimension)
    
    def add(self, chunks: List[DocumentChunk]) -> None:
        """
        添加文档块
        
        Args:
            chunks: 带有 embedding 的文档块列表
        """
        if not chunks:
            return
        
        # 准备向量矩阵
        embeddings = []
        valid_chunks = []
        
        for chunk in chunks:
            if chunk.embedding is not None:
                embeddings.append(chunk.embedding)
                valid_chunks.append(chunk)
            else:
                logger.warning(f"Chunk {chunk.id} has no embedding, skipped")
        
        if not embeddings:
            return
        
        # 转换为 numpy 数组
        vectors = np.array(embeddings, dtype=np.float32)
        
        # 归一化（用于内积相似度）
        faiss_module = self._get_faiss()
        if faiss_module:
            faiss_module.normalize_L2(vectors)
        
        # 添加到索引
        self._index.add(vectors)
        
        # 存储元数据
        for chunk in valid_chunks:
            faiss_id = self._next_id
            self._chunks[faiss_id] = chunk
            
            if chunk.doc_id not in self._doc_chunks:
                self._doc_chunks[chunk.doc_id] = []
            self._doc_chunks[chunk.doc_id].append(faiss_id)
            
            self._next_id += 1
        
        logger.info(f"Added {len(valid_chunks)} chunks to FAISS index")
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[RetrievalResult]:
        """
        搜索相似向量
        
        Args:
            query_embedding: 查询向量
            top_k: 返回数量
            
        Returns:
            RetrievalResult 列表
        """
        if self.size == 0:
            return []
        
        # 准备查询向量
        query_vector = np.array([query_embedding], dtype=np.float32)
        
        # 归一化
        faiss_module = self._get_faiss()
        if faiss_module:
            faiss_module.normalize_L2(query_vector)
        
        # 搜索
        top_k = min(top_k, self.size)
        distances, indices = self._index.search(query_vector, top_k)
        
        # 构建结果
        results = []
        for rank, (idx, score) in enumerate(zip(indices[0], distances[0])):
            if idx == -1:  # FAISS 用 -1 表示无效结果
                continue
            
            chunk = self._chunks.get(int(idx))
            if chunk:
                results.append(RetrievalResult(
                    chunk=chunk,
                    score=float(score),
                    rank=rank
                ))
        
        return results
    
    def delete(self, doc_id: str) -> None:
        """
        删除指定文档的所有块
        
        注意：FAISS IndexFlatIP 不支持删除，需要重建索引
        
        Args:
            doc_id: 文档 ID
        """
        if doc_id not in self._doc_chunks:
            return
        
        # 获取要删除的 FAISS IDs
        ids_to_delete = set(self._doc_chunks[doc_id])
        
        # 重建索引（不包含要删除的向量）
        remaining_chunks = [
            chunk for faiss_id, chunk in self._chunks.items()
            if faiss_id not in ids_to_delete
        ]
        
        # 清空当前存储
        self._chunks.clear()
        self._doc_chunks.clear()
        self._next_id = 0
        self._init_index()
        
        # 重新添加
        if remaining_chunks:
            self.add(remaining_chunks)
        
        logger.info(f"Deleted document {doc_id} from index")
    
    def save(self, path: str) -> None:
        """
        保存索引到磁盘
        
        Args:
            path: 保存路径（目录）
        """
        save_dir = Path(path)
        save_dir.mkdir(parents=True, exist_ok=True)
        
        faiss_module = self._get_faiss()
        
        # 保存 FAISS 索引
        if faiss_module and not isinstance(self._index, MockFAISSIndex):
            faiss_module.write_index(self._index, str(save_dir / "faiss.index"))
        
        # 保存元数据
        metadata = {
            "dimension": self.dimension,
            "index_type": self.index_type,
            "next_id": self._next_id,
            "doc_chunks": self._doc_chunks,
        }
        
        with open(save_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # 保存 chunks
        with open(save_dir / "chunks.pkl", "wb") as f:
            pickle.dump(self._chunks, f)
        
        logger.info(f"Saved FAISS index to {path}")
    
    def load(self, path: str) -> None:
        """
        从磁盘加载索引
        
        Args:
            path: 加载路径（目录）
        """
        load_dir = Path(path)
        
        if not load_dir.exists():
            raise FileNotFoundError(f"Index not found: {path}")
        
        faiss_module = self._get_faiss()
        
        # 加载 FAISS 索引
        index_path = load_dir / "faiss.index"
        if faiss_module and index_path.exists():
            self._index = faiss_module.read_index(str(index_path))
        
        # 加载元数据
        with open(load_dir / "metadata.json", "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        self.dimension = metadata["dimension"]
        self.index_type = metadata["index_type"]
        self._next_id = metadata["next_id"]
        self._doc_chunks = metadata["doc_chunks"]
        
        # 加载 chunks
        with open(load_dir / "chunks.pkl", "rb") as f:
            self._chunks = pickle.load(f)
        
        logger.info(f"Loaded FAISS index from {path}")
    
    @property
    def size(self) -> int:
        """存储的向量数量"""
        return len(self._chunks)
    
    def _get_faiss(self):
        """获取 faiss 模块"""
        try:
            import faiss
            return faiss
        except ImportError:
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        return {
            "total_chunks": self.size,
            "total_documents": len(self._doc_chunks),
            "dimension": self.dimension,
            "index_type": self.index_type,
        }


class MockFAISSIndex:
    """
    Mock FAISS 索引
    
    当 FAISS 未安装时使用，使用纯 NumPy 实现
    """
    
    def __init__(self, dimension: int):
        self.dimension = dimension
        self.vectors = []
    
    def add(self, vectors: np.ndarray):
        """添加向量"""
        for v in vectors:
            self.vectors.append(v.copy())
    
    def search(self, query: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray]:
        """搜索相似向量"""
        if not self.vectors:
            return np.array([[-1] * k]), np.array([[0.0] * k])
        
        vectors = np.array(self.vectors)
        
        # 计算内积相似度
        similarities = np.dot(vectors, query.T).flatten()
        
        # 获取 top-k
        k = min(k, len(similarities))
        top_indices = np.argsort(similarities)[-k:][::-1]
        top_scores = similarities[top_indices]
        
        return np.array([top_indices]), np.array([top_scores])
    
    @property
    def ntotal(self) -> int:
        return len(self.vectors)
