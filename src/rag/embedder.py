"""
文本向量化器

支持 Ollama、OpenAI Embedding 和本地模型
"""
from typing import List, Optional, Union
from abc import ABC, abstractmethod
import asyncio
import numpy as np
import httpx

from .document import DocumentChunk
from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger("rag.embedder")


class Embedder(ABC):
    """
    向量化器基类
    
    定义向量化接口
    """
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """向量维度"""
        pass
    
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """
        向量化单个文本
        
        Args:
            text: 输入文本
            
        Returns:
            向量列表
        """
        pass
    
    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        批量向量化文本
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表的列表
        """
        pass
    
    async def embed_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """
        向量化文档块
        
        Args:
            chunks: 文档块列表
            
        Returns:
            带有 embedding 的文档块列表
        """
        texts = [chunk.content for chunk in chunks]
        embeddings = await self.embed_texts(texts)
        
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding
        
        return chunks


class OpenAIEmbedder(Embedder):
    """
    OpenAI Embedding 向量化器
    
    使用 OpenAI 的 text-embedding-ada-002 或 text-embedding-3-small 模型
    """
    
    MODEL_DIMENSIONS = {
        "text-embedding-ada-002": 1536,
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
    }
    
    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: str = None,
        base_url: str = None,
        batch_size: int = 100
    ):
        """
        初始化 OpenAI Embedder
        
        Args:
            model: 模型名称
            api_key: API Key
            base_url: API Base URL
            batch_size: 批处理大小
        """
        self.model = model
        self.batch_size = batch_size
        self._dimension = self.MODEL_DIMENSIONS.get(model, 1536)
        
        settings = get_settings()
        self.api_key = api_key or settings.openai_api_key
        self.base_url = base_url or settings.openai_base_url
        
        self._client = None
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    def _get_client(self):
        """获取 OpenAI 客户端"""
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        return self._client
    
    async def embed_text(self, text: str) -> List[float]:
        """向量化单个文本"""
        embeddings = await self.embed_texts([text])
        return embeddings[0]
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量向量化文本"""
        if not texts:
            return []
        
        client = self._get_client()
        all_embeddings = []
        
        # 分批处理
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            
            try:
                response = await client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
                
                logger.debug(f"Embedded batch {i // self.batch_size + 1}, {len(batch)} texts")
                
            except Exception as e:
                logger.error(f"Embedding failed: {e}")
                # 返回零向量作为 fallback
                all_embeddings.extend([[0.0] * self._dimension] * len(batch))
        
        return all_embeddings


