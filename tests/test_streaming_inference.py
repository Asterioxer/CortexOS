from cortex.inference.streaming import OllamaChatStreamer


class FakeClient:
    model = "qwen2.5:3b"
    base_url = "http://127.0.0.1:11434"


def test_streamer_uses_local_client_defaults():
    streamer = OllamaChatStreamer(FakeClient())
    assert streamer.client.model == "qwen2.5:3b"
