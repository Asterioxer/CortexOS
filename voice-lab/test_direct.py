import urllib.request
import json
import time

url = "http://localhost:11434/api/generate"
payload = {
    "model": "qwen9b-direct",
    "prompt": "What is the capital of France? Answer in 3 words.",
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

print(f"Elapsed: {dt:.2f}s")
print("Response:", repr(data.get("response", "").strip()))
print("Thinking:", repr(data.get("thinking", "").strip()))
print("Done reason:", data.get("done_reason"))