class MockEmbedder(Embedder):
    """
    Mock 向量化器
    
    用于测试和演示，不需要 API 调用
    使用简单的词袋模型模拟向量化
    """
    
    def __init__(self, dimension: int = 384):
        """
        初始化 Mock Embedder
        
        Args:
            dimension: 向量维度
        """
        self._dimension = dimension
        self._vocab = {}
        self._vocab_size = 0
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    async def embed_text(self, text: str) -> List[float]:
        """向量化单个文本"""
        # 简单的词袋 + 位置编码模拟
        words = text.lower().split()
        vector = np.zeros(self._dimension)
        
        for i, word in enumerate(words):
            # 为每个词分配一个固定的伪随机向量
            np.random.seed(hash(word) % (2**32))
            word_vec = np.random.randn(self._dimension)
            
            # 位置衰减
            decay = 1.0 / (1 + i * 0.1)
            vector += word_vec * decay
        
        # 归一化
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector.tolist()
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量向量化文本"""
        embeddings = []
        for text in texts:
            embedding = await self.embed_text(text)
            embeddings.append(embedding)
        return embeddings


class OllamaEmbedder(Embedder):
    """
    Ollama Embedding 向量化器
    
    使用本地部署的 Ollama 服务进行向量化
    """
    
    def __init__(
        self,
        model: str = "qwen3-embedding:latest",
        base_url: str = "http://localhost:11434",
        dimension: int = 1024,
        batch_size: int = 32,
        timeout: float = 60.0
    ):
        """
        初始化 Ollama Embedder
        
        Args:
            model: Ollama embedding 模型名称
            base_url: Ollama API 地址
            dimension: 向量维度
            batch_size: 批处理大小
            timeout: 请求超时时间
        """
        self.model = model
        self.base_url = base_url.rstrip('/')
        self._dimension = dimension
        self.batch_size = batch_size
        self.timeout = timeout
        self._client = None
        
        logger.info(f"OllamaEmbedder initialized: model={model}, base_url={base_url}")
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout)
            )
        return self._client
    
    async def embed_text(self, text: str) -> List[float]:
        """向量化单个文本"""
        client = self._get_client()
        
        try:
            response = await client.post(
                "/api/embed",
                json={
                    "model": self.model,
                    "input": text
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Ollama embed API 返回格式: {"embeddings": [[...]]}
            embeddings = data.get("embeddings", [])
            if embeddings and len(embeddings) > 0:
                embedding = embeddings[0]
                # 动态更新维度
                if len(embedding) != self._dimension:
                    self._dimension = len(embedding)
                    logger.info(f"Updated embedding dimension to {self._dimension}")
                return embedding
            
            logger.warning(f"Empty embedding response for text: {text[:50]}...")
            return [0.0] * self._dimension
            
        except Exception as e:
            logger.error(f"Ollama embedding failed: {e}")
            return [0.0] * self._dimension
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量向量化文本"""
        if not texts:
            return []
        
        client = self._get_client()
        all_embeddings = []
        
        # 分批处理
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            
            try:
                # Ollama embed API 支持批量输入
                response = await client.post(
                    "/api/embed",
                    json={
                        "model": self.model,
                        "input": batch
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                embeddings = data.get("embeddings", [])
                
                # 动态更新维度
                if embeddings and len(embeddings) > 0 and len(embeddings[0]) != self._dimension:
                    self._dimension = len(embeddings[0])
                    logger.info(f"Updated embedding dimension to {self._dimension}")
                
                all_embeddings.extend(embeddings)
                logger.debug(f"Embedded batch {i // self.batch_size + 1}, {len(batch)} texts")
                
            except Exception as e:
                logger.error(f"Ollama batch embedding failed: {e}")
                # 尝试逐个处理
                for text in batch:
                    embedding = await self.embed_text(text)
                    all_embeddings.append(embedding)
        
        return all_embeddings
    
    async def close(self):
        """关闭客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None


class SentenceTransformerEmbedder(Embedder):
    """
    SentenceTransformer 本地向量化器
    
    使用本地模型进行向量化，不需要 API 调用
    需要安装: pip install sentence-transformers
    """
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: str = None
    ):
        """
        初始化 SentenceTransformer Embedder
        
        Args:
            model_name: 模型名称
            device: 设备 (cpu/cuda)
        """
        self.model_name = model_name
        self.device = device
        self._model = None
        self._dimension = None
    
    def _load_model(self):
        """懒加载模型"""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name, device=self.device)
                self._dimension = self._model.get_sentence_embedding_dimension()
                logger.info(f"Loaded SentenceTransformer model: {self.model_name}")
            except ImportError:
                raise ImportError(
                    "Please install sentence-transformers: pip install sentence-transformers"
                )
        return self._model
    
    @property
    def dimension(self) -> int:
        if self._dimension is None:
            self._load_model()
        return self._dimension
    
    async def embed_text(self, text: str) -> List[float]:
        """向量化单个文本"""
        model = self._load_model()
        # 在线程池中运行同步代码
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None, lambda: model.encode(text).tolist()
        )
        return embedding
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """批量向量化文本"""
        model = self._load_model()
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None, lambda: model.encode(texts).tolist()
        )
        return embeddings


# 全局 Embedder 实例
_embedder: Optional[Embedder] = None


def get_embedder(embedder_type: str = None) -> Embedder:
    """
    获取 Embedder 实例
    
    Args:
        embedder_type: 类型 (ollama/openai/local/mock)，默认从配置读取
        
    Returns:
        Embedder 实例
    """
    global _embedder
    
    if _embedder is not None:
        return _embedder
    
    settings = get_settings()
    embedder_type = embedder_type or settings.rag_embedder_type
    
    if embedder_type == "ollama":
        _embedder = OllamaEmbedder(
            model=settings.ollama_embedding_model,
            base_url=settings.ollama_base_url,
            dimension=settings.embedding_dimension
        )
        logger.info(f"Using OllamaEmbedder: {settings.ollama_embedding_model}")
    elif embedder_type == "openai":
        _embedder = OpenAIEmbedder()
        logger.info("Using OpenAIEmbedder")
    elif embedder_type == "local":
        _embedder = SentenceTransformerEmbedder()
        logger.info("Using SentenceTransformerEmbedder")
    else:
        _embedder = MockEmbedder()
        logger.warning("Using MockEmbedder for testing")
    
    return _embedder


def set_embedder(embedder: Embedder) -> None:
    """设置全局 Embedder"""
    global _embedder
    _embedder = embedder
