# SkillMCP-Agent

<div align="center">

![SkillMCP-Agent Banner](https://img.shields.io/badge/SkillMCP-Agent-brightgreen?style=for-the-badge&logo=robot)

**🤖 基于 MCP 协议的智能 Agent 系统**

支持多技能调度、工具调用与 RAG 增强 | 100% 真实数据 | 零虚拟

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.0+-brightgreen.svg)](https://vuejs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/Protocol-MCP-purple.svg)](https://modelcontextprotocol.io/)
[![GitHub release](https://img.shields.io/github/v/release/shihan-1147/SkillMCP-Agent)](https://github.com/shihan-1147/SkillMCP-Agent/releases)
[![GitHub stars](https://img.shields.io/github/stars/shihan-1147/SkillMCP-Agent?style=social)](https://github.com/shihan-1147/SkillMCP-Agent)

[🚀 快速开始](#-快速开始) | 
[📖 详细文档](#-文档) | 
[🎯 功能特性](#-核心功能) | 
[🗺️ 路线图](ROADMAP.md) | 
[🤝 贡献指南](CONTRIBUTING.md)

</div>

---

## 🎯 项目概述

SkillMCP-Agent 是一个**生产级**的 AI Agent 系统，采用模块化架构设计，实现了：

- 🧠 **智能规划**：多轮对话理解 + 意图识别 + 任务分解
- ⚡ **技能调度**：基于语义匹配的技能选择与执行
- 🔧 **MCP 工具**：遵循 Model Context Protocol 规范的工具调用
- 📚 **RAG 增强**：向量检索增强生成，支持知识库问答
- 🎨 **可视化控制台**：Vue 3 + Element Plus 构建的 Agent Console

### 技术亮点

| 特性 | 说明 |
|------|------|
| **MCP 协议** | 实现标准 MCP Server/Client，支持工具发现与调用 |
| **多模型支持** | 支持 OpenAI、Ollama 本地模型、自定义 LLM |
| **流式响应** | SSE 实时推送 Agent 思考过程与执行状态 |
| **执行追踪** | 完整的执行链路追踪与工具调用记录 |
| **热插拔技能** | 通过装饰器快速注册新技能，无需修改核心代码 |

---

## 🏗 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Vue 3)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ ChatInput   │  │ MessageView │  │ DebugPanel / AgentTrace │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │ HTTP/SSE
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   /chat     │  │  /stream    │  │  /health  /sessions     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Agent Orchestrator                          │
│  ┌──────────┐  ┌──────────────┐  ┌────────────┐  ┌───────────┐  │
│  │ Planner  │→ │ SkillSelector│→ │  Executor  │→ │ Reasoner  │  │
│  └──────────┘  └──────────────┘  └────────────┘  └───────────┘  │
│        ↓              ↓                ↓                        │
│  ┌──────────┐  ┌──────────────┐  ┌────────────┐                 │
│  │  Memory  │  │   Tracer     │  │ ToolRecord │                 │
│  └──────────┘  └──────────────┘  └────────────┘                 │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌─────────────────┐  ┌──────────────┐  ┌──────────────┐
│   Skills Layer  │  │  MCP Client  │  │ RAG Pipeline │
│  ┌───────────┐  │  │              │  │  ┌────────┐  │
│  │ travel    │  │  │   ┌──────┐  │  │  │Embedder│  │
│  │ weather   │  │  │   │Tools │  │  │  │Chunker │  │
│  │ knowledge │  │  │   └──────┘  │  │  │Retriev │  │
│  │ summarize │  │  │              │  │  └────────┘  │
│  └───────────┘  │  └──────────────┘  └──────────────┘
└─────────────────┘          │
                             ▼
                   ┌──────────────────┐
                   │    MCP Server    │
                   │  ┌────────────┐  │
                   │  │train_query │  │
                   │  │weather_api │  │
                   │  │system_time │  │
                   │  │rag_retriev │  │
                   │  └────────────┘  │
                   └──────────────────┘
```

### 核心模块

| 模块 | 职责 | 关键类 |
|------|------|--------|
| **Core** | 基础设施：配置、日志、异常 | `Settings`, `get_logger` |
| **Agent** | 任务规划与执行调度 | `AgentOrchestrator`, `Planner`, `Executor` |
| **Skills** | 业务技能封装 | `BaseSkill`, `SkillRegistry` |
| **MCP** | 工具协议实现 | `MCPServer`, `MCPClient`, `BaseTool` |
| **RAG** | 检索增强生成 | `RAGPipeline`, `Embedder`, `VectorStore` |
| **API** | HTTP 接口层 | `FastAPI`, `ChatService` |

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+ (前端)
- Ollama (本地模型) 或 OpenAI API Key

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/SkillMCP-Agent.git
cd SkillMCP-Agent

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 配置 LLM 参数

# 5. 启动后端
python -m uvicorn src.api.app:app --reload --port 8000

# 6. 启动前端 (新终端)
cd frontend
npm install
npm run dev
```

### 配置说明

```env
# .env 文件

# LLM 配置
LLM_PROVIDER=ollama              # ollama / openai
OLLAMA_MODEL=gemma3:latest       # Ollama 模型名
OLLAMA_EMBEDDING_MODEL=nomic-embed-text:latest

# OpenAI 配置 (可选)
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o-mini

# RAG 配置
RAG_EMBEDDER_TYPE=ollama
EMBEDDING_DIMENSION=768

# 日志
LOG_LEVEL=INFO
```

### 快速验证

```bash
# 健康检查
curl http://localhost:8000/api/v1/health

# 发送消息
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "北京今天天气怎么样？"}'
```

---

## 🔌 扩展指南

### 新增 Skill

技能是业务逻辑的封装单元，通过装饰器注册：

```python
# src/skills/my_skill.py

from src.skills.base import BaseSkill, skill_registry

@skill_registry.register("my_skill")
class MySkill(BaseSkill):
    """我的自定义技能"""
    
    name = "my_skill"
    description = "这是一个自定义技能，用于处理特定任务"
    
    # 技能触发关键词
    keywords = ["关键词1", "关键词2", "特定场景"]
    
    async def execute(self, query: str, context: dict = None) -> dict:
        """
        执行技能逻辑
        
        Args:
            query: 用户输入
            context: 上下文信息（包含历史对话、用户信息等）
        
        Returns:
            dict: 包含 success, data, message 的结果
        """
        # 1. 解析用户意图
        intent = self._parse_intent(query)
        
        # 2. 调用 MCP 工具 (如需要)
        from src.mcp import get_mcp_client
        mcp = get_mcp_client()
        tool_result = await mcp.call_tool("my_tool", {"param": "value"})
        
        # 3. 处理结果
        return {
            "success": True,
            "data": {
                "result": tool_result,
                "processed": self._process(tool_result)
            },
            "message": "处理完成"
        }
    
    def _parse_intent(self, query: str) -> str:
        # 意图解析逻辑
        return "default"
    
    def _process(self, data: dict) -> dict:
        # 数据处理逻辑
        return data
```

### 新增 MCP Tool

MCP 工具是可被 Agent 调用的原子能力：

```python
# src/mcp/tools/my_tool.py

from src.mcp.base import BaseTool, tool_registry

@tool_registry.register("my_tool")
class MyTool(BaseTool):
    """我的 MCP 工具"""
    
    name = "my_tool"
    description = "执行特定操作的工具"
    
    # 参数 Schema (JSON Schema 格式)
    parameters = {
        "type": "object",
        "properties": {
            "param1": {
                "type": "string",
                "description": "参数1说明"
            },
            "param2": {
                "type": "integer",
                "description": "参数2说明",
                "default": 10
            }
        },
        "required": ["param1"]
    }
    
    async def execute(self, **kwargs) -> dict:
        """
        执行工具逻辑
        
        Args:
            **kwargs: 根据 parameters schema 传入的参数
        
        Returns:
            dict: 工具执行结果
        """
        param1 = kwargs.get("param1")
        param2 = kwargs.get("param2", 10)
        
        # 执行具体逻辑
        result = await self._do_something(param1, param2)
        
        return {
            "success": True,
            "data": result
        }
    
    async def _do_something(self, p1: str, p2: int) -> dict:
        # 实际业务逻辑
        return {"processed": f"{p1}-{p2}"}
```

### 新增 RAG 数据源

```python
# 添加文档到 RAG 知识库

from src.rag import get_rag_pipeline

pipeline = get_rag_pipeline()

# 方式1: 从文件加载
await pipeline.load_documents("path/to/documents/")

# 方式2: 直接添加文本
await pipeline.add_texts([
    "这是第一段知识内容...",
    "这是第二段知识内容...",
], metadata=[
    {"source": "manual", "category": "FAQ"},
    {"source": "manual", "category": "Guide"},
])

# 检索验证
results = await pipeline.retrieve("相关问题", top_k=3)
```

---

## 📡 API 文档

### POST /api/v1/chat

发送消息并获取 Agent 响应

**Request:**
```json
{
  "message": "北京明天的天气怎么样？",
  "session_id": "optional-session-id",
  "stream": false
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "response": "北京明天晴，气温 15-25°C，适合出行。",
    "structured": {
      "intent": "weather",
      "skill": "weather_skill",
      "tools_called": ["weather_query"],
      "execution_time_ms": 1234
    }
  },
  "session_id": "sess_abc123",
  "trace_id": "trace_xyz789"
}
```

### GET /api/v1/chat/stream

SSE 流式响应

**Event Types:**
- `thinking`: Agent 思考过程
- `tool_call`: 工具调用事件
- `content`: 响应内容片段
- `done`: 完成信号

### GET /api/v1/health

健康检查

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "llm": "ok",
    "mcp": "ok",
    "rag": "ok"
  }
}
```

---

## 📊 执行追踪

系统内置完整的执行追踪能力：

```python
from src.agent import create_tracer, TraceEventType

# 创建追踪器
tracer = create_tracer()
tracer.start(query="用户查询")

# 追踪规划阶段
with tracer.trace(TraceEventType.PLANNER_START):
    tracer.log_intent("weather")
    tracer.log_plan(["解析城市", "查询天气", "格式化结果"])

# 追踪工具调用
tracer.log_tool_call(
    tool_name="weather_query",
    arguments={"city": "北京"},
    result={"temp": 25},
    duration_ms=150
)

# 获取追踪报告
report = tracer.get_report()
timeline = tracer.get_timeline()
```

**控制台输出示例:**
```
🚀 [agent_start] {"query": "北京天气"}
  🎯 [planner_start]
    💡 [planner_intent] {"intent": "weather"}
    📋 [planner_plan] {"step_count": 3}
  ✓ [planner_end] (15.2ms)
  ⚡ [skill_selected] {"skill": "weather_skill"}
  🔧 [mcp_call_start] {"tool": "weather_query"}
  ✓ [mcp_call_end] (150.3ms)
✅ [agent_end] (320.5ms) {"total_tool_calls": 1}
```

---

## 🧪 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_ollama.py -v

# 测试覆盖率
pytest tests/ --cov=src --cov-report=html
```

---

## 📁 项目结构

```
SkillMCP-Agent/
├── src/
│   ├── core/                # 核心基础设施
│   │   ├── config.py        # 配置管理
│   │   ├── logging.py       # 日志系统
│   │   ├── exceptions.py    # 异常定义
│   │   └── ollama.py        # Ollama 客户端
│   ├── agent/               # Agent 核心
│   │   ├── orchestrator.py  # 编排器
│   │   ├── planner.py       # 规划器
│   │   ├── executor.py      # 执行器
│   │   ├── reasoner.py      # 推理器
│   │   ├── tracer.py        # 执行追踪
│   │   └── tool_recorder.py # 工具记录
│   ├── skills/              # 技能层
│   │   ├── base.py          # 技能基类
│   │   ├── registry.py      # 技能注册表
│   │   └── impl/            # 技能实现
│   ├── mcp/                 # MCP 协议层
│   │   ├── server.py        # MCP 服务端
│   │   ├── client.py        # MCP 客户端
│   │   ├── base.py          # 工具基类
│   │   └── tools/           # 工具实现
│   ├── rag/                 # RAG 子系统
│   │   ├── pipeline.py      # RAG 流水线
│   │   ├── embedder.py      # 向量化
│   │   ├── chunker.py       # 文档切分
│   │   └── retriever.py     # 检索器
│   └── api/                 # API 层
│       ├── app.py           # FastAPI 应用
│       ├── routes/          # 路由
│       └── schemas/         # 数据模型
├── frontend/                # Vue 3 前端
│   ├── src/
│   │   ├── views/           # 页面
│   │   ├── components/      # 组件
│   │   └── api/             # API 调用
│   └── vite.config.js
├── tests/                   # 测试
├── docs/                    # 文档
└── requirements.txt
```

---

## 🛠 技术栈

**后端:**
- Python 3.10+
- FastAPI - 高性能 Web 框架
- Pydantic - 数据验证
- httpx - 异步 HTTP 客户端
- FAISS - 向量存储

**前端:**
- Vue 3 - 响应式框架
- Vite - 构建工具
- Element Plus - UI 组件库
- Pinia - 状态管理

**LLM:**
- Ollama - 本地模型部署
- OpenAI API - 云端模型

---

## 📝 License

MIT License

---

## 🤝 Contributing

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 提交 Pull Request

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐ Star！**

</div>
