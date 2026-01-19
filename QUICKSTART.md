# SkillMCP-Agent

基于 MCP 协议的智能 Agent 系统

## Quick Start

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env

# 启动后端
python -m uvicorn src.api.app:app --reload

# 启动前端 (新终端)
cd frontend && npm install && npm run dev
```

## Documentation

- [README.md](README.md) - 项目文档
- [docs/EXTENSION_GUIDE.md](docs/EXTENSION_GUIDE.md) - 扩展开发指南
- [CHANGELOG.md](CHANGELOG.md) - 更新日志

## License

MIT
