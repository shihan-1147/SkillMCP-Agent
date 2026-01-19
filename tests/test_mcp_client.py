"""测试 MCP Client Manager"""
import asyncio
from src.mcp.mcp_client import MCPClientManager

async def test():
    manager = MCPClientManager()
    print('Initializing MCP Client Manager...')
    try:
        await manager.initialize()
        print(f'Connected servers: {manager.list_available_servers()}')
        tools = manager.list_tools()
        print(f'Available tools ({len(tools)}):')
        for t in tools:
            print(f'  - {t["name"]}: {t.get("description", "")[:50]}')
        
        # 测试调用 12306-mcp
        if "12306-mcp" in manager.list_available_servers():
            print('\n--- Testing get-current-date ---')
            result = await manager.call_tool(
                "12306-mcp",
                "get-current-date",
                {}
            )
            print(f'Result: {result}')
            
            print('\n--- Testing get-station-code-of-citys ---')
            result = await manager.call_tool(
                "12306-mcp",
                "get-station-code-of-citys",
                {"citys": "北京|石家庄"}
            )
            print(f'Result: {result}')
            
            print('\n--- Testing get-tickets ---')
            result = await manager.call_tool(
                "12306-mcp",
                "get-tickets",
                {
                    "date": "2026-01-20",
                    "fromStation": "BJP",
                    "toStation": "SJP",
                    "trainFilterFlags": "G",
                    "limitedNum": 3
                }
            )
            print(f'Success: {result.get("success")}')
            print(f'Data:\n{result.get("data", "")[:500]}...')
            
    except Exception as e:
        import traceback
        print(f'Error: {e}')
        traceback.print_exc()
    finally:
        await manager.close()

if __name__ == "__main__":
    asyncio.run(test())
