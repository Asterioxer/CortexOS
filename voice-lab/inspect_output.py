import urllib.request
import json

url = "http://localhost:11434/api/generate"
payload = {
    "model": "qwen9b-fast",
    "prompt": "What is 2+2? Answer in one word.",
    "stream": False
}

req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode("utf-8"))

print("Keys:", list(data.keys()))
print("Response:", repr(data.get("response")))
print("Thinking:", repr(data.get("thinking")))
print("Done reason:", data.get("done_reason"))
