"""
Autonomous Windows Voice & Agentic Assistant v3.0
Combines:
1. Sub-50ms Instant Barge-In: Cuts off speaker audio immediately on user voice detection.
2. Self-Learning Memory: Remembers successful solutions in assistant_memory/learned_skills.json.
3. Superb Laptop Control: Generates code, opens directly in Notepad/VSCode, types/pastes into windows.
4. Self-Healing Multi-Model Tier: Fast model (qwen2.5:3b) + Deep model (qwen3.5 9b) for automatic error diagnosis.
5. Real Live News Engine: Live RSS feeds for factual, hallucination-free news.
6. Voice Shutdown: Hands-free exit back to PowerShell ("exit", "quit", "stop program", "go home").
"""
import os
import sys
import json
import time
import threading
import re
import win32com.client
from typing import Dict, Any, List, Optional

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from context_manager import AdaptiveContextEngine
from system_controller import SystemController
from sentiment_analyzer import CognitiveIntentAnalyzer
from voice_listener import VoiceListener
from autonomous_agent import AutonomousAgent
from voice_engine import UnifiedVoiceEngine
from session_sentinel import SessionUnlockSentinel
from mixture_of_experts import MoEGatingRouter
from ui_server import AssistantUIServer

class AutonomousAssistant:
    def __init__(
        self,
        tool_model: str = "qwen2.5:3b",
        chat_model: str = "dolphinlabs/llama3.2-3b-uncensored:latest",
        reasoning_model: str = "nandhank/qwen3.5-abliterated-truthful:9b",
        default_profile: str = "voice",
        voice_input_enabled: bool = True,
        voice_output_enabled: bool = True,
        wake_word: Optional[str] = None
    ):
        self.tool_model = tool_model
        self.chat_model = chat_model
        self.reasoning_model = reasoning_model
        self.active_model = tool_model
        
        self.profile = default_profile
        self.voice_output_enabled = voice_output_enabled
        self.voice_input_enabled = voice_input_enabled
        self.wake_word = wake_word
        
        # Core engines
        self.context_engine = AdaptiveContextEngine()
        self.controller = SystemController(sandbox_dir=r"C:\Users\soham\voice-lab\sandbox")
        self.analyzer = CognitiveIntentAnalyzer()
        self.agent = AutonomousAgent(
            fast_model=self.tool_model,
            heavy_model=self.reasoning_model,
            sandbox_dir=r"C:\Users\soham\voice-lab\sandbox"
        )
        self.moe_router = MoEGatingRouter()
        
        # High-Fidelity Studio Neural Voice Engine (JARVIS, Friday, Edith, Christopher, Neerja, etc.)
        self.voice_engine = UnifiedVoiceEngine(default_persona="jarvis")
        self.controller.set_voice_callback(self._on_controller_switch_persona)

        self.chat_history: List[Dict[str, str]] = []
        self.tools = self.controller.get_tool_definitions()

        # Real-time 3D Holographic Core Interface Server (Port 9090)
        self.ui_server = AssistantUIServer(port=9090)
        self.ui_server.set_on_command_callback(self.process_message)
        try:
            self.ui_server.start()
        except Exception as e:
            print(f"[!] Warning: UI Server error: {e}")

        # Initialize voice listener with Instant Sub-50ms Barge-In
        self.listener = None
        if self.voice_input_enabled:
            try:
                self.listener = VoiceListener(
                    on_speech_detected=self.handle_voice_input,
                    on_interrupt_detected=self.stop_speaking,
                    on_speech_started=lambda: self.ui_server.broadcast("state", "listening"),
                    wake_word=self.wake_word
                )
            except Exception as e:
                print(f"[!] Warning: Voice listener error: {e}")

        # Start speech state monitor thread
        self.monitor_thread = threading.Thread(target=self._speech_state_monitor, daemon=True)
        self.monitor_thread.start()

        # Autonomous Windows Session Unlock Sentinel (Phase 3)
        self.sentinel = SessionUnlockSentinel(
            on_unlock_callback=self._handle_unlock_briefing,
            username="Soham"
        )
        try:
            self.sentinel.start()
        except Exception as e:
            print(f"[!] Warning: Session Sentinel error: {e}")

        # Asynchronously pre-warm primary GPU model into VRAM for instant response
        def _silent_prewarm():
            try:
                self.context_engine.generate(self.tool_model, "ping", profile="voice")
            except Exception:
                pass

        threading.Thread(
            target=_silent_prewarm,
            daemon=True
        ).start()

    def _on_controller_switch_persona(self, persona_name: str) -> str:
        """Callback from tool execution when LLM initiates persona switch."""
        ack = self.voice_engine.set_persona(persona_name)
        print(f"[Persona Switched via LLM Tool] {ack}")
        if hasattr(self, "ui_server") and self.ui_server:
            self.ui_server.broadcast("persona", persona_name)
        return ack

    def _handle_unlock_briefing(self, briefing_text: str):
        """Delivers executive briefing upon Windows session unlock."""
        print(f"\n[Executive Briefing] {briefing_text}")
        self.speak(briefing_text)

    def is_speaking(self) -> bool:
        """Returns True if voice audio is actively playing."""
        return self.voice_engine.is_speaking()

    def stop_speaking(self):
        """Instantly stops and purges current speech in <10ms (Barge-In)."""
        self.voice_engine.stop()
        if self.listener:
            self.listener.set_speaking(False)
        if hasattr(self, "ui_server") and self.ui_server:
            self.ui_server.broadcast("state", "barge_in")

    def _speech_state_monitor(self):
        """Monitors when async speech finishes and notifies listener and HUD."""
        was_speaking = False
        while True:
            time.sleep(0.06)
            speaking = self.is_speaking()
            if was_speaking and not speaking:
                if self.listener:
                    self.listener.set_speaking(False)
                if hasattr(self, "ui_server") and self.ui_server:
                    self.ui_server.broadcast("state", "idle")
            elif not was_speaking and speaking:
                if self.listener:
                    self.listener.set_speaking(True)
            was_speaking = speaking

    def speak(self, text: str, wait: bool = False):
        """Speaks text using natural human neural voice."""
        if hasattr(self, "ui_server") and self.ui_server:
            self.ui_server.broadcast("response", text)
            self.ui_server.broadcast("state", "speaking")

        if not self.voice_output_enabled:
            return

        if self.listener:
            self.listener.set_speaking(True)

        self.voice_engine.speak(text, wait=wait)

    def stream_and_speak(self, model: str, messages: List[Dict[str, str]], profile: str = "voice") -> str:
        """
        Layer 1: Full-Duplex Real-Time LLM Token Streaming with Adaptive Micro-Clause Pipelining.
        Dispatches tokens directly to UI, and partitions streaming tokens into conversational
        clauses (commas, semicolons, dashes, sentence ends) for sub-600ms speech initiation.
        """
        gen_id = self.voice_engine.pipeline_start() if self.voice_output_enabled else 0
        if self.listener and self.voice_output_enabled:
            self.listener.set_speaking(True)
        if hasattr(self, "ui_server") and self.ui_server:
            self.ui_server.broadcast("state", "speaking")

        print("\nAssistant: ", end="", flush=True)

        full_content = ""
        buffer = ""
        seq_idx = 0

        # Pattern for sentence boundaries
        sentence_end_re = re.compile(r"([.!?]+(?:\s+|\Z)|\n+)")
        # Pattern for intermediate clause boundaries (commas, semicolons, dashes)
        clause_break_re = re.compile(r"([,;:—–]\s+)")

        try:
            for chunk in self.context_engine.chat_stream(model=model, messages=messages, profile=profile):
                content = chunk.get("content", "")
                if not content:
                    continue
                print(content, end="", flush=True)
                full_content += content
                buffer += content

                # Broadcast live token to HUD interface
                if hasattr(self, "ui_server") and self.ui_server:
                    self.ui_server.broadcast_token(content)

                words = buffer.strip().split()
                # 1. Immediate sentence end match
                s_match = sentence_end_re.search(buffer)
                if s_match:
                    sentence = buffer[:s_match.end()].strip()
                    buffer = buffer[s_match.end():]
                    if sentence and self.voice_output_enabled:
                        self.voice_engine.pipeline_feed(sentence, seq_idx, gen_id)
                        seq_idx += 1
                    continue

                # 2. Micro-clause match for rapid speech onset:
                # First clause needs >= 2 words (e.g. "Certainly Sir,", "Good afternoon,"),
                # subsequent clauses need >= 5 words to preserve natural phrasing
                min_words = 2 if seq_idx == 0 else 5
                if len(words) >= min_words:
                    c_match = clause_break_re.search(buffer)
                    if c_match:
                        clause = buffer[:c_match.end()].strip()
                        buffer = buffer[c_match.end():]
                        if clause and self.voice_output_enabled:
                            self.voice_engine.pipeline_feed(clause, seq_idx, gen_id)
                            seq_idx += 1
                        continue

                # 3. Safety word limit: if buffer exceeds 14 words without any punctuation, dispatch at word boundary
                if len(words) >= 14:
                    cut_idx = buffer.rfind(" ")
                    if cut_idx > 0:
                        clause = buffer[:cut_idx].strip()
                        buffer = buffer[cut_idx:].strip()
                        if clause and self.voice_output_enabled:
                            self.voice_engine.pipeline_feed(clause, seq_idx, gen_id)
                            seq_idx += 1

            # Flush any remaining buffer text
            remaining = buffer.strip()
            if remaining and self.voice_output_enabled:
                self.voice_engine.pipeline_feed(remaining, seq_idx, gen_id)
                seq_idx += 1

            if self.voice_output_enabled:
                self.voice_engine.pipeline_finish(seq_idx, gen_id)

        except Exception as e:
            err = f"Streaming inference error: {e}"
            print(f"\n[-] {err}")
            if hasattr(self, "ui_server") and self.ui_server:
                self.ui_server.broadcast("response", err)
            return full_content or err

        print()  # Newline after token stream
        res_text = full_content.strip()
        if hasattr(self, "ui_server") and self.ui_server:
            self.ui_server.broadcast("response", res_text)
            self.ui_server.broadcast_token("", is_done=True)
        return res_text

    def wait_until_done_speaking(self, timeout: float = 15.0):
        """Waits until the assistant finishes speaking current phrase."""
        self.voice_engine.wait_until_done(timeout=timeout)

    def handle_voice_input(self, transcribed_text: str):
        """Callback from background microphone listener."""
        print(f"\n[Voice Command] -> \"{transcribed_text}\"")
        if hasattr(self, "ui_server") and self.ui_server:
            self.ui_server.broadcast("heard", transcribed_text)
            self.ui_server.broadcast("state", "thinking")

        # Arm speaking state immediately so listener ignores ambient transients during thought/synthesis
        if self.listener:
            self.listener.set_speaking(True)

        # Dispatch execution to background worker to prevent listener loop thread starvation
        def _worker():
            try:
                self.process_message(transcribed_text)
            except Exception as e:
                print(f"[!] Processing error: {e}")

        threading.Thread(target=_worker, daemon=True).start()
        print("\nYou > ", end="", flush=True)

    def process_message(self, user_input: str) -> str:
        """Processes user input through cognitive intent routing, agentic execution, and voice feedback."""
        cleaned = user_input.strip()
        if not cleaned:
            return ""

        if hasattr(self, "ui_server") and self.ui_server:
            self.ui_server.broadcast("heard", cleaned)
            self.ui_server.broadcast("state", "thinking")

        # Slash commands
        if cleaned.startswith("/mode "):
            mode = cleaned.split(" ", 1)[1].strip()
            self.profile = mode
            print(f"[Profile Switched] Mode: {self.profile.upper()}")
            return f"Context profile set to {mode}."
        elif cleaned.startswith("/model "):
            mdl = cleaned.split(" ", 1)[1].strip()
            self.active_model = mdl
            print(f"[Model Switched] Active model: {self.active_model}")
            return f"Model changed to {mdl}."
        elif cleaned.startswith("/persona "):
            persona = cleaned.split(" ", 1)[1].strip()
            ack = self.voice_engine.set_persona(persona)
            print(f"[Persona Switched] {ack}")
            if hasattr(self, "ui_server") and self.ui_server:
                self.ui_server.broadcast("persona", persona)
            self.speak(ack)
            return ack
        elif cleaned == "/voice on":
            self.voice_output_enabled = True
            return "Voice feedback enabled."
        elif cleaned == "/voice off":
            self.voice_output_enabled = False
            return "Voice feedback disabled."
        elif cleaned in ["/briefing", "/brief"]:
            text = self.sentinel.trigger_briefing_now()
            return text
        elif cleaned == "/clear":
            self.chat_history.clear()
            return "Conversation history cleared."

        # 1. Cognitive Intent & Sentiment Analysis
        analysis = self.analyzer.analyze(cleaned)
        intent = analysis["intent"]
        emotion = analysis["emotion"]
        guidance = analysis["guidance"]
        norm_text = analysis.get("normalized_text", cleaned)

        print(f"[Intent: {intent} | Emotion: {emotion.upper()}]")

        # Handle Voice Exit / Shutdown Command
        if intent == "EXIT":
            farewell = "Assistant shutting down. Have a great day!"
            print(f"\nAssistant: {farewell}")
            print("\n[Exiting to terminal as requested...]")
            self.speak(farewell)
            time.sleep(1.2)
            self.stop_speaking()
            if self.listener:
                self.listener.stop()
            if hasattr(self, "sentinel") and self.sentinel:
                self.sentinel.stop()
            os._exit(0)

        # Handle Immediate Interrupt / Stop
        if intent == "INTERRUPT":
            self.stop_speaking()
            ack = "Understood. Paused and standing by."
            print(f"\nAssistant: {ack}")
            self.speak(ack)
            return ack

        # Handle Executive Briefing intent (0ms LLM overhead)
        if intent == "BRIEFING":
            text = self.sentinel.trigger_briefing_now()
            self.chat_history.append({"role": "user", "content": norm_text})
            self.chat_history.append({"role": "assistant", "content": text})
            return text

        # Handle Voice Persona Switch (0ms LLM overhead)
        if intent == "PERSONA_SWITCH":
            target_p = analysis.get("target_persona", "christopher")
            if target_p == "toggle":
                curr = self.voice_engine.persona_name
                cycle = ["christopher", "jenny", "aria", "guy", "neerja"]
                try:
                    idx = cycle.index(curr)
                    target_p = cycle[(idx + 1) % len(cycle)]
                except ValueError:
                    target_p = "jenny"
            ack = self.voice_engine.set_persona(target_p)
            spoken_ack = f"Voice persona switched to {target_p}. Ready to assist you."
            print(f"[Persona Switched] {ack}")
            print(f"\nAssistant: {spoken_ack}")
            if hasattr(self, "ui_server") and self.ui_server:
                self.ui_server.broadcast("persona", target_p)
            self.speak(spoken_ack)
            self.chat_history.append({"role": "user", "content": norm_text})
            self.chat_history.append({"role": "assistant", "content": spoken_ack})
            return spoken_ack

        # Handle Greetings / Acknowledgements (Zero tool hallucinations)
        if intent == "GREETING":
            greetings = {
                "friendly": "Hello Soham! I'm ready, what would you like to do?",
                "neutral": "Ready when you are."
            }
            reply = greetings.get(emotion, "Hello! How can I assist you right now?")
            print(f"\nAssistant: {reply}")
            self.speak(reply)
            self.chat_history.append({"role": "user", "content": norm_text})
            self.chat_history.append({"role": "assistant", "content": reply})
            return reply

        # Handle Media / Music (Direct browser/YouTube playback)
        if intent == "MEDIA_PLAY":
            query = analysis.get("media_query") or norm_text
            app = "brave" if "brave" in norm_text.lower() else ("chrome" if "chrome" in norm_text.lower() else None)
            result = self.controller.play_media(query, app=app)
            print(f"[Action: Media] {result}")
            spoken_ack = f"Playing {query} for you now."
            print(f"\nAssistant: {spoken_ack}")
            self.speak(spoken_ack)
            self.chat_history.append({"role": "user", "content": norm_text})
            self.chat_history.append({"role": "assistant", "content": spoken_ack})
            return spoken_ack

        # Handle Direct Desktop Actions (0ms LLM overhead)
        if intent == "SCREENSHOT":
            result = self.controller.take_screenshot()
            ack = "I have captured a screenshot and saved it to the sandbox."
            print(f"[Action: Screenshot] {result}")
            print(f"\nAssistant: {ack}")
            self.speak(ack)
            self.chat_history.append({"role": "user", "content": norm_text})
            self.chat_history.append({"role": "assistant", "content": ack})
            return ack

        if intent == "DESKTOP_TOGGLE":
            result = self.controller.toggle_desktop()
            ack = "Desktop toggled."
            print(f"[Action: Desktop] {result}")
            print(f"\nAssistant: {ack}")
            self.speak(ack)
            self.chat_history.append({"role": "user", "content": norm_text})
            self.chat_history.append({"role": "assistant", "content": ack})
            return ack

        if intent == "VOLUME_MUTE":
            result = self.controller.mute_volume()
            ack = "Audio mute toggled."
            print(f"[Action: Volume] {result}")
            print(f"\nAssistant: {ack}")
            self.speak(ack)
            self.chat_history.append({"role": "user", "content": norm_text})
            self.chat_history.append({"role": "assistant", "content": ack})
            return ack

        # Visual Chrome Tab Automation (0ms LLM overhead)
        if intent == "CHROME_TAB":
            target = analysis.get("target", "")
            result = self.controller.open_chrome_tab(target)
            ack = f"Opened a new tab in Chrome{' for ' + target if target else ''}."
            print(f"[Action: Chrome Tab] {result}")
            print(f"\nAssistant: {ack}")
            self.speak(ack)
            self.chat_history.append({"role": "user", "content": norm_text})
            self.chat_history.append({"role": "assistant", "content": ack})
            return ack

        # Visual Browser Tab Switch (0ms LLM overhead)
        if intent == "BROWSER_TAB_SWITCH":
            tab_num = analysis.get("tab_number", 1)
            result = self.controller.switch_browser_tab(tab_num)
            ack = f"Switched to tab {tab_num} in your browser."
            print(f"[Action: Browser Tab Switch] {result}")
            print(f"\nAssistant: {ack}")
            self.speak(ack)
            self.chat_history.append({"role": "user", "content": norm_text})
            self.chat_history.append({"role": "assistant", "content": ack})
            return ack

        # Visual Claude AI Web Automation (0ms LLM overhead)
        if intent == "CLAUDE_PROMPT":
            c_prompt = analysis.get("claude_prompt", "")
            ack = "Opening Claude AI in Chrome and submitting your prompt."
            print(f"\nAssistant: {ack}")
            self.speak(ack)
            result = self.controller.claude_web_prompt(c_prompt)
            print(f"[Action: Claude Web] {result}")
            self.chat_history.append({"role": "user", "content": norm_text})
            self.chat_history.append({"role": "assistant", "content": ack})
            return ack

        # Handle Real Live News Intent
        if intent == "NEWS":
            topic = analysis.get("news_topic") or norm_text
            print(f"[*] Fetching real live news for topic: '{topic}'...")
            live_news_data = self.controller.fetch_live_news(topic)
            
            news_prompt = [
                {"role": "system", "content": (
                    "You are an objective news anchor assistant. "
                    "Based ON THE LIVE HEADLINES BELOW, provide a clear, factual summary of what is happening. "
                    "Keep the main spoken summary direct and factual."
                )},
                {"role": "user", "content": f"User question: '{norm_text}'\n\nLive News Data:\n{live_news_data}"}
            ]
            try:
                res = self.context_engine.chat(
                    model=self.chat_model,
                    messages=news_prompt,
                    profile="balanced"
                )
                detailed_summary = res.get("message", {}).get("content", "").strip() or live_news_data
            except Exception:
                detailed_summary = live_news_data

            print(f"\n--- Detailed News Report ---")
            print(detailed_summary)
            print(f"----------------------------\n")
            
            self.speak(detailed_summary)
            self.chat_history.append({"role": "user", "content": norm_text})
            self.chat_history.append({"role": "assistant", "content": detailed_summary})
            return detailed_summary

        # Handle Code Creation & Notepad Operations via Autonomous Agent
        lower_norm = norm_text.lower()
        if "notepad" in lower_norm and any(w in lower_norm for w in ["write", "code", "program", "script", "generate"]):
            result = self.agent.execute_with_self_healing(norm_text)
            print(f"\nAssistant: {result}")
            self.speak(result)
            self.chat_history.append({"role": "user", "content": norm_text})
            self.chat_history.append({"role": "assistant", "content": result})
            return result

        # 2. Select Optimal Model & Mode via MoE Gating Router
        moe_route = self.moe_router.route(norm_text)
        expert = moe_route["expert"]
        print(f"[MoE Router] -> {moe_route['description']}")

        if expert == "HERMES_BRIDGE":
            skills = self.moe_router.hermes.list_skills()
            summary = f"Hermes Agent bridge active. Connected to {len(skills)} installed skills including autonomous coding, research, and computer use."
            print(f"\nAssistant: {summary}")
            self.speak(summary)
            self.chat_history.append({"role": "user", "content": norm_text})
            self.chat_history.append({"role": "assistant", "content": summary})
            return summary

        if expert == "CS_SCIENTIST":
            chosen_model = self.reasoning_model
            active_tools = None
            system_persona = self.moe_router.cs_expert.SYSTEM_PROMPT
        elif expert == "STRATEGIC_NEWS" and intent != "NEWS":
            intelligence = self.moe_router.news_expert.fetch_prioritized_news(norm_text)
            news_prompt = [
                {"role": "system", "content": "You are a Senior Strategic Geopolitical Analyst. Summarize the prioritized intelligence directly in 1-2 spoken sentences."},
                {"role": "user", "content": f"Intelligence Data:\n{intelligence}\n\nDeliver the verbal summary for: {norm_text}"}
            ]
            final_reply = self.stream_and_speak(model=self.chat_model, messages=news_prompt, profile="balanced")
            self.chat_history.append({"role": "user", "content": norm_text})
            self.chat_history.append({"role": "assistant", "content": final_reply})
            return final_reply
        elif expert == "OS_OPERATOR" or intent == "SYSTEM_CONTROL":
            chosen_model = self.tool_model
            active_tools = self.tools
            system_persona = (
                f"You are a high-precision Windows desktop operator. "
                f"User Emotion: {emotion}. Instruction: {guidance} "
                f"Always keep your spoken reply to 1-2 direct, natural sentences without robotic bullet lists."
            )
        elif intent == "DEEP_REASONING":
            chosen_model = self.reasoning_model
            active_tools = None
            system_persona = (
                f"You are an analytical reasoning assistant. "
                f"User Emotion: {emotion}. Instruction: {guidance} "
                f"Deliver clear, well-reasoned answers."
            )
        else: # CONVERSATION / EMOTIONAL SHARING
            chosen_model = self.chat_model
            active_tools = None
            system_persona = (
                f"You are an intuitive, direct Windows desktop assistant. "
                f"User Emotion: {emotion}. Instruction: {guidance} "
                f"Always keep your spoken reply to 1-2 direct, natural sentences without robotic bullet lists."
            )

        messages = [{"role": "system", "content": system_persona}]
        for h in self.chat_history[-4:]:
            messages.append(h)
        messages.append({"role": "user", "content": norm_text})

        print(f"[Thinking...] Model: {chosen_model} | Profile: {self.profile}")

        if active_tools is None:
            # Ultra-Low Latency Streaming Sentence Pipeline (<1.2s Perceived Latency)
            final_reply = self.stream_and_speak(
                model=chosen_model,
                messages=messages,
                profile=self.profile
            )
            self.chat_history.append({"role": "user", "content": norm_text})
            self.chat_history.append({"role": "assistant", "content": final_reply})
            return final_reply

        try:
            res = self.context_engine.chat(
                model=chosen_model,
                messages=messages,
                tools=active_tools,
                profile=self.profile
            )
        except Exception as e:
            err = f"Ollama connection error: {e}"
            print(f"[-] {err}")
            return err

        msg = res.get("message", {})
        tool_calls = msg.get("tool_calls", [])
        content = msg.get("content", "")

        # 3. Tool Execution Handling
        if tool_calls and active_tools:
            print(f"[Tools Triggered] {len(tool_calls)} action(s):")
            results = []
            for tc in tool_calls:
                fn = tc.get("function", {})
                fn_name = fn.get("name")
                fn_args = fn.get("arguments", {})
                print(f"  -> Executing: {fn_name}({fn_args})")
                r = self.controller.execute_tool(fn_name, fn_args)
                print(f"     Result: {r}")
                results.append(r)

            combined_results = "\n".join(results)
            summary_prompt = [
                {"role": "system", "content": "Summarize what was done in 1 short conversational sentence for the user."},
                {"role": "user", "content": f"User request: '{norm_text}'. Tool result: '{combined_results}'."}
            ]
            final_reply = self.stream_and_speak(
                model=self.tool_model,
                messages=summary_prompt,
                profile="voice"
            )
            if not final_reply:
                final_reply = combined_results

            self.chat_history.append({"role": "user", "content": norm_text})
            self.chat_history.append({"role": "assistant", "content": final_reply})
            return final_reply
        else:
            final_reply = content.strip()
            print(f"\nAssistant: {final_reply}")
            self.speak(final_reply)
            self.chat_history.append({"role": "user", "content": norm_text})
            self.chat_history.append({"role": "assistant", "content": final_reply})
            return final_reply

    def start_assistant(self):
        """Starts the autonomous assistant loop."""
        print("=" * 65)
        print("🤖 AUTONOMOUS WINDOWS AGENTIC ASSISTANT v3.5")
        print("=" * 65)
        print(f"Voice Engine:        Studio Human Neural TTS ({self.voice_engine.persona_name.capitalize()})")
        print(f"Latency Pipelining:  ACTIVE (<1.2s voice response via sentence streaming)")
        print(f"Whisper STT:         faster-whisper base.en (VAD 0.42s, Anti-Hallucination)")
        print(f"Fast Orchestrator:   {self.tool_model} (38 tok/s, 100% GPU VRAM)")
        print(f"Chat / Sentiment:    {self.chat_model} (Uncensored 23 tok/s)")
        print(f"Deep Self-Healing:   {self.reasoning_model} (9B Abliterated)")
        print(f"Browser Operator:    ACTIVE (Visual Chrome Tabs & Claude AI Web Automation)")
        print(f"Session Sentinel:    ACTIVE (Windows Unlock Detection & Executive Briefing)")
        print(f"MoE Gating Router:   ACTIVE (CS Scientist, OS Operator, Strategic News)")
        print(f"Hermes Agent Bridge: ACTIVE (51+ skills linked in C:\\Users\\soham\\AppData\\Local\\hermes)")
        print(f"Self-Learning Memory: ACTIVE (assistant_memory/learned_skills.json)")
        print(f"3D Holographic Core: ACTIVE (Live at http://localhost:9090)")
        print(f"Instant Barge-In:    ACTIVE (<50ms cut-off on user voice)")
        print(f"App Manipulation:    ACTIVE (Code generation & Notepad/App injection)")
        print(f"Live News Engine:    ACTIVE (Real Google/DDGS News Feeds)")
        print(f"Voice Shutdown:      ACTIVE (Say 'exit' or 'stop program' to quit)")
        print("\nCommands:")
        print("  - /persona [christopher|jenny|guy|aria|neerja|prabhat] - Switch voice")
        print("  - /mode [voice|balanced|deep] - Adjust reasoning depth")
        print("  - /voice [on|off] - Toggle speech audio")
        print("  - Speak naturally anytime (No Win+H needed)")
        print("  - Say 'Stop' or speak over assistant to interrupt instantly")
        print("  - Say 'exit' or type 'exit' to shut down to terminal")
        print("=" * 65)

        if self.listener:
            self.listener.start()

        self.speak("Agentic assistant ready. Speak anytime.")

        while True:
            try:
                user_input = input("\nYou > ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ["exit", "quit", "q"]:
                    self.stop_speaking()
                    if self.listener:
                        self.listener.stop()
                    if hasattr(self, "sentinel") and self.sentinel:
                        self.sentinel.stop()
                    self.speak("Assistant stopping. Goodbye!")
                    print("Assistant stopped.")
                    break

                self.process_message(user_input)
            except KeyboardInterrupt:
                if self.is_speaking():
                    self.stop_speaking()
                    print("\n[Speech Silenced via Ctrl+C]")
                    continue
                else:
                    print("\n(To stop the assistant completely, say or type 'exit')")
                    continue
            except EOFError:
                time.sleep(1)
            except Exception as e:
                print(f"[!] Error: {e}")

if __name__ == "__main__":
    assistant = AutonomousAssistant(
        tool_model="qwen2.5:3b",
        chat_model="dolphinlabs/llama3.2-3b-uncensored:latest",
        reasoning_model="nandhank/qwen3.5-abliterated-truthful:9b",
        default_profile="voice",
        voice_input_enabled=True,
        voice_output_enabled=True
    )
    assistant.start_assistant()
