import urllib.request
import json
import time

def test_speed_and_gpu(model_name, prompt="Hello! Who are you? Answer in 1 short sentence."):
    print(f"\n==========================================")
    print(f"Testing Model: {model_name}")
    print(f"==========================================")
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_ctx": 2048,
            "temperature": 0.2
        }
    }
    t0 = time.time()
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        elapsed = time.time() - t0
    
    eval_count = data.get('eval_count', 0)
    eval_dur = data.get('eval_duration', 0) / 1e9
    tok_per_sec = eval_count / eval_dur if eval_dur > 0 else 0
    print(f"Total time:       {elapsed:.2f}s")
    print(f"Prompt eval time: {data.get('prompt_eval_duration', 0) / 1e9:.2f}s")
    print(f"Eval speed:       {tok_per_sec:.2f} tokens/sec")
    print(f"Response:         {data.get('response', '').strip()}")

if __name__ == "__main__":
    test_speed_and_gpu("dolphinlabs/llama3.2-3b-uncensored:latest")
    test_speed_and_gpu("qwen2.5:3b")
