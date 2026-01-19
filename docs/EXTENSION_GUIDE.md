# SkillMCP-Agent 扩展开发指南

本文档详细说明如何扩展 SkillMCP-Agent 系统，包括新增技能、MCP 工具、RAG 数据源等。

---

## 目录

1. [新增 Skill（技能）](#1-新增-skill技能)
2. [新增 MCP Tool（工具）](#2-新增-mcp-tool工具)
3. [新增 RAG 数据源](#3-新增-rag-数据源)
4. [自定义 LLM Provider](#4-自定义-llm-provider)
5. [扩展 API 接口](#5-扩展-api-接口)
6. [前端组件扩展](#6-前端组件扩展)

---

## 1. 新增 Skill（技能）

技能（Skill）是 Agent 的业务能力单元，负责处理特定类型的用户请求。

### 1.1 技能架构

```
用户输入 → Planner(意图识别) → SkillSelector(技能选择) → Skill(执行) → 结果
                                                            ↓
                                                    MCP Tools / RAG
```

### 1.2 创建新技能

**步骤 1**: 创建技能文件

```python
# src/skills/impl/translator_skill.py

from typing import Dict, Any, Optional
from src.skills.base import BaseSkill
from src.skills.registry import skill_registry
from src.core.logging import get_logger

logger = get_logger("skills.translator")


@skill_registry.register("translator")
class TranslatorSkill(BaseSkill):
    """翻译技能 - 处理多语言翻译请求"""
    
    # ========== 基础配置 ==========
    name = "translator"
    description = "多语言翻译技能，支持中英日韩等语言互译"
    version = "1.0.0"
    
    # 触发关键词（用于技能选择）
    keywords = [
        "翻译", "translate", "翻成", "用英语怎么说",
        "中译英", "英译中", "日语", "韩语"
    ]
    
    # 优先级（数值越高优先级越高）
    priority = 10
    
    # 技能能力声明
    capabilities = ["translate", "detect_language"]
    
    # ========== 核心方法 ==========
    
    async def execute(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        执行翻译
        
        Args:
            query: 用户输入，如 "把hello翻译成中文"
            context: 上下文信息，包含：
                - session_id: 会话ID
                - history: 历史对话
                - user_info: 用户信息
        
        Returns:
            dict: {
                "success": bool,
                "data": {...},
                "message": str
            }
        """
        context = context or {}
        
        try:
            # 1. 解析翻译请求
            parsed = self._parse_translation_request(query)
            source_text = parsed["text"]
            source_lang = parsed["source_lang"]
            target_lang = parsed["target_lang"]
            
            logger.info(f"Translating: {source_lang} -> {target_lang}")
            
            # 2. 调用 MCP 翻译工具（如果有）
            # from src.mcp import get_mcp_client
            # mcp = get_mcp_client()
            # result = await mcp.call_tool("translate_api", {
            #     "text": source_text,
            #     "source": source_lang,
            #     "target": target_lang
            # })
            
            # 3. 或直接调用翻译 API / LLM
            translated = await self._translate_with_llm(
                source_text, source_lang, target_lang
            )
            
            return {
                "success": True,
                "data": {
                    "original": source_text,
                    "translated": translated,
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                },
                "message": f"翻译完成: {translated}"
            }
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return {
                "success": False,
                "data": None,
                "message": f"翻译失败: {str(e)}"
            }
    
    def can_handle(self, query: str, context: Optional[Dict] = None) -> float:
        """
        判断是否能处理该查询
        
        Args:
            query: 用户查询
            context: 上下文
        
        Returns:
            float: 置信度 (0.0 - 1.0)
        """
        query_lower = query.lower()
        
        # 关键词匹配
        for keyword in self.keywords:
            if keyword in query_lower:
                return 0.9
        
        # 模式匹配
        patterns = [
            r"翻译[成为]",
            r"用.+[说写]",
            r"\btranslate\b",
        ]
        import re
        for pattern in patterns:
            if re.search(pattern, query_lower):
                return 0.8
        
        return 0.0
    
    # ========== 辅助方法 ==========
    
    def _parse_translation_request(self, query: str) -> Dict[str, str]:
        """解析翻译请求"""
        # 简单实现，实际可用 NLP 或正则
        
        # 检测目标语言
        target_lang = "en"  # 默认英语
        if "中文" in query or "汉语" in query:
            target_lang = "zh"
        elif "英" in query or "english" in query.lower():
            target_lang = "en"
        elif "日" in query:
            target_lang = "ja"
        elif "韩" in query:
            target_lang = "ko"
        
        # 提取待翻译文本
        # 这里简化处理，实际需要更复杂的 NLP
        import re
        patterns = [
            r"[把将](.+?)翻译",
            r"翻译[：:]?\s*(.+)",
            r"\"(.+?)\"",
            r"'(.+?)'",
        ]
        
        text = query
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                text = match.group(1).strip()
                break
        
        return {
            "text": text,
            "source_lang": "auto",  # 自动检测
            "target_lang": target_lang
        }
    
    async def _translate_with_llm(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str
    ) -> str:
        """使用 LLM 翻译"""
        from src.core.ollama import get_ollama_client
        
        lang_names = {
            "zh": "中文",
            "en": "英语",
            "ja": "日语",
            "ko": "韩语",
            "auto": "自动检测"
        }
        
        prompt = f"""请将以下文本翻译成{lang_names.get(target_lang, target_lang)}:

原文: {text}

要求:
1. 保持原意，表达自然
2. 只输出翻译结果，不要解释

翻译:"""
        
        client = get_ollama_client()
        response = await client.generate(prompt)
        
        return response.get("response", "").strip()
```

**步骤 2**: 注册技能（自动）

由于使用了 `@skill_registry.register()` 装饰器，技能会自动注册。

**步骤 3**: 导入技能

```python
# src/skills/__init__.py

# 添加新技能的导入
from .impl.translator_skill import TranslatorSkill
```

### 1.3 技能生命周期

```python
class BaseSkill:
    # 初始化时调用
    async def setup(self):
        """初始化资源（如数据库连接、模型加载）"""
        pass
    
    # 销毁时调用
    async def teardown(self):
        """释放资源"""
        pass
    
    # 每次执行前调用
    async def before_execute(self, query: str, context: dict):
        """预处理（如参数验证、权限检查）"""
        pass
    
    # 每次执行后调用
    async def after_execute(self, result: dict):
        """后处理（如日志记录、指标采集）"""
        pass
```

### 1.4 技能间协作

技能可以调用其他技能：

```python
class ComplexSkill(BaseSkill):
    async def execute(self, query: str, context: dict = None):
        # 调用其他技能
        from src.skills import skill_registry
        
        weather_skill = skill_registry.get("weather")
        weather_result = await weather_skill.execute("北京天气", context)
        
        translator = skill_registry.get("translator")
        translated = await translator.execute(
            f"翻译: {weather_result['message']}", 
            context
        )
        
        return translated
```

---

## 2. 新增 MCP Tool（工具）

MCP Tool 是遵循 Model Context Protocol 规范的原子能力单元。

### 2.1 工具架构

```
Agent → MCP Client → MCP Server → Tool → 外部服务/API
                          ↓
                    工具发现 & 调用
```

### 2.2 创建新工具

**步骤 1**: 创建工具文件

```python
# src/mcp/tools/stock_tool.py

from typing import Dict, Any, Optional
from src.mcp.base import BaseTool
from src.mcp.registry import tool_registry
from src.core.logging import get_logger

logger = get_logger("mcp.tools.stock")


@tool_registry.register("stock_query")
class StockQueryTool(BaseTool):
    """股票查询工具 - 查询股票行情"""
    
    # ========== 工具元信息 ==========
    name = "stock_query"
    description = "查询股票实时行情、历史数据和公司信息"
    version = "1.0.0"
    
    # 参数 Schema (符合 JSON Schema 规范)
    parameters = {
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "股票代码，如 AAPL, 600519.SH"
            },
            "query_type": {
                "type": "string",
                "enum": ["realtime", "history", "info"],
                "description": "查询类型: realtime=实时行情, history=历史数据, info=公司信息",
                "default": "realtime"
            },
            "days": {
                "type": "integer",
                "description": "历史数据天数（仅 history 类型有效）",
                "default": 30,
                "minimum": 1,
                "maximum": 365
            }
        },
        "required": ["symbol"]
    }
    
    # 返回值 Schema
    returns = {
        "type": "object",
        "properties": {
            "symbol": {"type": "string"},
            "name": {"type": "string"},
            "price": {"type": "number"},
            "change": {"type": "number"},
            "change_percent": {"type": "string"},
            "volume": {"type": "integer"},
            "timestamp": {"type": "string"}
        }
    }
    
    # ========== 核心方法 ==========
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        执行股票查询
        
        Args:
            symbol: 股票代码
            query_type: 查询类型
            days: 历史天数
        
        Returns:
            dict: 查询结果
        """
        symbol = kwargs.get("symbol")
        query_type = kwargs.get("query_type", "realtime")
        days = kwargs.get("days", 30)
        
        # 参数验证
        if not symbol:
            return {
                "success": False,
                "error": "股票代码不能为空"
            }
        
        try:
            if query_type == "realtime":
                result = await self._get_realtime(symbol)
            elif query_type == "history":
                result = await self._get_history(symbol, days)
            elif query_type == "info":
                result = await self._get_info(symbol)
            else:
                return {
                    "success": False,
                    "error": f"不支持的查询类型: {query_type}"
                }
            
            return {
                "success": True,
                "data": result
            }
            
        except Exception as e:
            logger.error(f"Stock query failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def validate(self, **kwargs) -> Optional[str]:
        """
        验证参数
        
        Returns:
            str: 错误信息，None 表示验证通过
        """
        symbol = kwargs.get("symbol", "")
        if not symbol or len(symbol) < 2:
            return "股票代码格式不正确"
        
        query_type = kwargs.get("query_type", "realtime")
        if query_type not in ["realtime", "history", "info"]:
            return f"不支持的查询类型: {query_type}"
        
        return None
    
    # ========== 私有方法 ==========
    
    async def _get_realtime(self, symbol: str) -> Dict[str, Any]:
        """获取实时行情"""
        import httpx
        
        # 示例：调用行情 API
        # async with httpx.AsyncClient() as client:
        #     resp = await client.get(
        #         f"https://api.example.com/stock/{symbol}/realtime"
        #     )
        #     return resp.json()
        
        # Mock 数据
        return {
            "symbol": symbol,
            "name": "示例股票",
            "price": 150.25,
            "change": 2.35,
            "change_percent": "+1.59%",
            "volume": 12345678,
            "timestamp": "2024-01-15T10:30:00Z"
        }
    
    async def _get_history(self, symbol: str, days: int) -> Dict[str, Any]:
        """获取历史数据"""
        # 实现历史数据查询
        return {
            "symbol": symbol,
            "days": days,
            "data": [
                {"date": "2024-01-14", "close": 148.50},
                {"date": "2024-01-13", "close": 147.20},
            ]
        }
    
    async def _get_info(self, symbol: str) -> Dict[str, Any]:
        """获取公司信息"""
        return {
            "symbol": symbol,
            "name": "示例公司",
            "industry": "科技",
            "market_cap": "1000亿",
            "employees": 50000
        }
```

**步骤 2**: 导入工具

```python
# src/mcp/tools/__init__.py

from .stock_tool import StockQueryTool
```

### 2.3 工具调用示例

```python
# 在 Skill 中调用 MCP 工具

from src.mcp import get_mcp_client
from src.agent import get_tool_recorder

async def use_stock_tool():
    mcp = get_mcp_client()
    recorder = get_tool_recorder()
    
    # 开始记录
    entry = recorder.start_call(
        tool_name="stock_query",
        arguments={"symbol": "AAPL"},
        session_id="session_123"
    )
    
    try:
        # 调用工具
        result = await mcp.call_tool("stock_query", {
            "symbol": "AAPL",
            "query_type": "realtime"
        })
        
        # 完成记录
        recorder.end_call(entry.id, result=result)
        
    except Exception as e:
        recorder.end_call(entry.id, error=str(e))
        raise
```

### 2.4 工具参数 Schema

使用 JSON Schema 定义参数：

```python
parameters = {
    "type": "object",
    "properties": {
        # 必填字符串
        "name": {
            "type": "string",
            "description": "名称",
            "minLength": 1,
            "maxLength": 100
        },
        # 枚举值
        "type": {
            "type": "string",
            "enum": ["A", "B", "C"],
            "default": "A"
        },
        # 数字范围
        "count": {
            "type": "integer",
            "minimum": 1,
            "maximum": 100,
            "default": 10
        },
        # 数组
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 5
        },
        # 嵌套对象
        "options": {
            "type": "object",
            "properties": {
                "flag": {"type": "boolean", "default": False}
            }
        }
    },
    "required": ["name"]
}
```

---

## 3. 新增 RAG 数据源

### 3.1 RAG Pipeline 架构

```
文档 → Loader → Chunker → Embedder → VectorStore
                                          ↓
Query → Embedder → Retriever → 相关文档 → LLM → Response
```

### 3.2 添加文档

**方式 1: 从文件加载**

```python
from src.rag import get_rag_pipeline

pipeline = get_rag_pipeline()

# 加载单个文件
await pipeline.load_file("path/to/document.pdf")

# 加载目录
await pipeline.load_directory(
    "path/to/docs/",
    patterns=["*.md", "*.txt", "*.pdf"]
)
```

**方式 2: 直接添加文本**

```python
await pipeline.add_texts(
    texts=[
        "SkillMCP-Agent 是一个智能 Agent 系统...",
        "MCP 协议定义了工具调用的标准格式...",
    ],
    metadata=[
        {"source": "manual", "category": "intro"},
        {"source": "manual", "category": "protocol"},
    ]
)
```

**方式 3: 自定义 Loader**

```python
# src/rag/loaders/custom_loader.py

from typing import List, Dict, Any
from src.rag.loader import BaseLoader

class DatabaseLoader(BaseLoader):
    """从数据库加载文档"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
    
    async def load(self) -> List[Dict[str, Any]]:
        """加载文档"""
        import asyncpg
        
        conn = await asyncpg.connect(self.connection_string)
        rows = await conn.fetch(
            "SELECT id, content, title, category FROM documents"
        )
        await conn.close()
        
        documents = []
        for row in rows:
            documents.append({
                "content": row["content"],
                "metadata": {
                    "source": "database",
                    "doc_id": row["id"],
                    "title": row["title"],
                    "category": row["category"],
                }
            })
        
        return documents

# 使用
loader = DatabaseLoader("postgresql://...")
docs = await loader.load()
await pipeline.add_documents(docs)
```

### 3.3 自定义 Chunker

```python
# src/rag/chunkers/semantic_chunker.py

from typing import List
from src.rag.chunker import BaseChunker

class SemanticChunker(BaseChunker):
    """基于语义的文档切分"""
    
    def __init__(self, max_tokens: int = 512):
        self.max_tokens = max_tokens
    
    def chunk(self, text: str, metadata: dict = None) -> List[dict]:
        """按语义边界切分"""
        # 使用 NLP 模型检测语义边界
        # 这里简化为按段落切分
        
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) < self.max_tokens * 4:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append({
                        "content": current_chunk.strip(),
                        "metadata": metadata or {}
                    })
                current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append({
                "content": current_chunk.strip(),
                "metadata": metadata or {}
            })
        
        return chunks
```

---

## 4. 自定义 LLM Provider

### 4.1 实现自定义 Provider

```python
# src/core/llm/custom_provider.py

from typing import Dict, Any, AsyncIterator
from abc import ABC, abstractmethod

class BaseLLMProvider(ABC):
    """LLM Provider 基类"""
    
    @abstractmethod
    async def chat(
        self, 
        messages: list, 
        **kwargs
    ) -> Dict[str, Any]:
        """同步对话"""
        pass
    
    @abstractmethod
    async def chat_stream(
        self, 
        messages: list, 
        **kwargs
    ) -> AsyncIterator[str]:
        """流式对话"""
        pass


class CustomLLMProvider(BaseLLMProvider):
    """自定义 LLM Provider"""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
    
    async def chat(self, messages: list, **kwargs) -> Dict[str, Any]:
        import httpx
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/chat",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "messages": messages,
                    **kwargs
                }
            )
            return resp.json()
    
    async def chat_stream(
        self, 
        messages: list, 
        **kwargs
    ) -> AsyncIterator[str]:
        import httpx
        
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/stream",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"messages": messages, **kwargs}
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        yield line[6:]
```

### 4.2 注册 Provider

```python
# src/core/llm/__init__.py

from .custom_provider import CustomLLMProvider

def get_llm_provider():
    from src.core.config import get_settings
    settings = get_settings()
    
    if settings.llm_provider == "ollama":
        from src.core.ollama import get_ollama_client
        return get_ollama_client()
    elif settings.llm_provider == "openai":
        from .openai_provider import OpenAIProvider
        return OpenAIProvider(settings.openai_api_key)
    elif settings.llm_provider == "custom":
        return CustomLLMProvider(
            api_key=settings.custom_api_key,
            base_url=settings.custom_base_url
        )
    else:
        raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")
```

---

## 5. 扩展 API 接口

### 5.1 添加新路由

```python
# src/api/routes/custom.py

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/custom", tags=["custom"])


class CustomRequest(BaseModel):
    data: str
    options: Optional[dict] = None


class CustomResponse(BaseModel):
    success: bool
    result: dict


@router.post("/process", response_model=CustomResponse)
async def process_custom(request: CustomRequest):
    """自定义处理接口"""
    try:
        # 处理逻辑
        result = {"processed": request.data.upper()}
        return CustomResponse(success=True, result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_status():
    """获取状态"""
    return {"status": "ok"}
```

### 5.2 注册路由

```python
# src/api/app.py

from src.api.routes.custom import router as custom_router

app.include_router(custom_router, prefix="/api/v1")
```

---

## 6. 前端组件扩展

### 6.1 添加新组件

```vue
<!-- frontend/src/components/StockCard.vue -->

<template>
  <el-card class="stock-card">
    <template #header>
      <div class="header">
        <span class="symbol">{{ data.symbol }}</span>
        <span class="name">{{ data.name }}</span>
      </div>
    </template>
    
    <div class="price-info">
      <span class="price">{{ data.price }}</span>
      <span :class="['change', data.change > 0 ? 'up' : 'down']">
        {{ data.change > 0 ? '+' : '' }}{{ data.change }}
        ({{ data.change_percent }})
      </span>
    </div>
  </el-card>
</template>

<script setup>
defineProps({
  data: {
    type: Object,
    required: true
  }
})
</script>

<style scoped>
.stock-card {
  margin: 10px 0;
}
.header {
  display: flex;
  justify-content: space-between;
}
.symbol {
  font-weight: bold;
  font-size: 16px;
}
.price {
  font-size: 24px;
  font-weight: bold;
}
.change.up {
  color: #67c23a;
}
.change.down {
  color: #f56c6c;
}
</style>
```

### 6.2 在消息中使用

```vue
<!-- frontend/src/components/MessageBubble.vue -->

<template>
  <div class="message-bubble">
    <!-- 现有内容 -->
    
    <!-- 新增: 股票卡片 -->
    <StockCard 
      v-if="message.type === 'stock'" 
      :data="message.data" 
    />
  </div>
</template>

<script setup>
import StockCard from './StockCard.vue'
</script>
```

---

## 最佳实践

### 代码规范

1. **类型注解**: 所有函数都应有完整的类型注解
2. **文档字符串**: 公开方法必须有 docstring
3. **错误处理**: 使用 try-catch 并返回结构化错误
4. **日志记录**: 关键操作必须记录日志
5. **单元测试**: 新功能必须有对应测试

### 性能优化

1. **异步优先**: 所有 I/O 操作使用 async
2. **连接池**: 数据库/HTTP 使用连接池
3. **缓存**: 热点数据使用缓存
4. **批处理**: 向量化操作使用批处理

### 安全考虑

1. **输入验证**: 所有外部输入必须验证
2. **敏感数据**: API Key 等不能硬编码
3. **速率限制**: API 需要限流保护
4. **权限检查**: 操作前检查权限

---

## FAQ

**Q: 如何调试技能执行？**

A: 启用追踪器并查看控制台输出：
```python
from src.agent import create_tracer
tracer = create_tracer(enable_console=True)
```

**Q: 如何查看工具调用历史？**

A: 使用工具记录器：
```python
from src.agent import get_tool_recorder
recorder = get_tool_recorder()
print(recorder.export_report(format="markdown"))
```

**Q: 如何测试新技能？**

A: 编写单元测试：
```python
# tests/test_my_skill.py

import pytest
from src.skills.impl.my_skill import MySkill

@pytest.mark.asyncio
async def test_my_skill():
    skill = MySkill()
    result = await skill.execute("测试查询")
    assert result["success"] is True
```
