"""
Ollama Profile Builder
Create optimized, low-latency Modelfiles for any local model with custom context windows.
"""
import subprocess
import argparse
import sys
import json
import urllib.request

PROFILES = {
    "voice": {
        "num_ctx": 1536,
        "num_predict": 256,
        "temperature": 0.2,
        "system": "You are a fast, concise Windows desktop voice assistant. Keep answers brief, direct, and actionable."
    },
    "balanced": {
        "num_ctx": 4096,
        "num_predict": 512,
        "temperature": 0.3,
        "system": "You are an intelligent Windows assistant capable of calling tools, running commands, and answering questions clearly."
    },
    "deep": {
        "num_ctx": 8192,
        "num_predict": 2048,
        "temperature": 0.5,
        "system": "You are a comprehensive reasoning and coding assistant. Provide detailed, well-structured, and accurate solutions."
    }
}

def create_model_profile(base_model: str, target_name: str, profile_name: str = "voice", custom_ctx: int = None, custom_predict: int = None):
    preset = PROFILES.get(profile_name, PROFILES["voice"]).copy()
    
    if custom_ctx:
        preset["num_ctx"] = custom_ctx
    if custom_predict:
        preset["num_predict"] = custom_predict
        
    modelfile_content = f"""FROM {base_model}
PARAMETER num_ctx {preset['num_ctx']}
PARAMETER num_predict {preset['num_predict']}
PARAMETER temperature {preset['temperature']}
SYSTEM \"\"\"{preset['system']}\"\"\"
"""
    modelfile_path = f"Modelfile.{target_name}"
    with open(modelfile_path, "w", encoding="utf-8") as f:
        f.write(modelfile_content)
        
    print(f"[*] Generated {modelfile_path} with num_ctx={preset['num_ctx']}, num_predict={preset['num_predict']}")
    print(f"[*] Creating Ollama model: '{target_name}' from base '{base_model}'...")
    
    res = subprocess.run(["ollama", "create", target_name, "-f", modelfile_path], capture_output=True, text=True)
    if res.returncode == 0:
        print(f"[+] Successfully created model '{target_name}'!")
        return True
    else:
        print(f"[-] Failed to create model: {res.stderr}")
        return False

def list_installed_models():
    req = urllib.request.Request("http://localhost:11434/api/tags")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            return [m["name"] for m in data.get("models", [])]
    except Exception as e:
        print(f"[-] Could not connect to Ollama: {e}")
        return []

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build fast Ollama profiles with tuned context windows.")
    parser.add_argument("--base", type=str, default="nandhank/qwen3.5-abliterated-truthful:9b", help="Base model name in Ollama")
    parser.add_argument("--name", type=str, default="qwen9b-voice", help="New model alias")
    parser.add_argument("--profile", type=str, default="voice", choices=["voice", "balanced", "deep"], help="Predefined profile")
    parser.add_argument("--ctx", type=int, default=None, help="Custom context window size (e.g. 1024, 2048, 4096)")
    parser.add_argument("--predict", type=int, default=None, help="Max tokens to predict (e.g. 128, 256, 512)")
    parser.add_argument("--list", action="store_true", help="List all installed models")
    
    args = parser.parse_args()
    
    if args.list:
        models = list_installed_models()
        print("Installed Ollama models:")
        for m in models:
            print(f"  - {m}")
        sys.exit(0)
        
    create_model_profile(args.base, args.name, args.profile, args.ctx, args.predict)
