"""Sentence-level Edge-TTS streaming with bounded buffering and interruption."""
from __future__ import annotations

import asyncio
import io
import queue
import re
import threading
from typing import Iterable, Optional

import sounddevice as sd
import soundfile as sf

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+|(?<=[:;])\s+")


def split_ready_sentences(buffer: str, flush: bool = False) -> tuple[list[str], str]:
    parts = _SENTENCE_END.split(buffer)
    if flush:
        return [p.strip() for p in parts if p.strip()], ""
    if len(parts) == 1:
        return [], buffer
    return [p.strip() for p in parts[:-1] if p.strip()], parts[-1]


class EdgeSentenceStreamer:
    """Consume text fragments and speak completed sentences as soon as possible."""

    def __init__(self, personas: dict, persona: str = "jarvis", max_buffered: int = 4):
        if persona not in personas:
            raise ValueError(f"Unknown voice persona: {persona}")
        self.personas = personas
        self.persona = persona
        self.max_buffered = max_buffered
        self._cancel = threading.Event()
        self._queue: queue.Queue[Optional[bytes]] = queue.Queue(max_buffered)
        self._producer: Optional[threading.Thread] = None
        self._consumer: Optional[threading.Thread] = None

    def speak_stream(self, fragments: Iterable[str]) -> None:
        self.stop()
        self._cancel.clear()
        self._queue = queue.Queue(self.max_buffered)
        self._producer = threading.Thread(target=self._produce, args=(fragments,), daemon=True)
        self._consumer = threading.Thread(target=self._consume, daemon=True)
        self._consumer.start()
        self._producer.start()

    def _produce(self, fragments: Iterable[str]) -> None:
        buffer = ""
        try:
            for fragment in fragments:
                if self._cancel.is_set():
                    break
                ready, buffer = split_ready_sentences(buffer + fragment)
                for sentence in ready:
                    if not self._enqueue(self._synthesize(sentence)):
                        return
            ready, _ = split_ready_sentences(buffer, flush=True)
            for sentence in ready:
                if self._cancel.is_set() or not self._enqueue(self._synthesize(sentence)):
                    return
        finally:
            close = getattr(fragments, "close", None)
            if callable(close):
                try:
                    close()
                except Exception:
                    pass
            self._enqueue(None)

    def _enqueue(self, item: Optional[bytes]) -> bool:
        while not self._cancel.is_set():
            try:
                self._queue.put(item, timeout=0.1)
                return True
            except queue.Full:
                continue
        return False

    def _synthesize(self, sentence: str) -> bytes:
        async def run() -> bytes:
            import edge_tts
            p = self.personas[self.persona]
            communicate = edge_tts.Communicate(
                sentence, p["voice"], rate=p.get("rate", "+0%"),
                pitch=p.get("pitch", "+0Hz")
            )
            chunks = []
            async for chunk in communicate.stream():
                if self._cancel.is_set():
                    break
                if chunk.get("type") == "audio":
                    chunks.append(chunk["data"])
            return b"".join(chunks)
        return asyncio.run(run())

    def _consume(self) -> None:
        while not self._cancel.is_set():
            try:
                payload = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue
            if payload is None:
                return
            try:
                audio, sample_rate = sf.read(io.BytesIO(payload), dtype="float32")
                if audio.ndim == 2:
                    audio = audio.mean(axis=1)
                if not self._cancel.is_set():
                    sd.play(audio, sample_rate, blocking=True)
            except Exception:
                if not self._cancel.is_set():
                    continue

    def stop(self) -> None:
        self._cancel.set()
        try:
            sd.stop()
        except Exception:
            pass
        for thread in (self._producer, self._consumer):
            if thread and thread.is_alive() and thread is not threading.current_thread():
                thread.join(timeout=1.0)
