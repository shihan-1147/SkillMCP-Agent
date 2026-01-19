# 🎓 MCP 调用原理 - 小学生都能懂的版本

## 📚 第一章：什么是 MCP？

### 🌰 用一个故事来理解

想象你在肯德基点餐：

1. **你（前端）**: "我要一个汉堡！"
2. **收银员（后端）**: "好的，我去厨房问问。"
3. **厨房（MCP Server）**: "汉堡做好了，给你！"
4. **收银员**: "您的汉堡，请慢用。"

**MCP 就是这个"收银员和厨房的对话规则"！**

```
前端用户                后端系统              MCP Server (12306)
   │                      │                       │
   │─── 查火车票 ───────>│                       │
   │                      │                       │
   │                      │── 调用 MCP 工具 ───> │
   │                      │                       │
   │                      │<── 返回真实数据 ───  │
   │                      │                       │
   │<─── 显示车票 ────── │                       │
```

---

## 🧩 第二章：系统里用到的"零件"（包和工具）

### 📦 核心包（就像乐高积木）

#### 1. **mcp** - MCP 官方 Python SDK
```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
```

**作用**: 
- `ClientSession` → 建立和 MCP Server 的连接（就像打电话）
- `StdioServerParameters` → 设置连接参数（就像拨号码）
- `stdio_client` → 通过"标准输入输出"连接（就像用对讲机说话）

#### 2. **asyncio** - 异步编程
```python
import asyncio
```

**作用**: 让程序可以"同时做多件事"
- 就像你一边听音乐，一边写作业
- 程序可以一边查火车票，一边查天气

#### 3. **httpx** - HTTP 请求库
```python
import httpx
```

**作用**: 向网站发送请求获取数据
- 就像你给朋友发微信
- 程序给 API 发请求

---

## 🎯 第三章：调用 MCP 的完整流程

### 步骤一：启动 MCP Server（开店）

```json
// mcp_config.json - 配置文件
{
  "12306-mcp": {
    "transport": "stdio",      // 通信方式：标准输入输出
    "command": "npx",          // 启动命令
    "args": ["-y", "12306-mcp"],  // 命令参数
    "enabled": true            // 是否启用
  }
}
```

**用人话说**:
- 告诉系统："用 `npx -y 12306-mcp` 这个命令启动 12306 查询工具"
- `stdio` 就像用"对讲机"和它说话

---

### 步骤二：建立连接（拨号）

```python
# src/mcp/mcp_client.py

# 1️⃣ 设置参数（准备拨号）
server_params = StdioServerParameters(
    command="npx",              # 📞 用什么拨号
    args=["-y", "12306-mcp"]    # 📞 拨什么号码
)

# 2️⃣ 建立连接（拨通电话）
stdio_transport = await stdio_client(server_params)
read_stream, write_stream = stdio_transport  # 📞 通话通道

# 3️⃣ 创建会话（开始对话）
session = ClientSession(read_stream, write_stream)
await session.initialize()  # 📞 "喂，你好！"
```

**打个比方**:
- `stdio_client` = 拨号器
- `read_stream` = 你的耳朵（听对方说话）
- `write_stream` = 你的嘴巴（对对方说话）
- `session` = 一次完整的通话

---

### 步骤三：查询可用工具（看菜单）

```python
# 获取工具列表
tools_resp = await session.list_tools()

# 工具列表示例
[
  {
    "name": "get-tickets",           # 查询火车票
    "description": "查询12306余票",   
    "input_schema": {...}            # 需要什么参数
  },
  {
    "name": "get-current-date",      # 获取当前日期
    "description": "获取当前日期",
    "input_schema": {...}
  }
]
```

**就像**:
- 你拿到了肯德基的菜单
- 知道有"汉堡、薯条、可乐"可以点

---

### 步骤四：调用工具（点餐）

