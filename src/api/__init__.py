"""
API 模块

提供 FastAPI 后端接口

架构:
- app.py: FastAPI 应用实例
- routes/: 路由模块
- schemas/: 请求响应模型
- deps.py: 依赖注入
- middleware.py: 中间件

使用示例:
```python
from src.api import create_app

app = create_app()
# uvicorn src.api:app --reload
```
"""

from .app import create_app, get_app

__all__ = ["create_app", "get_app"]
