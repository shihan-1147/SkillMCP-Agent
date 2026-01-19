"""
文档数据模型

定义文档和文档块的结构
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import hashlib


@dataclass
class Document:
    """
    原始文档
    
    Attributes:
        id: 文档唯一标识
        content: 文档内容
        source: 来源路径
        title: 文档标题
        doc_type: 文档类型 (markdown/txt)
        metadata: 额外元数据
        created_at: 创建时间
    """
    content: str
    source: str
    id: str = ""
    title: str = ""
    doc_type: str = "txt"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.id:
            # 基于内容和来源生成唯一 ID
            hash_input = f"{self.source}:{self.content[:500]}"
            self.id = hashlib.md5(hash_input.encode()).hexdigest()[:12]
        
        if not self.title and self.source:
            # 从路径提取标题
            from pathlib import Path
            self.title = Path(self.source).stem
    
    def __len__(self) -> int:
        return len(self.content)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "source": self.source,
            "title": self.title,
            "doc_type": self.doc_type,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class DocumentChunk:
    """
    文档块
    
    文档切分后的片段，用于向量化和检索
    
    Attributes:
        id: 块唯一标识
        content: 块内容
        doc_id: 所属文档 ID
        chunk_index: 在文档中的序号
        start_pos: 在原文中的起始位置
        end_pos: 在原文中的结束位置
        embedding: 向量表示
        metadata: 额外元数据
    """
    content: str
    doc_id: str
    chunk_index: int = 0
    id: str = ""
    start_pos: int = 0
    end_pos: int = 0
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = f"{self.doc_id}_chunk_{self.chunk_index}"
    
    def __len__(self) -> int:
        return len(self.content)
    
    @property
    def has_embedding(self) -> bool:
        return self.embedding is not None and len(self.embedding) > 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "doc_id": self.doc_id,
            "chunk_index": self.chunk_index,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "has_embedding": self.has_embedding,
            "metadata": self.metadata,
        }


@dataclass
class RetrievalResult:
    """
    检索结果
    
    Attributes:
        chunk: 文档块
        score: 相似度分数
        rank: 排名
    """
    chunk: DocumentChunk
    score: float
    rank: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk": self.chunk.to_dict(),
            "score": self.score,
            "rank": self.rank,
        }
    
    def to_context_string(self) -> str:
        """转换为上下文字符串，用于注入 Prompt"""
        return f"[来源: {self.chunk.metadata.get('source', 'unknown')}]\n{self.chunk.content}"
