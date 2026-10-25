import urllib.request
import json
import time

def test_ollama_tool_call(model_name="qwen2.5-64k:latest"):
    print(f"Testing tool calling on model: {model_name}...")
    url = "http://localhost:11434/api/chat"
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "open_application",
                "description": "Opens a Windows application like notepad, calculator, or chrome",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "app_name": {
                            "type": "string",
                            "description": "The name or executable of the application, e.g. notepad, calc, chrome"
                        }
                    },
                    "required": ["app_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_files",
                "description": "Searches for files matching a pattern in a directory",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "The directory to search in"
                        },
                        "pattern": {
                            "type": "string",
                            "description": "The glob pattern, e.g. *.txt, *.py"
                        }
                    },
                    "required": ["directory", "pattern"]
                }
            }
        }
    ]
    
    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": "Can you open Notepad for me please?"
            }
        ],
        "tools": tools,
        "stream": False,
        "options": {
            "num_ctx": 4096,
            "temperature": 0.0
        }
    }
    
    t0 = time.time()
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        t_elapsed = time.time() - t0
        
    print(f"Completed in {t_elapsed:.2f}s")
    message = res.get("message", {})
    print("Response message:")
    print(json.dumps(message, indent=2))
    
    tool_calls = message.get("tool_calls", [])
    if tool_calls:
        print("\nSUCCESS! Model generated structured tool call(s):")
        for tc in tool_calls:
            print(f"  Tool: {tc.get('function', {}).get('name')}")
            print(f"  Args: {tc.get('function', {}).get('arguments')}")
    else:
        print("\nNo tool call returned. Raw content:")
        print(message.get("content"))

if __name__ == "__main__":
    test_ollama_tool_call()
