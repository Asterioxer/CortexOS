import numpy as np

from cortex.embodiment.live_audio import VoiceConfig, CortexVoiceListener


class FakeVAD:
    def __init__(self, *args, **kwargs):
        self.n = 0
    def process_chunk(self, frame):
        self.n += 1
        return (0.9, True) if self.n <= 2 else (0.0, False)
    def reset_states(self):
        self.n = 0


def test_listener_constructs_without_opening_microphone():
    listener = CortexVoiceListener(config=VoiceConfig(), vad=FakeVAD())
    assert not listener.is_listening()
    assert listener.config.sample_rate == 16000
