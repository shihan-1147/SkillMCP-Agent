# SkillMCP Agent Console - 前端

Agent 可视化调试与交互控制台

## 📁 目录结构

```
frontend/
├── index.html                    # HTML 入口
├── package.json                  # 项目依赖
├── vite.config.js                # Vite 配置
└── src/
    ├── main.js                   # 应用入口
    ├── App.vue                   # 根组件
    ├── api/
    │   └── index.js              # API 服务层（与后端通信的唯一入口）
    ├── router/
    │   └── index.js              # 路由配置
    ├── stores/
    │   └── chat.js               # Pinia 状态管理
    ├── styles/
    │   ├── variables.scss        # 样式变量
    │   └── main.scss             # 全局样式
    ├── views/
    │   ├── ConsoleView.vue       # 主控制台页面
    │   └── DebugView.vue         # 调试页面
    └── components/
        ├── chat/
        │   ├── MessageBubble.vue # 消息气泡
        │   ├── ChatInput.vue     # 聊天输入框
        │   └── StructuredCard.vue# 结构化数据卡片
        └── debug/
            ├── AgentProgress.vue # Agent 执行进度
            └── DebugPanel.vue    # 调试面板
```

## 🎨 核心组件说明

### 页面组件

| 组件 | 功能 |
|------|------|
| `ConsoleView.vue` | 主控制台，包含聊天区域和调试面板 |
| `DebugView.vue` | 独立调试页面（扩展用） |

### 聊天组件

| 组件 | 功能 |
|------|------|
| `MessageBubble.vue` | 消息气泡，支持 Markdown 渲染和结构化数据展示 |
| `ChatInput.vue` | 聊天输入框，支持 Enter 发送和 Shift+Enter 换行 |
| `StructuredCard.vue` | 结构化数据卡片（天气、火车票、知识等） |

### 调试组件

| 组件 | 功能 |
|------|------|
| `AgentProgress.vue` | Agent 执行进度指示器 |
| `DebugPanel.vue` | 调试面板，展示执行步骤、结构化数据、RAG 来源等 |

## 🔗 后端接口对齐

### 请求格式 (ChatRequest)

```typescript
interface ChatRequest {
  message: string       // 用户消息
  session_id?: string   // 会话 ID（可选，支持多轮对话）
  stream?: boolean      // 是否流式响应
}
```

### 响应格式 (ChatResponse)

```typescript
interface ChatResponse {
  status: 'success' | 'error'
  message: string
  reply: string                    // 自然语言回答
  session_id: string               // 会话 ID
  structured_data?: StructuredData[] // 结构化数据
  sources?: string[]               // RAG 来源
  debug_info?: object              // 调试信息
}

interface StructuredData {
  type: 'weather' | 'train' | 'knowledge' | string
  data: object
}
```

### API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/chat` | 发送消息 |
| POST | `/api/v1/chat/stream` | 流式响应 |
| GET | `/api/v1/chat/session/{id}` | 获取会话信息 |
| DELETE | `/api/v1/chat/session/{id}` | 删除会话 |
| GET | `/api/v1/health` | 健康检查 |

## 🚀 快速开始

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问 http://localhost:3000

## ⚠️ 架构约束

> 前端只负责：**输入、展示、调试**
> 
> 前端**不参与**任何 Agent 决策逻辑

- ✅ 前端只能调用后端 API
- ❌ 前端不得直接访问 MCP
- ❌ 前端不得直接访问向量库
- ❌ 前端不得直接调用 LLM

所有智能决策由后端 Agent 完成，前端仅负责可视化展示。

## 🎯 功能特性

1. **聊天输入区**
   - 输入用户问题
   - 发送到后端 /chat 接口
   - 支持快捷操作

2. **Agent 执行流程展示**
   - 任务规划（Planner 输出）
   - Skills 调用顺序
   - MCP 工具调用参数与结果（可折叠）
   - RAG 命中内容展示

3. **最终结果展示**
   - 自然语言回答（Markdown 渲染）
   - 结构化展示（天气卡片、火车票卡片等）
   - 来源标签

4. **调试面板**
   - 执行步骤追踪
   - 结构化数据查看
   - RAG 来源展示
   - 会话信息
