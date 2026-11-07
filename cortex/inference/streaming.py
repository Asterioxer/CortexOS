"""True token streaming adapter for the repository's LocalInferenceClient."""
from __future__ import annotations

import json
from typing import Any, Dict, Iterator, Optional

import httpx


class OllamaChatStreamer:
    """Streams Ollama chat deltas while reusing LocalInferenceClient settings."""

    def __init__(self, client, timeout: float = 90.0):
        self.client = client
        self.timeout = timeout

    def stream_chat(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Iterator[str]:
        payload: Dict[str, Any] = {
            "model": model or self.client.model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": temperature},
        }
        timeout = httpx.Timeout(self.timeout, connect=5.0)
        with httpx.Client(timeout=timeout) as http:
            with http.stream(
                "POST", f"{self.client.base_url}/api/chat", json=payload
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    event = json.loads(line)
                    delta = event.get("message", {}).get("content", "")
                    if delta:
                        yield delta
                    if event.get("done"):
                        break
