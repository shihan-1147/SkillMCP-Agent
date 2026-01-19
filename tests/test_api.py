"""
API 接口测试
"""
import asyncio
import sys
from pathlib import Path

# 确保路径正确
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_api():
    """测试 API 模块"""
    print("=" * 60)
    print("🧪 Testing API Module")
    print("=" * 60)
    
    # 1. 测试配置
    print("\n📋 Test 1: Configuration")
    from src.core.config import get_settings
    settings = get_settings()
    print(f"  ✅ Project Name: {settings.project_name}")
    print(f"  ✅ Version: {settings.version}")
    print(f"  ✅ API Host: {settings.api_host}:{settings.api_port}")
    
    # 2. 测试 Schema
    print("\n📋 Test 2: API Schemas")
    from src.api.schemas import (
        ChatRequest, ChatResponse, StructuredData, 
        ResponseStatus, SessionInfo
    )
    
    request = ChatRequest(message="北京天气", session_id="test-123")
    print(f"  ✅ ChatRequest: message={request.message}, session={request.session_id}")
    
    response = ChatResponse(
        status=ResponseStatus.SUCCESS,
        message="OK",
        reply="北京今天天气晴朗",
        session_id="test-123",
        structured_data=[
            StructuredData(type="weather", data={"city": "北京", "temp": 25})
        ]
    )
    print(f"  ✅ ChatResponse: status={response.status}, reply={response.reply[:20]}...")
    
    # 3. 测试 Session Manager
    print("\n📋 Test 3: Session Manager")
    from src.api.session import get_session_manager
    
    session_manager = get_session_manager()
    session = await session_manager.get_or_create("test-session-001")
    print(f"  ✅ Created session: {session.session_id}")
    
    session.add_message("user", "Hello")
    session.add_message("assistant", "Hi there!")
    print(f"  ✅ Added messages: {len(session.messages)} messages")
    
    history = session.get_history_for_llm()
    print(f"  ✅ History for LLM: {len(history)} items")
    
    stats = session_manager.get_stats()
    print(f"  ✅ Session stats: {stats}")
    
    # 4. 测试 Chat Service
    print("\n📋 Test 4: Chat Service")
    from src.api.chat_service import get_chat_service
    
    chat_service = get_chat_service()
    
    # 测试意图分析
    intent = chat_service._analyze_intent("北京今天天气怎么样？")
    print(f"  ✅ Intent analysis (weather): {intent}")
    
    intent = chat_service._analyze_intent("北京到上海的火车")
    print(f"  ✅ Intent analysis (train): {intent}")
    
    intent = chat_service._analyze_intent("什么是 Agent？")
    print(f"  ✅ Intent analysis (knowledge): {intent}")
    
    # 测试城市提取
    city = chat_service._extract_city("杭州明天天气")
    print(f"  ✅ City extraction: {city}")
    
    # 测试路线提取
    origin, dest = chat_service._extract_route("北京到上海的高铁")
    print(f"  ✅ Route extraction: {origin} → {dest}")
    
    # 5. 测试 FastAPI App
    print("\n📋 Test 5: FastAPI App Creation")
    from src.api.app import create_app
    
    app = create_app()
    print(f"  ✅ App created: {app.title}")
    print(f"  ✅ Routes count: {len(app.routes)}")
    
    # 列出所有路由
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            print(f"     - {route.methods} {route.path}")
    
    # 6. 测试 Chat 流程（不需要真实服务）
    print("\n📋 Test 6: Chat Flow (Mock)")
    
    # 使用通用处理器测试
    reply = await chat_service._handle_general(
        "你好",
        []
    )
    print(f"  ✅ General handler: {reply[:50]}...")
    
    # 清理
    await session_manager.delete("test-session-001")
    print(f"  ✅ Cleanup: session deleted")
    
    print("\n" + "=" * 60)
    print("✅ All API tests passed!")
    print("=" * 60)
    
    print("\n📝 Next Steps:")
    print("  1. Start the server: python main.py")
    print("  2. Open browser: http://127.0.0.1:8000/docs")
    print("  3. Try the /api/v1/chat endpoint")
    
    return True


if __name__ == "__main__":
    asyncio.run(test_api())
