# Release v1.0.0 - 首次发布 🎉

## 🌟 亮点

这是 SkillMCP-Agent 的首次正式发布！一个基于 MCP 协议的智能 Agent 系统，支持多技能调度、工具调用与 RAG 增强。

### ✨ 核心特性

#### 🤖 AI 对话系统
- ✅ **Ollama 本地 LLM 集成**：使用 qwen3:latest 模型，无需 API Key
- ✅ **智能意图识别**：自动识别用户意图并路由到对应技能
- ✅ **多轮对话支持**：保持上下文，支持连续对话
- ✅ **流式响应**：实时输出，提升用户体验

#### 🔧 MCP 工具系统
- ✅ **标准 MCP 协议**：遵循 Model Context Protocol 规范
- ✅ **真实 12306 查询**：通过 12306-mcp 获取真实火车票数据
- ✅ **真实天气查询**：通过高德地图 API 获取实时天气
- ✅ **支持多种传输**：stdio、SSE、HTTP 三种方式

#### 📚 RAG 知识库
- ✅ **向量检索**：基于 FAISS 的高效检索
- ✅ **文档问答**：支持 Markdown、PDF、TXT 等格式
- ✅ **语义分块**：智能文档切分，提高检索准确度
- ✅ **本地 Embedding**：使用 Ollama 进行向量化

#### 🎨 现代化界面
- ✅ **Vue 3 前端**：使用 Element Plus 组件库
- ✅ **实时对话**：流式输出，即时反馈
- ✅ **调试面板**：可视化 Agent 思考过程
- ✅ **结构化展示**：天气、车票等数据卡片化展示

## 📦 包含的功能

### 后端服务 (FastAPI)

```
src/
├── api/              # API 路由与服务
├── core/             # 核心配置与日志
├── mcp/              # MCP 客户端与工具
│   ├── client.py    # MCP 客户端
│   └── tools/       # 内置工具
│       ├── train_query.py    # 12306 查询
│       ├── weather_query.py  # 天气查询
│       └── rag_retriever.py  # RAG 检索
├── rag/              # RAG 检索增强
└── skills/           # 技能模块
```

### 前端界面 (Vue 3)

```
frontend/
├── src/
│   ├── components/   # 组件
│   │   ├── chat/    # 对话组件
│   │   └── debug/   # 调试组件
│   ├── views/        # 页面
│   └── stores/       # 状态管理
```

## 📖 文档

- 📘 [README.md](README.md) - 项目介绍与快速开始
- 📗 [QUICKSTART.md](QUICKSTART.md) - 5分钟上手指南
- 📙 [MCP调用原理-小学生版](docs/MCP调用原理-小学生版.md) - 详细教程
- 📕 [模型切换总结](docs/模型切换总结.md) - 模型配置指南
- 📓 [CONTRIBUTING.md](CONTRIBUTING.md) - 贡献指南
- 📔 [ROADMAP.md](ROADMAP.md) - 项目路线图

## 🚀 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/shihan-1147/SkillMCP-Agent.git
cd SkillMCP-Agent
```

### 2. 安装依赖
```bash
# 后端
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 3. 配置环境
```bash
cp .env.example .env
# 编辑 .env 文件，设置 AMAP_API_KEY
```

### 4. 启动 Ollama
```bash
ollama pull qwen3:latest
ollama pull qwen3-embedding:latest
```

### 5. 运行服务
```bash
# 后端（终端1）
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload

# 前端（终端2）
cd frontend
npm run dev
```

### 6. 访问应用
打开浏览器访问：http://localhost:3000

## 📊 技术栈

### 后端
- Python 3.10+
- FastAPI 0.100+
- Pydantic 2.0+
- httpx (异步 HTTP)
- mcp (MCP SDK)

### 前端
- Vue 3
- Element Plus
- Pinia (状态管理)
- Vue Router
- Vite (构建工具)

### AI & 数据
- Ollama (本地 LLM)
- FAISS (向量检索)
- 高德地图 API (天气)
- 12306-mcp (火车票)

## ⚙️ 系统要求

- **操作系统**：Windows 10+, macOS 12+, Ubuntu 20.04+
- **Python**：3.10 或更高版本
- **Node.js**：18.0 或更高版本
- **内存**：建议 8GB+
- **磁盘**：建议 10GB+ (包含模型文件)

## 🔧 配置说明

### 环境变量 (.env)

```env
# LLM 配置
OLLAMA_MODEL=qwen3:latest
OLLAMA_BASE_URL=http://localhost:11434

# 天气 API
AMAP_API_KEY=your_api_key_here

# 服务配置
API_HOST=127.0.0.1
API_PORT=8000
```

### MCP 配置 (mcp_config.json)

```json
{
  "12306-mcp": {
    "transport": "stdio",
    "command": "npx",
    "args": ["-y", "12306-mcp"],
    "enabled": true
  }
}
```

## 🐛 已知问题

- Windows 系统下某些路径可能需要使用绝对路径
- 首次启动时加载模型较慢，属正常现象
- 部分防火墙可能阻止本地端口访问

## 🔮 未来计划

查看 [ROADMAP.md](ROADMAP.md) 了解详细的开发计划。

近期重点：
- 多模型切换支持
- 更多 MCP 工具集成
- 暗色模式
- Docker 部署支持

## 🤝 贡献

欢迎贡献！请阅读 [贡献指南](CONTRIBUTING.md)。

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

## 🙏 致谢

感谢以下项目：
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Ollama](https://ollama.ai/)
- [12306-mcp](https://www.npmjs.com/package/12306-mcp)
- [高德地图开放平台](https://lbs.amap.com/)

---

**完整更新日志请查看 [CHANGELOG.md](CHANGELOG.md)**

如有问题，请提交 [Issue](https://github.com/shihan-1147/SkillMCP-Agent/issues) 或参与 [讨论](https://github.com/shihan-1147/SkillMCP-Agent/discussions)。

⭐ 如果这个项目对你有帮助，请给个 Star！
