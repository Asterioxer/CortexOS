import asyncio
import aiohttp
import json
import sys
import time

async def test_ui_connection():
    print("[*] Testing UI Server connectivity on http://127.0.0.1:9090...")
    async with aiohttp.ClientSession() as session:
        # 1. Test HTTP GET /
        async with session.get("http://127.0.0.1:9090/") as resp:
            status = resp.status
            assert status == 200, f"Expected 200, got {status}"
            print(f"[+] HTTP GET / returned 200 OK")

        # 2. Test WebSocket /ws with full bidirectional echo
        async with session.ws_connect("http://127.0.0.1:9090/ws") as ws:
            print("[+] WebSocket connection established successfully!")
            
            # Receive initial sync message
            msg = await ws.receive_json(timeout=3.0)
            assert msg.get("type") == "state_sync"
            print(f"[+] Initial state synced: {msg['data']['persona']}")
            
            # Send command
            await ws.send_str(json.dumps({"command": "set_persona", "persona": "jenny"}))
            
            # Wait for broadcast
            raw = await ws.receive_str(timeout=2.0)
            data = json.loads(raw)
            print(f"[+] Broadcast received from Assistant: {data}")
            assert data.get("type") == "persona"
            assert data.get("data") == "jenny"
            return True

if __name__ == "__main__":
    from ui_server import AssistantUIServer
    server = AssistantUIServer(port=9090)
    
    # Simulate assistant callback
    def mock_assistant_callback(cmd_text: str):
        print(f"[Mock Assistant Callback] Received: {cmd_text}")
        if cmd_text.startswith("/persona "):
            p = cmd_text.split(" ")[1]
            server.broadcast("persona", p)
    
    server.set_on_command_callback(mock_assistant_callback)
    server.start()
    time.sleep(1.0)
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success = loop.run_until_complete(test_ui_connection())
    if success:
        print("\n[SUCCESS] Bidirectional WebSocket and UI integration 100% verified!")
        sys.exit(0)
    else:
        sys.exit(1)
