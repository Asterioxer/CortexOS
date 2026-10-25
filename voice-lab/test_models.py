import urllib.request
import json
import time

def test_tool(model_name):
    print(f"\n--- Testing {model_name} ---")
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": "Can you open Notepad for me please?"}],
        "tools": [{
            "type": "function",
            "function": {
                "name": "open_application",
                "description": "Opens a Windows application",
                "parameters": {
                    "type": "object",
                    "properties": {"app_name": {"type": "string"}},
                    "required": ["app_name"]
                }
            }
        }],
        "stream": False,
        "options": {"num_ctx": 4096, "temperature": 0.0}
    }
    
    t0 = time.time()
    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            dt = time.time() - t0
            msg = res.get("message", {})
            tcs = msg.get("tool_calls", [])
            print(f"Elapsed: {dt:.2f}s")
            if tcs:
                print("Tool call generated:", tcs)
            else:
                print("No tool call. Output:", msg.get("content"))
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_tool("gemma3:4b")
