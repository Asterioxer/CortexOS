"""
CortexOS Autonomous Full-Duplex Voice & Somatosensory Assistant.
Absorbed and modernized from Voice Lab.

Combines:
1. Hands-Free Neural Speech & Whisper VAD.
2. Sub-10ms Instant Hardware Barge-In (interruption).
3. Cognitive Sentiment Tracking & Dynamic Personality Adaptation.
4. Somatosensory Laptop Control (PowerShell, Chrome tabs, volume, media, windows).
5. Multi-Model Local MoE (qwen2.5:3b, llama3.2-3b-uncensored, qwen3.5:9b).
6. Time-of-day Executive Briefing on session unlock or command.
"""

import os
import sys
import time
import threading
from typing import Dict, Any, List, Optional

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from cortex.embodiment.voice import CortexVoiceEngine, CortexVoiceListener, voice_engine
from cortex.embodiment.sentiment import CognitiveSentimentTracker
from cortex.embodiment.system_somatosensory import SystemSomatosensory
from cortex.embodiment.session_sentinel import ExecutiveBriefing, SessionUnlockSentinel
from cortex.inference.moe_router import MoEGatingRouter
from cortex.inference.client import LocalInferenceClient


class CortexVoiceAssistant:
    def __init__(
        self,
        voice_enabled: bool = True,
        default_persona: str = "friday",
        wake_word: Optional[str] = None
    ):
        self.voice_enabled = voice_enabled
        self.active_persona = default_persona
        self.wake_word = wake_word
        self.is_running = False

        # Engines
        self.voice = voice_engine
        self.voice.set_persona(default_persona)
        self.sentiment = CognitiveSentimentTracker()
        self.somato = SystemSomatosensory()
        self.moe = MoEGatingRouter()
        self.llm = LocalInferenceClient()
        self.briefing = ExecutiveBriefing(username="Soham")

        # Session Sentinel
        self.sentinel = SessionUnlockSentinel(
            on_unlock_callback=self._on_unlock_briefing,
            username="Soham"
        )

        # Listener
        self.listener = CortexVoiceListener(
            on_speech_detected=self.handle_input,
            on_interrupt_detected=self.voice.stop,
            wake_word=self.wake_word
        )

    def _on_unlock_briefing(self, text: str):
        print(f"\n[⚡ Executive Briefing] {text}")
        if self.voice_enabled:
            self.voice.speak(text, persona=self.active_persona)

    def handle_input(self, text: str):
        """Processes voice or text utterance."""
        clean = text.strip()
        if not clean:
            return

        print(f"\n[User Spoke] \"{clean}\"")

        # Stop any active voice playback immediately
        self.voice.stop()

        # Check special voice shortcuts
        lower = clean.lower()
        if lower in ["stop", "quiet", "silence", "hush", "shut up"]:
            print("[CortexOS] Vocal playback silenced.")
            return

        if lower in ["exit", "quit", "shutdown", "bye", "goodbye"]:
            print("[CortexOS] Shutting down voice assistant. Standby.")
            if self.voice_enabled:
                self.voice.speak("Shutting down voice assistant. Standby.", persona=self.active_persona, blocking=True)
            self.stop()
            return

        if lower.startswith("/persona") or lower.startswith("switch persona to ") or lower.startswith("switch voice to "):
            persona_name = clean.split()[-1].lower()
            res = self.voice.set_persona(persona_name)
            if res.get("status") == "SUCCESS":
                self.active_persona = persona_name
                ack = f"Switched voice persona to {persona_name.capitalize()}."
            else:
                ack = f"Persona '{persona_name}' not found."
            print(f"[CortexOS] {ack}")
            if self.voice_enabled:
                self.voice.speak(ack, persona=self.active_persona)
            return

        if "briefing" in lower or "give me a briefing" in lower:
            brief = self.briefing.generate()
            print(f"[CortexOS Briefing] {brief}")
            if self.voice_enabled:
                self.voice.speak(brief, persona=self.active_persona)
            return

        # Sentiment Analysis & Dynamic Adaptation
        sentiment_res = self.sentiment.analyze_utterance(clean)
        clean_text = sentiment_res["clean_text"]
        emotion = sentiment_res["emotion"]
        temp = sentiment_res["recommended_temperature"]
        print(f"  [Sentiment: {emotion.upper()} | Temp: {temp} | Style: {sentiment_res['tone_style']}]")

        # MoE Expert Routing
        route = self.moe.route(clean_text)
        expert = route["expert"]
        target_model = route["model"]
        print(f"  [MoE Routed -> {expert} via {target_model}]")

        # System 1 Somatosensory Reflex check
        reflex = self.llm.evaluate_system1_fastpath(clean_text)
        if reflex:
            action = reflex.get("action")
            res_val = reflex.get("resource")
            print(f"  [System 1 Reflex: {action}({res_val})]")

            reply = ""
            if action == "launch_terminal":
                r = self.somato.launch_terminal()
                reply = "Opening a new PowerShell terminal for you."
            elif action == "media_control":
                cmd = reflex.get("command", "pause")
                r = self.somato.media_control(cmd)
                reply = f"Media playback command {cmd} dispatched."
            elif action == "set_volume":
                level = reflex.get("level", 50)
                r = self.somato.set_volume(level)
                reply = f"Audio volume set to {level} percent."
            elif action == "toggle_mute":
                r = self.somato.toggle_mute()
                reply = "Master audio mute toggled."
            elif action == "open_application":
                r = self.somato.launch_application(str(res_val))
                reply = f"Opening {res_val} on your desktop."
            elif action == "close_application":
                r = self.somato.close_application(str(res_val))
                reply = f"Closing {res_val}."
            elif action == "capture_screenshot":
                r = self.somato.capture_screenshot()
                reply = "Desktop screenshot captured."
            else:
                reply = f"Executed {action}."

            print(f"[CortexOS] {reply}")
            if self.voice_enabled:
                self.voice.speak(reply, persona=self.active_persona)
            return

        # Handle CS Scientist AST verification
        if expert == "CS_SCIENTIST":
            prompt = (
                f"You are CortexOS CS Scientist Expert. User asked: {clean_text}\n"
                "Provide first-principles intuition, algorithmic complexity O(...), and concise code."
            )
            resp = self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=temp,
                override_model=target_model
            )
            print(f"[CortexOS CS Expert]\n{resp}")
            if self.voice_enabled:
                self.voice.speak(resp, persona=self.active_persona)
            return

        # Handle Strategic News
        if expert == "STRATEGIC_NEWS":
            news_report = self.somato.fetch_prioritized_news(clean_text)
            print(f"[CortexOS News]\n{news_report}")
            spoken_summary = news_report.split("\n")[1] if "\n" in news_report else news_report
            if self.voice_enabled:
                self.voice.speak(f"Here is your strategic intelligence report. {spoken_summary}", persona=self.active_persona)
            return

        # General LLM dialogue with somatosensory context
        snap = self.somato.get_summary_snapshot()
        system_prompt = (
            f"You are CortexOS, an embodied AI cognitive system residing on Soham's Windows 11 laptop.\n"
            f"Hardware telemetry:\n{snap}\n"
            f"User tone: {emotion}. Respond directly, concisely, and accurately without fluff."
        )
        resp = self.llm.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": clean_text}
            ],
            temperature=temp,
            override_model=target_model
        )
        print(f"[CortexOS]\n{resp}")
        if self.voice_enabled:
            self.voice.speak(resp, persona=self.active_persona)

    def start(self):
        """Starts background listener and session sentinel."""
        self.is_running = True
        self.sentinel.start()
        self.listener.start()
        print("\n=======================================================")
        print("  🧠 CortexOS Full-Duplex Voice & Somatosensory Engine")
        print(f"  Active Persona: {self.active_persona.capitalize()}")
        print("  Listening continuously... (Speak or type your commands)")
        print("=======================================================\n")

    def stop(self):
        self.is_running = False
        self.voice.stop()
        self.listener.stop()
        self.sentinel.stop()

    def run_cli_loop(self):
        """Interactive console loop allowing keyboard input alongside voice."""
        self.start()
        try:
            while self.is_running:
                user_msg = input("\n[CortexOS Input] > ").strip()
                if user_msg:
                    self.handle_input(user_msg)
        except (KeyboardInterrupt, EOFError):
            print("\n[CortexOS] Interrupted by operator.")
        finally:
            self.stop()


if __name__ == "__main__":
    assistant = CortexVoiceAssistant()
    assistant.run_cli_loop()
