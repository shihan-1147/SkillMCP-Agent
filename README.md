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

[🚀 快速开始](#-快速开始) | [📖 详细文档](#-文档) | [🎯 功能特性](#-核心功能) | [🤝 贡献指南](#-贡献)

</div>

---

## 🌟 项目亮点

### ✨ 为什么选择 SkillMCP-Agent？

- 🎯 **真实数据，零虚拟**
  - 真实 12306 火车票查询（通过官方 MCP Server）
  - 真实高德地图天气查询（实时 API）
  - 拒绝虚假数据，所有信息来自可靠数据源

- 🔧 **标准 MCP 协议**
  - 遵循 Model Context Protocol 规范
  - 轻松集成第三方 MCP Server
  - 支持 stdio、SSE、HTTP 三种传输方式

- 🧠 **本地化 AI**
  - 使用 Ollama 本地部署（无需 API Key）
  - 支持 qwen3、gemma3、llama3 等多种模型
  - 数据隐私完全可控

- 🎨 **现代化界面**
  - Vue 3 + Element Plus
  - 实时对话流式输出
  - 调试面板可视化 Agent 思考过程

---

## 🎯 核心功能

### 1️⃣ 智能对话

```
用户：明天从北京到上海的高铁票有哪些？

AI：  🚄 北京 → 上海 (2026-01-20)
     共找到 10 个车次：
     
     • G103 (高铁)
       06:20 → 11:58 (05:38)
       商务座: 8张 1873元
       一等座: 有票 930元
       二等座: 有票 553元
```

### 2️⃣ 天气查询

```
用户：北京今天天气怎么样？

AI：  🌤️ 北京当前天气阴 ☁️
     温度：-9℃
     风力：西风 ≤3级
     湿度：19%
     
     💡 气温较低，请注意保暖，穿厚外套
```

### 3️⃣ 知识问答

```
用户：什么是 MCP 协议？

AI：  MCP (Model Context Protocol) 是一个标准协议，
     用于 AI 应用与外部工具的交互。它定义了：
     - 工具发现机制
     - 参数传递规范
     - 结果返回格式
     
     📚 数据来源：项目文档 RAG 检索
```

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                      前端 (Vue 3)                            │
│   🎨 Element Plus UI + 🔄 Pinia 状态管理                      │
└───────────────────────┬─────────────────────────────────────┘
                        │ HTTP / SSE
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                   后端 (FastAPI)                             │
│   📡 RESTful API + 🌊 流式响应 + 📊 会话管理                  │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ↓               ↓               ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Ollama LLM  │ │  MCP Client  │ │ RAG Pipeline │
│              │ │              │ │              │
│ qwen3:latest │ │  12306-mcp   │ │  向量检索    │
│              │ │  amap-mcp    │ │  文档问答    │
└──────────────┘ └──────────────┘ └──────────────┘
```

---

## 🚀 快速开始

### 📋 系统要求

- Python 3.10+
- Node.js 18+
- Ollama（用于本地 LLM）

### 1️⃣ 克隆项目

```bash
git clone https://github.com/shihan-1147/SkillMCP-Agent.git
cd SkillMCP-Agent
```

### 2️⃣ 安装依赖

**后端：**
```bash
pip install -r requirements.txt
```

**前端：**
```bash
cd frontend
npm install
```

### 3️⃣ 配置环境

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
# 设置 AMAP_API_KEY（高德地图 API，免费申请：https://lbs.amap.com/）
```

### 4️⃣ 安装 Ollama 模型

```bash
# 安装 Ollama (https://ollama.ai/)
# Windows: 下载安装包
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.ai/install.sh | sh

# 拉取模型
ollama pull qwen3:latest
ollama pull qwen3-embedding:latest
```

### 5️⃣ 启动服务

**终端 1 - 后端：**
```bash
python -m uvicorn src.api.app:app --host 127.0.0.1 --port 8000 --reload
```

**终端 2 - 前端：**
```bash
cd frontend
npm run dev
```

### 6️⃣ 访问应用

打开浏览器访问：http://localhost:3000

---

## 📖 文档

| 文档 | 说明 |
|------|------|
| [快速开始](QUICKSTART.md) | 5分钟上手指南 |
| [MCP调用原理](docs/MCP调用原理-小学生版.md) | 小学生都能懂的教程 |
| [扩展指南](docs/EXTENSION_GUIDE.md) | 如何添加新功能 |
| [模型切换](docs/模型切换总结.md) | 如何切换不同的 LLM |
| [GitHub发布](docs/GitHub发布指南.md) | 项目发布流程 |

---

## 🎨 功能截图

### 对话界面
![Chat Interface](https://via.placeholder.com/800x500?text=Chat+Interface)

### 调试面板
![Debug Panel](https://via.placeholder.com/800x500?text=Debug+Panel)

---

## 🔧 使用的技术

### 后端技术栈

| 技术 | 用途 |
|------|------|
| **FastAPI** | Web 框架 |
| **Pydantic** | 数据验证 |
| **httpx** | HTTP 客户端 |
| **mcp** | MCP 协议 SDK |
| **Ollama** | 本地 LLM |
| **FAISS** | 向量检索 |

### 前端技术栈

| 技术 | 用途 |
|------|------|
| **Vue 3** | 前端框架 |
| **Element Plus** | UI 组件库 |
| **Pinia** | 状态管理 |
| **Vue Router** | 路由管理 |
| **Vite** | 构建工具 |

---

## 📦 项目结构

```
SkillMCP-Agent/
├── 📁 src/                    # 后端源码
│   ├── api/                  # FastAPI 接口
│   ├── core/                 # 核心模块（配置、日志）
│   ├── mcp/                  # MCP 客户端与工具
│   ├── rag/                  # RAG 检索增强
│   └── skills/               # 技能模块
├── 📁 frontend/               # 前端源码
│   ├── src/
│   │   ├── components/       # Vue 组件
│   │   ├── views/            # 页面视图
│   │   └── stores/           # Pinia 状态
│   └── public/
├── 📁 tests/                  # 测试文件
├── 📁 docs/                   # 文档
├── 📄 .env.example           # 配置模板
├── 📄 requirements.txt       # Python 依赖
└── 📄 README.md              # 本文件
```

---

## 🤝 贡献

欢迎贡献代码！

### 贡献方式

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 开发指南

- 遵循 PEP 8 代码规范
- 添加必要的注释和文档
- 编写测试用例
- 更新 CHANGELOG.md

---

## 🐛 问题反馈

遇到问题？请：

1. 查看 [Issues](https://github.com/shihan-1147/SkillMCP-Agent/issues)
2. 提交新的 Issue（包含详细的错误信息）
3. 加入讨论 [Discussions](https://github.com/shihan-1147/SkillMCP-Agent/discussions)

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源协议。

---

## 🙏 致谢

- [Model Context Protocol](https://modelcontextprotocol.io/) - MCP 协议规范
- [Ollama](https://ollama.ai/) - 本地 LLM 运行时
- [12306-mcp](https://www.npmjs.com/package/12306-mcp) - 火车票查询 MCP Server
- [高德地图开放平台](https://lbs.amap.com/) - 天气 API

---

## 📞 联系方式

- GitHub: [@shihan-1147](https://github.com/shihan-1147)
- Email: [你的邮箱]
- 博客: [你的博客]

---

<div align="center">

**如果这个项目对你有帮助，请给个 ⭐ Star！**

Made with ❤️ by [shihan-1147](https://github.com/shihan-1147)

</div>
