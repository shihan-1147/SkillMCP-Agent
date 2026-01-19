# 贡献指南

感谢你对 SkillMCP-Agent 的关注！我们欢迎所有形式的贡献。

## 🤝 如何贡献

### 报告问题 (Issues)

如果你发现了 bug 或有新功能建议：

1. 先搜索 [现有 Issues](https://github.com/shihan-1147/SkillMCP-Agent/issues) 避免重复
2. 创建新 Issue，使用合适的模板
3. 提供详细的信息：
   - Bug：系统环境、复现步骤、错误日志
   - 功能：使用场景、期望效果、参考示例

### 提交代码 (Pull Requests)

1. **Fork 仓库**
   ```bash
   # 在 GitHub 上点击 Fork 按钮
   git clone https://github.com/你的用户名/SkillMCP-Agent.git
   cd SkillMCP-Agent
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/bug-description
   ```

3. **开发**
   - 遵循代码规范（见下文）
   - 编写测试用例
   - 更新相关文档
   - 提交信息要清晰

4. **提交**
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   git push origin feature/your-feature-name
   ```

5. **创建 PR**
   - 在 GitHub 上创建 Pull Request
   - 填写 PR 模板
   - 等待 Review

## 📝 代码规范

### Python 代码

遵循 **PEP 8** 规范：

```python
# ✅ 好的示例
def query_weather(city: str) -> Dict[str, Any]:
    """
    查询城市天气
    
    Args:
        city: 城市名称
        
    Returns:
        天气数据字典
    """
    if not city:
        raise ValueError("城市名称不能为空")
    
    return {"city": city, "weather": "晴"}


# ❌ 不好的示例
def QueryWeather(City):
    if not City:
        return None
    return {"city":City,"weather":"晴"}
```

### 命名规范

- **文件名**：小写+下划线 `weather_query.py`
- **类名**：大驼峰 `WeatherQueryTool`
- **函数名**：小写+下划线 `query_weather()`
- **变量名**：小写+下划线 `api_key`
- **常量**：全大写+下划线 `MAX_RETRIES`

### Vue 代码

```vue
<!-- ✅ 好的示例 -->
<template>
  <div class="weather-card">
    <h3>{{ cityName }}</h3>
    <p>{{ temperature }}℃</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const cityName = ref('北京')
const temperature = ref(25)
</script>

<style scoped>
.weather-card {
  padding: 20px;
  border-radius: 8px;
}
</style>
```

### 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/)：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type 类型：**

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

**示例：**

```bash
feat(mcp): 添加 Bing 搜索 MCP 工具

- 实现 BingSearchTool 类
- 添加搜索结果解析
- 集成到 MCP Client

Closes #123
```

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_mcp_client.py

# 带覆盖率
pytest --cov=src tests/
```

### 编写测试

```python
# tests/test_new_feature.py
import pytest
from src.mcp.tools.new_tool import NewTool

def test_new_tool_basic():
    """测试基本功能"""
    tool = NewTool()
    result = tool.execute({"query": "test"})
    assert result["success"] is True

@pytest.mark.asyncio
async def test_new_tool_async():
    """测试异步功能"""
    tool = NewTool()
    result = await tool.execute_async({"query": "test"})
    assert "data" in result
```

## 📚 文档

### 更新文档

如果你的修改影响到了：

- ✅ 添加新功能 → 更新 README.md
- ✅ 修改 API → 更新 API 文档
- ✅ 添加配置项 → 更新 .env.example
- ✅ 修改架构 → 更新架构图

### 文档格式

```markdown
## 功能名称

### 功能说明

简要描述功能的作用。

### 使用方法

\`\`\`python
# 代码示例
from src.module import Feature

feature = Feature()
result = feature.do_something()
\`\`\`

### 配置参数

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| param1 | str | 参数说明 | "default" |
```

## 🏗️ 项目结构

添加新功能时请遵循现有结构：

```
src/
├── mcp/tools/          # MCP 工具放这里
│   └── new_tool.py
├── skills/             # 技能模块放这里
│   └── new_skill/
│       ├── __init__.py
│       ├── SKILL.md
│       └── skill.py
└── api/routes/         # API 路由放这里
    └── new_route.py
```

## 🎯 开发建议

### 优先级

1. **Bug 修复** 优先级最高
2. **性能优化** 其次
3. **新功能** 确保不影响现有功能
4. **文档完善** 随时欢迎

### 最佳实践

- ✅ 小步提交，频繁推送
- ✅ 一个 PR 只做一件事
- ✅ 先写测试，再写代码（TDD）
- ✅ 代码要有注释
- ✅ 保持向后兼容

### 需要帮助？

- 📝 [提出 Issue](https://github.com/shihan-1147/SkillMCP-Agent/issues)
- 💬 [参与讨论](https://github.com/shihan-1147/SkillMCP-Agent/discussions)
- 📧 发邮件给维护者

## 📋 检查清单

提交 PR 前请确认：

- [ ] 代码符合规范
- [ ] 通过所有测试
- [ ] 添加了必要的测试
- [ ] 更新了相关文档
- [ ] 提交信息清晰
- [ ] 没有遗留 debug 代码
- [ ] 没有提交敏感信息

## 🙏 感谢

感谢所有贡献者！你们的付出让这个项目变得更好。

---

**Happy Coding! 🎉**
