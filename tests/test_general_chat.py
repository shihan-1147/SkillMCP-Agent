"""
测试通用对话功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.chat_service import ChatService
from src.api.schemas import ChatRequest


async def test_general_chat():
    """测试通用对话"""
    print("=" * 60)
    print("🧪 Testing General Chat with qwen3:latest")
    print("=" * 60)

    # 创建聊天服务
    chat_service = ChatService()

    # 测试用例
    test_messages = ["你好", "你叫什么名字？", "你能做什么？", "给我讲个笑话", "谢谢你"]

    for i, message in enumerate(test_messages, 1):
        print(f"\n📋 Test {i}: {message}")
        print("-" * 60)

        # 创建请求
        request = ChatRequest(message=message, session_id="test_session")

        try:
            # 发送请求
            response = await chat_service.chat(request)

            # 打印响应
            print(f"✅ Response:")
            print(f"   {response.reply}")

            if response.structured_data:
                print(f"   Structured Data: {response.structured_data}")

        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n" + "=" * 60)
    print("✅ General chat tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_general_chat())