```python
# src/mcp/mcp_client.py - call_tool 方法

async def call_tool(
    self,
    server_name: str,      # 哪个店？（12306-mcp）
    tool_name: str,        # 点什么？（get-tickets）
    arguments: Dict        # 怎么做？（北京→上海）
) -> Dict:
    """调用 MCP 工具"""
    
    # 1️⃣ 获取会话（找到店员）
    session = self._sessions.get(server_name)
    
    # 2️⃣ 调用工具（下单）
    result = await session.call_tool(tool_name, arguments)
    
    # 3️⃣ 解析结果（拿到餐品）
    text_content = []
    for item in result.content:
        if hasattr(item, 'text'):
            text_content.append(item.text)
    
    return {
        "success": True,
        "data": "\n".join(text_content)  # 火车票信息
    }
```

**实际使用**:
```python
# 查询火车票
result = await mcp.call_tool(
    "12306-mcp",           # 哪个店：12306
    "get-tickets",         # 点什么：查票
    {
        "date": "2026-01-20",
        "fromStation": "BJP",   # 北京
        "toStation": "SHH",     # 上海
        "trainFilterFlags": "G" # 只要高铁
    }
)

# 返回结果
"""
G103 北京南 → 上海虹桥 06:20-11:58 历时05:38
  商务座: 8张 1873元
  一等座: 有票 930元
  二等座: 有票 553元
"""
```

---

## 🔧 第四章：使用的技巧

### 技巧 1: 使用上下文管理器（自动清理）

```python
# AsyncExitStack - 就像"自动关门器"
self.exit_stack = AsyncExitStack()

# 进入时自动连接
stdio_transport = await self.exit_stack.enter_async_context(
    stdio_client(server_params)
)

# 退出时自动断开（不用手动关闭）
await self.exit_stack.aclose()
```

**好处**:
- 就像电梯门，进去自动开，出来自动关
- 防止"忘记关门"导致资源泄漏

---

### 技巧 2: 缓存站点代码（快速查询）

```python
# 城市 → 站点代码映射表
CITY_STATION_CODES = {
    "北京": "BJP",
    "上海": "SHH",
    "广州": "GZQ",
    ...
}

# 快速查询
origin_code = self.CITY_STATION_CODES.get("北京")  # 直接得到 "BJP"
```

**好处**:
- 不用每次都问 MCP "北京的代码是什么？"
- 就像你记住了好朋友的电话号码

---

### 技巧 3: 错误处理（防止崩溃）

```python
try:
    # 尝试调用 MCP
    result = await session.call_tool(tool_name, arguments)
    return {"success": True, "data": result}
    
except Exception as e:
    # 出错了也不崩溃
    logger.error(f"调用失败: {e}")
    return {
        "success": False,
        "error": "查询失败，请稍后重试"
    }
```

**好处**:
- 就像骑自行车摔倒了，爬起来继续骑
- 程序不会因为一个错误就整个停止

---

### 技巧 4: 数据解析（整理数据）

```python
def _parse_mcp_train_data(self, raw_data: str) -> List[Dict]:
    """把文本数据变成结构化数据"""
    
    # 原始数据（文本）
    """
    G103 北京南 → 上海虹桥 06:20-11:58
      商务座: 8张 1873元
    """
    
    # 解析后（字典）
    {
        "train_no": "G103",
        "origin_station": "北京南",
        "departure_time": "06:20",
        "arrival_time": "11:58",
        "seats": {
            "商务座": "8张 1873元"
        }
    }
```

**好处**:
- 把"一大段话"变成"整齐的表格"
- 前端更容易显示

---

## 🌟 第五章：完整的调用示例

### 场景：用户查询"明天从北京到上海的高铁"

