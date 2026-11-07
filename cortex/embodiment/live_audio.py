"""Live microphone capture, VAD and Faster-Whisper transcription for CortexOS.

The sounddevice callback is deliberately kept lightweight: it copies 32 ms
frames into a bounded queue. Model inference and user callbacks run elsewhere.
"""
from __future__ import annotations

import logging
import queue
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Callable, Deque, Optional

import numpy as np

from cortex.embodiment.audio_dsp import PHANTOM_PHRASES, SileroVAD

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class VoiceConfig:
    sample_rate: int = 16000
    frame_samples: int = 512
    pre_roll_frames: int = 12
    end_silence_seconds: float = 0.65
    min_utterance_seconds: float = 0.25
    max_utterance_seconds: float = 18.0
    queue_frames: int = 64
    speech_threshold: float = 0.5
    barge_in_threshold: float = 0.70
    whisper_model: str = "tiny.en"
    device: Optional[int] = None
    compute_type: str = "int8"
    wake_word: Optional[str] = None


class CortexVoiceListener:
    """A real microphone listener compatible with the legacy listener API."""

    def __init__(
        self,
        on_speech_detected: Optional[Callable[[str], None]] = None,
        on_interrupt_detected: Optional[Callable[[], None]] = None,
        on_speech_started: Optional[Callable[[], None]] = None,
        config: Optional[VoiceConfig] = None,
        vad: Optional[SileroVAD] = None,
    ) -> None:
        self.config = config or VoiceConfig()
        self.on_speech_detected = on_speech_detected
        self.on_interrupt_detected = on_interrupt_detected
        self.on_speech_started = on_speech_started
        self.vad = vad or SileroVAD(
            speech_threshold=self.config.speech_threshold,
            barge_in_threshold=self.config.barge_in_threshold,
        )
        self._frames: queue.Queue[np.ndarray] = queue.Queue(self.config.queue_frames)
        self._stop = threading.Event()
        self._worker: Optional[threading.Thread] = None
        self._stream = None
        self._model = None
        self._active = False
        self._interrupt_sent = False
        self._pre_roll: Deque[np.ndarray] = deque(maxlen=self.config.pre_roll_frames)
        self._utterance: list[np.ndarray] = []
        self._silence_frames = 0
        self._last_probability = 0.0
        self._callback_threads: set[threading.Thread] = set()

    def start(self) -> None:
        if self._worker and self._worker.is_alive():
            return
        try:
            import sounddevice as sd
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError("Live voice requires sounddevice and faster-whisper") from exc

        self._stop.clear()
        self._model = WhisperModel(
            self.config.whisper_model,
            device="cpu",
            compute_type=self.config.compute_type,
        )
        self._worker = threading.Thread(target=self._run, name="cortex-voice-vad", daemon=True)
        self._worker.start()
        try:
            self._stream = sd.InputStream(
                samplerate=self.config.sample_rate,
                channels=1,
                dtype="float32",
                blocksize=self.config.frame_samples,
                device=self.config.device,
                callback=self._audio_callback,
            )
            self._stream.start()
        except Exception:
            self.stop()
            raise

    def _audio_callback(self, indata, frames, time_info, status) -> None:
        if status:
            log.debug("Microphone status: %s", status)
        frame = np.asarray(indata[:, 0], dtype=np.float32).copy()
        try:
            self._frames.put_nowait(frame)
        except queue.Full:
            try:
                self._frames.get_nowait()
            except queue.Empty:
                pass
            try:
                self._frames.put_nowait(frame)
            except queue.Full:
                pass

    def _dispatch(self, callback, *args) -> None:
        if callback is None:
            return
        def invoke():
            try:
                callback(*args)
            except Exception:
                log.exception("Voice callback failed")
        t = threading.Thread(target=invoke, daemon=True)
        self._callback_threads.add(t)
        t.start()

    def _run(self) -> None:
        frame_seconds = self.config.frame_samples / self.config.sample_rate
        while not self._stop.is_set():
            try:
                frame = self._frames.get(timeout=0.1)
            except queue.Empty:
                continue
            if len(frame) != self.config.frame_samples:
                continue
            try:
                probability, speech = self.vad.process_chunk(frame)
            except Exception:
                log.exception("VAD frame failed")
                continue
            self._last_probability = probability

            if speech and not self._active:
                self._active = True
                self._interrupt_sent = False
                self._silence_frames = 0
                self._utterance = list(self._pre_roll)
                self._dispatch(self.on_speech_started)

            if self._active:
                self._utterance.append(frame)
                if probability >= self.config.barge_in_threshold and not self._interrupt_sent:
                    self._interrupt_sent = True
                    self._dispatch(self.on_interrupt_detected)
                if speech:
                    self._silence_frames = 0
                else:
                    self._silence_frames += 1
                duration = len(self._utterance) * frame_seconds
                end_after = int(self.config.end_silence_seconds / frame_seconds)
                if (self._silence_frames >= end_after or
                        duration >= self.config.max_utterance_seconds):
                    self._finish_utterance(frame_seconds)
            else:
                self._pre_roll.append(frame)

    def _finish_utterance(self, frame_seconds: float) -> None:
        audio = np.concatenate(self._utterance) if self._utterance else np.array([], dtype=np.float32)
        duration = len(audio) / self.config.sample_rate
        self._active = False
        self._utterance = []
        self._silence_frames = 0
        self._pre_roll.clear()
        self.vad.reset_states()
        if duration < self.config.min_utterance_seconds or self._model is None:
            return
        try:
            segments, _ = self._model.transcribe(
                audio,
                language="en",
                beam_size=1,
                vad_filter=False,
                condition_on_previous_text=False,
            )
            text = " ".join(s.text.strip() for s in segments).strip()
        except Exception:
            log.exception("Faster-Whisper transcription failed")
            return
        normalized = text.lower().strip().rstrip(".!?")
        if not text or normalized in PHANTOM_PHRASES:
            return
        if self.config.wake_word:
            if self.config.wake_word.lower() not in normalized:
                return
            text = text.replace(self.config.wake_word, "", 1).strip(" ,")
            if not text:
                return
        self._dispatch(self.on_speech_detected, text)

    def stop(self) -> None:
        self._stop.set()
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                log.exception("Failed to close microphone stream")
            self._stream = None
        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=4.0)
        self._active = False
        self._utterance.clear()
        self._pre_roll.clear()
        self.vad.reset_states()

    def is_listening(self) -> bool:
        return bool(self._stream is not None and self._worker and self._worker.is_alive())
