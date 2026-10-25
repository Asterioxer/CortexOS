import urllib.request
import json
import time

url = "http://localhost:11434/api/generate"
payload = {
    "model": "qwen2.5-fast",
    "prompt": "What is 2+2? Answer in one word.",
    "stream": False
}

t0 = time.time()
req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode("utf-8"))
    dt = time.time() - t0

print(f"Elapsed time:       {dt:.2f}s")
print(f"Load duration:      {data.get('load_duration', 0) / 1e9:.2f}s")
print(f"Prompt eval tokens: {data.get('prompt_eval_count', 0)}")
print(f"Prompt eval time:   {data.get('prompt_eval_duration', 0) / 1e9:.2f}s")
eval_count = data.get('eval_count', 0)
eval_dur = data.get('eval_duration', 0) / 1e9
tok_per_sec = eval_count / eval_dur if eval_dur > 0 else 0
print(f"Eval tokens:        {eval_count} tokens in {eval_dur:.2f}s ({tok_per_sec:.2f} tok/s)")
print("Response:          ", repr(data.get("response", "").strip()))