```python
# 1️⃣ 前端发送请求
POST http://localhost:8000/api/v1/chat
{
  "message": "帮我查询明天从北京到上海的高铁票",
  "session_id": "user123"
}

# 2️⃣ 后端识别意图（ChatService）
意图: 查询火车票
参数: {
  "origin": "北京",
  "destination": "上海", 
  "date": "2026-01-20"
}

# 3️⃣ 调用 TrainQueryTool
tool = TrainQueryTool()
result = await tool.execute({
    "action": "query_tickets",
    "origin": "北京",
    "destination": "上海",
    "date": "2026-01-20"
})

# 4️⃣ TrainQueryTool 调用 MCP Client
mcp = get_mcp_client_manager()

# 4.1 先获取站点代码
code_result = await mcp.call_tool(
    "12306-mcp",
    "get-station-code-of-citys",
    {"citys": "北京|上海"}
)
# 返回: {"北京": {"station_code": "BJP"}, "上海": {"station_code": "SHH"}}

# 4.2 查询火车票
ticket_result = await mcp.call_tool(
    "12306-mcp",
    "get-tickets",
    {
        "date": "2026-01-20",
        "fromStation": "BJP",
        "toStation": "SHH",
        "trainFilterFlags": "G",
        "limitedNum": 10,
        "format": "text"
    }
)

# 5️⃣ 返回给前端
{
  "status": "success",
  "reply": "🚄 找到 10 趟高铁...",
  "structured_data": [
    {
      "type": "train",
      "data": {
        "trains": [
          {
            "train_no": "G103",
            "departure_time": "06:20",
            ...
          }
        ]
      }
    }
  ]
}
```

---

## 🎨 第六章：架构图（大白话版）

```
┌─────────────────────────────────────────────────────────┐
│                    你的系统                              │
│                                                          │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐      │
│  │          │      │          │      │          │      │
│  │  前端    │─────>│  后端    │─────>│   MCP    │      │
│  │ (Vue 3)  │      │ (FastAPI)│      │  Client  │      │
│  │          │      │          │      │          │      │
│  └──────────┘      └──────────┘      └─────┬────┘      │
│                                            │            │
└────────────────────────────────────────────┼────────────┘
                                             │
                            通过 stdio 连接  │
                                             ↓
                               ┌──────────────────────┐
                               │   MCP Server         │
                               │   (12306-mcp)        │
                               │                      │
                               │  运行在 Node.js 上   │
                               │  使用 npx 启动       │
                               └──────────────────────┘
                                             │
                                             ↓
                               ┌──────────────────────┐
                               │  12306 官方网站      │
                               │  (真实数据源)        │
                               └──────────────────────┘
```

---

## 📝 第七章：关键代码位置

### 1️⃣ MCP 客户端管理器
**文件**: `src/mcp/mcp_client.py`
- **MCPClientManager** 类：管理所有 MCP 连接
- `initialize()`: 启动时连接 MCP Server
- `call_tool()`: 调用 MCP 工具

### 2️⃣ MCP 配置文件
**文件**: `mcp_config.json`
```json
{
  "12306-mcp": {
    "transport": "stdio",
    "command": "npx",
    "args": ["-y", "12306-mcp"]
  }
}
```

### 3️⃣ 火车票查询工具
**文件**: `src/mcp/tools/train_query.py`
- **TrainQueryTool** 类：封装 12306 查询逻辑
- `_query_tickets_via_mcp()`: 通过 MCP 查询
- `_parse_mcp_train_data()`: 解析返回数据

### 4️⃣ 应用启动
**文件**: `src/api/app.py`
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    await initialize_mcp_client()  # 连接 MCP
    yield
    # 关闭时
    mcp = get_mcp_client_manager()
    await mcp.close()  # 断开 MCP
```

---

## 🎯 第八章：核心概念总结

### MCP 的三个关键词

1. **Transport（传输方式）**
   - `stdio` = 标准输入输出（对讲机）
   - `sse` = 服务器推送事件（实时通知）
   - `http` = HTTP 请求（发邮件）

2. **Session（会话）**
   - 就像打电话的一次通话
   - 保持连接状态
   - 可以多次交流

3. **Tool（工具）**
   - MCP Server 提供的功能
   - 就像菜单上的菜品
   - 需要传入参数才能执行

---

## 🔬 第九章：实际数据流动

### 查询"北京到上海"的数据流

```python
# 步骤 1: 用户输入
"帮我查询明天从北京到上海的高铁票"

