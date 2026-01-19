"""
全局配置管理模块
使用 Pydantic Settings 进行配置验证
"""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 项目配置
    project_name: str = "SkillMCP-Agent"
    version: str = "0.1.0"
    debug: bool = True

    # API 服务配置
    api_host: str = Field(default="127.0.0.1", description="API 服务地址")
    api_port: int = Field(default=8000, description="API 服务端口")
    api_key: Optional[str] = Field(default=None, description="API 访问密钥（可选）")
    cors_origins: list = Field(default=["*"], description="CORS 允许的来源")

    # LLM 配置 - Ollama
    llm_provider: str = Field(default="ollama", description="LLM 提供者: ollama/openai")
    ollama_base_url: str = Field(
        default="http://localhost:11434", description="Ollama API 地址"
    )
    ollama_model: str = Field(
        default="gemini-3-flash-preview:latest", description="Ollama 模型"
    )

    # OpenAI 配置（备用）
    openai_api_key: str = Field(default="", description="OpenAI API Key")
    openai_base_url: Optional[str] = Field(default=None, description="OpenAI Base URL")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI 模型")

    # Embedding 配置 - Ollama
    embedding_provider: str = Field(
        default="ollama", description="Embedding 提供者: ollama/openai/local/mock"
    )
    ollama_embedding_model: str = Field(
        default="qwen3-embedding:latest", description="Ollama Embedding 模型"
    )
    embedding_model: str = Field(
        default="text-embedding-3-small", description="OpenAI Embedding 模型"
    )
    embedding_dimension: int = Field(default=4096, description="向量维度")

    # RAG 配置
    rag_chunk_size: int = Field(default=500, description="文档切分大小")
    rag_chunk_overlap: int = Field(default=50, description="切分重叠大小")
    rag_top_k: int = Field(default=5, description="检索返回数量")
    rag_score_threshold: float = Field(default=0.3, description="检索分数阈值")
    rag_embedder_type: str = Field(
        default="ollama", description="Embedder 类型: ollama/openai/local/mock"
    )
    rag_index_path: str = Field(
        default="data/rag_index", description="RAG 索引存储路径"
    )

    # 路径配置
    documents_dir: str = Field(default="data/documents", description="文档目录")
    vectordb_dir: str = Field(default="data/vectordb", description="向量库目录")
    data_dir: str = Field(default="data", description="数据目录")
    log_dir: str = Field(default="logs", description="日志目录")

    # 外部 API 配置
    amap_api_key: str = Field(default="", description="高德地图 API Key")
    use_real_api: bool = Field(default=True, description="是否使用真实 API（否则报错）")

    # Agent 配置
    max_iterations: int = Field(default=10, description="Agent 最大迭代次数")
    max_history_length: int = Field(default=20, description="最大历史消息数")

    # 兼容旧字段
    @property
    def chunk_size(self) -> int:
        return self.rag_chunk_size

    @property
    def chunk_overlap(self) -> int:
        return self.rag_chunk_overlap

    @property
    def top_k(self) -> int:
        return self.rag_top_k

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 全局配置单例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取全局配置实例"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# 兼容旧代码
settings = get_settings()
