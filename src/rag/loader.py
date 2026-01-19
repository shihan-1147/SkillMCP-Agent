"""
文档加载器

支持加载 Markdown 和 TXT 文件
"""

import re
from pathlib import Path
from typing import List, Optional, Set

from src.core.logging import get_logger

from .document import Document

logger = get_logger("rag.loader")


class DocumentLoader:
    """
    文档加载器

    支持的格式:
    - Markdown (.md)
    - 纯文本 (.txt)

    使用示例:
    ```python
    loader = DocumentLoader()

    # 加载单个文件
    doc = loader.load_file("readme.md")

    # 加载目录
    docs = loader.load_directory("./docs")
    ```
    """

    SUPPORTED_EXTENSIONS: Set[str] = {".md", ".markdown", ".txt", ".text"}

    def __init__(self, encoding: str = "utf-8"):
        """
        初始化加载器

        Args:
            encoding: 文件编码
        """
        self.encoding = encoding

    def load_file(self, file_path: str | Path) -> Optional[Document]:
        """
        加载单个文件

        Args:
            file_path: 文件路径

        Returns:
            Document 对象，失败返回 None
        """
        path = Path(file_path)

        if not path.exists():
            logger.error(f"File not found: {path}")
            return None

        if not path.is_file():
            logger.error(f"Not a file: {path}")
            return None

        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            logger.warning(f"Unsupported file type: {path.suffix}")
            return None

        try:
            content = path.read_text(encoding=self.encoding)
            doc_type = (
                "markdown" if path.suffix.lower() in (".md", ".markdown") else "txt"
            )

            # 提取标题
            title = self._extract_title(content, doc_type) or path.stem

            # 清理内容
            cleaned_content = self._clean_content(content, doc_type)

            doc = Document(
                content=cleaned_content,
                source=str(path.absolute()),
                title=title,
                doc_type=doc_type,
                metadata={
                    "file_name": path.name,
                    "file_size": path.stat().st_size,
                    "extension": path.suffix,
                },
            )

            logger.info(f"Loaded document: {path.name} ({len(doc)} chars)")
            return doc

        except Exception as e:
            logger.error(f"Failed to load file {path}: {e}")
            return None

    def load_directory(
        self, dir_path: str | Path, recursive: bool = True, pattern: str = None
    ) -> List[Document]:
        """
        加载目录中的所有文档

        Args:
            dir_path: 目录路径
            recursive: 是否递归加载子目录
            pattern: 文件名匹配模式 (glob)

        Returns:
            Document 列表
        """
        path = Path(dir_path)

        if not path.exists():
            logger.error(f"Directory not found: {path}")
            return []

        if not path.is_dir():
            logger.error(f"Not a directory: {path}")
            return []

        documents = []

        # 构建文件迭代器
        if pattern:
            if recursive:
                files = path.rglob(pattern)
            else:
                files = path.glob(pattern)
        else:
            # 默认加载所有支持的文件
            files = []
            for ext in self.SUPPORTED_EXTENSIONS:
                if recursive:
                    files.extend(path.rglob(f"*{ext}"))
                else:
                    files.extend(path.glob(f"*{ext}"))

        for file_path in files:
            doc = self.load_file(file_path)
            if doc:
                documents.append(doc)

        logger.info(f"Loaded {len(documents)} documents from {path}")
        return documents

    def load_text(
        self,
        content: str,
        source: str = "inline",
        title: str = "Untitled",
        doc_type: str = "txt",
    ) -> Document:
        """
        从字符串加载文档

        Args:
            content: 文档内容
            source: 来源标识
            title: 文档标题
            doc_type: 文档类型

        Returns:
            Document 对象
        """
        cleaned_content = self._clean_content(content, doc_type)

        return Document(
            content=cleaned_content, source=source, title=title, doc_type=doc_type
        )

    def _extract_title(self, content: str, doc_type: str) -> Optional[str]:
        """从内容中提取标题"""
        if doc_type == "markdown":
            # 匹配 Markdown 一级标题
            match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            if match:
                return match.group(1).strip()

        # 尝试取第一行作为标题
        lines = content.strip().split("\n")
        if lines:
            first_line = lines[0].strip()
            if len(first_line) <= 100:  # 标题不应太长
                return first_line

        return None

    def _clean_content(self, content: str, doc_type: str) -> str:
        """清理文档内容"""
        # 统一换行符
        content = content.replace("\r\n", "\n").replace("\r", "\n")

        # 移除过多空行
        content = re.sub(r"\n{3,}", "\n\n", content)

        if doc_type == "markdown":
            # 移除 HTML 注释
            content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)

            # 可选：移除代码块中的内容（保留代码块标记）
            # content = re.sub(r'```[\s\S]*?```', '[CODE BLOCK]', content)

        return content.strip()
