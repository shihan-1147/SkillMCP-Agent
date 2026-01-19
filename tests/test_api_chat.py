"""
通过 API 测试通用对话
"""

import asyncio

import httpx


async def test_api_chat():
    """通过 HTTP API 测试聊天"""
    print("=" * 60)
    print("🧪 Testing Chat API with qwen3:latest")
    print("=" * 60)

    base_url = "http://127.0.0.1:8000"

    # 测试消息
    test_messages = [
        "你好",
        "你是谁？",
        "北京明天天气怎么样？",
        "帮我查询明天从北京到上海的高铁票",
        "谢谢",
    ]

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, message in enumerate(test_messages, 1):
            print(f"\n📋 Test {i}: {message}")
            print("-" * 60)

            try:
                response = await client.post(
                    f"{base_url}/api/v1/chat",
                    json={"message": message, "session_id": "test_api_session"},
                )

                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Status: {data['status']}")
                    print(f"   Reply: {data['reply']}")

                    if data.get("structured_data"):
                        print(f"   Structured Data: {data['structured_data']}")
                else:
                    print(f"❌ HTTP {response.status_code}")
                    print(f"   {response.text}")

            except Exception as e:
                print(f"❌ Error: {e}")

            # 稍作停顿
            await asyncio.sleep(1)

    print("\n" + "=" * 60)
    print("✅ API chat tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_api_chat())
