"""
文本分块器

将长文档切分为适合向量化的小块
"""

import re
from enum import Enum
from typing import List, Optional

from src.core.logging import get_logger

from .document import Document, DocumentChunk

logger = get_logger("rag.chunker")


class ChunkStrategy(str, Enum):
    """分块策略"""

    FIXED_SIZE = "fixed_size"  # 固定大小
    SENTENCE = "sentence"  # 按句子
    PARAGRAPH = "paragraph"  # 按段落
    MARKDOWN = "markdown"  # Markdown 结构


class TextChunker:
    """
    文本分块器

    支持多种分块策略:
    - fixed_size: 固定字符数切分
    - sentence: 按句子边界切分
    - paragraph: 按段落切分
    - markdown: 按 Markdown 结构切分

    使用示例:
    ```python
    chunker = TextChunker(chunk_size=500, overlap=50)
    chunks = chunker.chunk_document(document)
    ```
    """

    def __init__(
        self,
        chunk_size: int = 500,
        overlap: int = 50,
        strategy: ChunkStrategy = ChunkStrategy.FIXED_SIZE,
        min_chunk_size: int = 100,
    ):
        """
        初始化分块器

        Args:
            chunk_size: 目标块大小（字符数）
            overlap: 块之间的重叠大小
            strategy: 分块策略
            min_chunk_size: 最小块大小（小于此值会与前一块合并）
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.strategy = strategy
        self.min_chunk_size = min_chunk_size

        # 验证参数
        if overlap >= chunk_size:
            raise ValueError("Overlap must be less than chunk_size")

    def chunk_document(self, document: Document) -> List[DocumentChunk]:
        """
        将文档切分为块

        Args:
            document: 文档对象

        Returns:
            DocumentChunk 列表
        """
        content = document.content

        if not content or len(content) < self.min_chunk_size:
            # 内容太短，直接作为一个块
            return [
                DocumentChunk(
                    content=content,
                    doc_id=document.id,
                    chunk_index=0,
                    start_pos=0,
                    end_pos=len(content),
                    metadata={
                        "source": document.source,
                        "title": document.title,
                        "doc_type": document.doc_type,
                    },
                )
            ]

        # 根据策略选择切分方法
        if self.strategy == ChunkStrategy.FIXED_SIZE:
            chunks = self._chunk_fixed_size(content)
        elif self.strategy == ChunkStrategy.SENTENCE:
            chunks = self._chunk_by_sentence(content)
        elif self.strategy == ChunkStrategy.PARAGRAPH:
            chunks = self._chunk_by_paragraph(content)
        elif self.strategy == ChunkStrategy.MARKDOWN:
            chunks = self._chunk_markdown(content)
        else:
            chunks = self._chunk_fixed_size(content)

        # 转换为 DocumentChunk 对象
        result = []
        for idx, (text, start, end) in enumerate(chunks):
            chunk = DocumentChunk(
                content=text,
                doc_id=document.id,
                chunk_index=idx,
                start_pos=start,
                end_pos=end,
                metadata={
                    "source": document.source,
                    "title": document.title,
                    "doc_type": document.doc_type,
                },
            )
            result.append(chunk)

        logger.debug(f"Document {document.id} chunked into {len(result)} pieces")
        return result

    def chunk_documents(self, documents: List[Document]) -> List[DocumentChunk]:
        """
        批量切分文档

        Args:
            documents: 文档列表

        Returns:
            所有文档的 DocumentChunk 列表
        """
        all_chunks = []
        for doc in documents:
            chunks = self.chunk_document(doc)
            all_chunks.extend(chunks)

        logger.info(f"Chunked {len(documents)} documents into {len(all_chunks)} chunks")
        return all_chunks

    def _chunk_fixed_size(self, text: str) -> List[tuple]:
        """固定大小切分"""
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + self.chunk_size, text_len)

            # 尝试在句子边界切分
            if end < text_len:
                # 向后查找句子结束符
                for sep in ["。", "！", "？", ".", "!", "?", "\n"]:
                    sep_pos = text.rfind(sep, start + self.chunk_size // 2, end)
                    if sep_pos != -1:
                        end = sep_pos + 1
                        break

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append((chunk_text, start, end))

            # 计算下一个起始位置（考虑重叠）
            start = end - self.overlap if end < text_len else text_len

        return self._merge_small_chunks(chunks)

    def _chunk_by_sentence(self, text: str) -> List[tuple]:
        """按句子切分"""
        # 句子分割正则
        sentence_pattern = r"([^。！？.!?\n]+[。！？.!?\n]?)"
        sentences = re.findall(sentence_pattern, text)

        chunks = []
        current_chunk = ""
        current_start = 0
        pos = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if len(current_chunk) + len(sentence) <= self.chunk_size:
                current_chunk += sentence
            else:
                if current_chunk:
                    chunks.append((current_chunk, current_start, pos))

                # 重叠处理：保留前一块的末尾
                overlap_text = (
                    current_chunk[-self.overlap :]
                    if len(current_chunk) > self.overlap
                    else ""
                )
                current_chunk = overlap_text + sentence
                current_start = max(0, pos - len(overlap_text))

            pos += len(sentence)

        if current_chunk:
            chunks.append((current_chunk, current_start, pos))

        return self._merge_small_chunks(chunks)

    def _chunk_by_paragraph(self, text: str) -> List[tuple]:
        """按段落切分"""
        paragraphs = text.split("\n\n")

        chunks = []
        current_chunk = ""
        current_start = 0
        pos = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                pos += 2  # 空段落
                continue

            if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                if current_chunk:
                    current_chunk += "\n\n"
                current_chunk += para
            else:
                if current_chunk:
                    chunks.append((current_chunk, current_start, pos))
                current_chunk = para
                current_start = pos

            pos += len(para) + 2

        if current_chunk:
            chunks.append((current_chunk, current_start, pos))

        return self._merge_small_chunks(chunks)

    def _chunk_markdown(self, text: str) -> List[tuple]:
        """按 Markdown 结构切分"""
        # 按标题切分
        header_pattern = r"^(#{1,3})\s+(.+)$"
        lines = text.split("\n")

        sections = []
        current_section = []
        current_start = 0
        pos = 0

        for line in lines:
            if re.match(header_pattern, line):
                if current_section:
                    section_text = "\n".join(current_section)
                    if section_text.strip():
                        sections.append((section_text, current_start, pos))
                current_section = [line]
                current_start = pos
            else:
                current_section.append(line)
            pos += len(line) + 1

        if current_section:
            section_text = "\n".join(current_section)
            if section_text.strip():
                sections.append((section_text, current_start, pos))

        # 如果 section 太大，进一步切分
        final_chunks = []
        for section_text, start, end in sections:
            if len(section_text) > self.chunk_size:
                # 递归使用固定大小切分
                sub_chunks = self._chunk_fixed_size(section_text)
                for sub_text, sub_start, sub_end in sub_chunks:
                    final_chunks.append((sub_text, start + sub_start, start + sub_end))
            else:
                final_chunks.append((section_text, start, end))

        return self._merge_small_chunks(final_chunks)

    def _merge_small_chunks(self, chunks: List[tuple]) -> List[tuple]:
        """合并过小的块"""
        if not chunks:
            return chunks

        merged = []
        current_text, current_start, current_end = chunks[0]

        for text, start, end in chunks[1:]:
            if len(current_text) < self.min_chunk_size:
                # 当前块太小，与下一块合并
                current_text += "\n" + text
                current_end = end
            else:
                merged.append((current_text, current_start, current_end))
                current_text, current_start, current_end = text, start, end

        merged.append((current_text, current_start, current_end))
        return merged
