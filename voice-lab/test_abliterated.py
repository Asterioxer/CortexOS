import urllib.request
import json
import time

def test_model(model_name, prompt="Hello! Who are you, and what are you capable of doing? Give a concise 2-sentence intro."):
    print(f"\n=======================================================")
    print(f"Testing Model: {model_name}")
    print(f"Prompt: {prompt}")
    print(f"=======================================================")
    
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_ctx": 4096,
            "temperature": 0.2
        }
    }
    
    t0 = time.time()
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elapsed = time.time() - t0
            
            print(f"Total time elapsed: {elapsed:.2f}s")
            print(f"Load duration:      {data.get('load_duration', 0) / 1e9:.2f}s")
            print(f"Prompt eval tokens: {data.get('prompt_eval_count', 0)}")
            print(f"Prompt eval time:   {data.get('prompt_eval_duration', 0) / 1e9:.2f}s")
            eval_count = data.get('eval_count', 0)
            eval_dur = data.get('eval_duration', 0) / 1e9
            tok_per_sec = eval_count / eval_dur if eval_dur > 0 else 0
            print(f"Eval tokens:        {eval_count} tokens in {eval_dur:.2f}s ({tok_per_sec:.2f} tok/s)")
            print("\n--- Response ---")
            print(data.get("response", "").strip())
            print("----------------\n")
            return data
    except Exception as e:
        print(f"Error testing generate: {e}")
        return None

def test_tool_calling(model_name):
    print(f"\n=======================================================")
    print(f"Testing Tool Calling on: {model_name}")
    print(f"=======================================================")
    
    url = "http://localhost:11434/api/chat"
    tools = [
        {
            "type": "function",
            "function": {
                "name": "open_application",
                "description": "Opens a Windows application",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "app_name": {"type": "string", "description": "e.g. notepad, calc, chrome, powershell"}
                    },
                    "required": ["app_name"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "run_shell_command",
                "description": "Executes a safe PowerShell command",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "PowerShell command to run"}
                    },
                    "required": ["command"]
                }
            }
        }
    ]
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "user", "content": "Open Notepad and list files in the current folder"}
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
    
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elapsed = time.time() - t0
            msg = data.get("message", {})
            print(f"Tool Calling response time: {elapsed:.2f}s")
            print("Message:")
            print(json.dumps(msg, indent=2))
            
            tool_calls = msg.get("tool_calls", [])
            if tool_calls:
                print(f"\nSUCCESS! {len(tool_calls)} Tool Call(s) Detected:")
                for i, tc in enumerate(tool_calls, 1):
                    fn = tc.get("function", {})
                    print(f"  [{i}] {fn.get('name')}({fn.get('arguments')})")
            else:
                print("\nNo tool call returned.")
    except Exception as e:
        print(f"Error testing tool calling: {e}")

if __name__ == "__main__":
    model = "nandhank/qwen3.5-abliterated-truthful:9b"
    test_model(model)
    test_tool_calling(model)