# 步骤 2: 后端识别
意图: train_query
参数: {"origin": "北京", "destination": "上海", "date": "2026-01-20"}

# 步骤 3: 获取站点代码
MCP 调用: get-station-code-of-citys
参数: {"citys": "北京|上海"}
返回: {"北京": {"station_code": "BJP"}, "上海": {"station_code": "SHH"}}

# 步骤 4: 查询火车票
MCP 调用: get-tickets
参数: {
  "date": "2026-01-20",
  "fromStation": "BJP",
  "toStation": "SHH",
  "trainFilterFlags": "G",
  "limitedNum": 10
}
返回: "G103 北京南 → 上海虹桥 06:20-11:58\n  商务座: 8张 1873元\n..."

# 步骤 5: 解析数据
原始文本 → 结构化 JSON
{
  "trains": [
    {
      "train_no": "G103",
      "origin_station": "北京南",
      "destination_station": "上海虹桥",
      "departure_time": "06:20",
      "arrival_time": "11:58",
      "duration": "05:38",
      "seats": {
        "商务座": "8张 1873元",
        "一等座": "有票 930元",
        "二等座": "有票 553元"
      }
    },
    ...
  ]
}

# 步骤 6: 返回前端
{
  "reply": "🚄 北京 → 上海 (2026-01-20)\n共找到 10 个车次...",
  "structured_data": [...]
}
```

---

## 💡 第十章：为什么这样设计？

### 问：为什么不直接调用 12306 官网？
**答**: 
- ❌ 12306 有反爬虫机制
- ❌ 需要处理验证码、登录等
- ✅ 使用 MCP Server，别人已经处理好了这些问题
- ✅ 我们只需要"点菜"，不需要"做菜"

### 问：为什么用 stdio 而不是 HTTP？
**答**:
- ✅ stdio 更简单（像打电话）
- ✅ 都在本地运行，不需要网络
- ✅ 启动就连接，不需要额外配置
- ❌ HTTP 需要启动一个服务器，更复杂

### 问：为什么要缓存站点代码？
**答**:
- ✅ 常用城市代码固定不变
- ✅ 减少 MCP 调用次数（省钱省时间）
- ✅ 查询更快（不用每次都问）

---

## 🎓 小结

### 核心流程（5 步走）

1. **启动**: 系统启动时连接 MCP Server
2. **准备**: 查看 MCP 提供了哪些工具
3. **调用**: 把参数传给 MCP，让它帮我们查询
4. **解析**: 把 MCP 返回的数据整理好
5. **返回**: 显示给用户

### 关键技术

- ✅ **mcp SDK**: 官方工具，负责通信
- ✅ **asyncio**: 异步编程，提高效率
- ✅ **stdio**: 标准输入输出，简单可靠
- ✅ **缓存**: 常用数据本地存储，加快速度
- ✅ **错误处理**: 出错不崩溃，用户体验好

### 为什么这么做？

- 🎯 **不重复造轮子**: 别人做好的工具直接用
- 🎯 **模块化设计**: 每个部分职责清晰
- 🎯 **易于维护**: 12306 规则变了，只需要更新 MCP Server
- 🎯 **可扩展**: 想加高德地图？再加一个 MCP Server 就行

---

**恭喜你！现在你已经完全理解了 MCP 的调用原理！🎉**

如果你是小学生，可以这样记：
> MCP 就像外卖平台，
> 我们是顾客（后端），
> 12306-mcp 是餐厅（MCP Server），
> stdio 是外卖员（传输方式），
> 我们点餐（调用工具），
> 餐厅做菜（查询数据），
> 外卖员送餐（返回结果），
> 我们吃饭（显示数据）！🍔
