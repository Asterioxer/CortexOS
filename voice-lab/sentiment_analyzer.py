"""
Cognitive Sentiment & Intent Analyzer v2.2
Detects voice exit commands, real-time news inquiries, media playback, interruptions, and emotional tone.
"""
import re
from typing import Dict, Any

class CognitiveIntentAnalyzer:
    def __init__(self):
        # Exit / Shutdown trigger phrases
        self.exit_patterns = [
            r"^(exit|quit|stop the program|exit the program|exit out of this shell|close the assistant|go home|shutdown assistant|terminate assistant|close assistant|bye assistant|exit our conversation)\b",
            r"\b(exit the session|stop running|quit the assistant|exit out)\b"
        ]

        # Stop / Barge-in trigger phrases
        self.stop_patterns = [
            r"^(stop|quiet|shut up|hush|silence|cancel|never mind|wait|hold on|pause)\b",
            r"\b(shut up|be quiet|stop talking|cancel that|dont think yet|wait wait)\b"
        ]

        # Greeting & acknowledgement phrases (NO TOOLS)
        self.greeting_patterns = [
            r"^(hello|hi|hey|good morning|good afternoon|good evening|sup|howdy)\b",
            r"^(all right|alright|okay|ok|cool|got it|sounds good|understood|yes|yep|sure)\.?$"
        ]

        # News / Real-time information intent
        self.news_triggers = [
            r"\b(?:give me|tell me|read|fetch|show|get|search|what is|what are)\s+(?:the\s+)?news\b",
            r"\bnews\s+(?:about|on|for|regarding|of)\b",
            r"\b(?:latest|breaking|world|today'?s)\s+news\b",
            r"\bwhat(?:'s|\s+is)\s+happening\s+(?:around\s+the\s+world|in\s+the\s+world|today)\b",
            r"\bnews\s+of\s+the\s+day\b",
            r"\bgive me (?:the )?news\b",
            r"\bheadlines\b",
            r"\b(?:research|check)\s+(?:today'?s\s+)?(?:latest\s+)?news\b"
        ]

        # Media / Music playback intent
        self.media_patterns = [
            r"\b(play|listen to|put on)\b.+?\b(song|music|track|album|by|video|youtube)?\b",
            r"\bplay\b"
        ]

        # Fast direct system actions
        self.screenshot_patterns = [
            r"\b(take a screenshot|capture (the )?screen|take a snapshot|capture display|screenshot)\b"
        ]
        self.desktop_patterns = [
            r"\b(minimize (all|everything)|show (the )?desktop|hide all windows|desktop view)\b"
        ]
        self.mute_patterns = [
            r"\b(mute (the )?(audio|volume|sound)|unmute|silence (the )?laptop)\b",
            r"^(mute|unmute)$"
        ]
        self.claude_patterns = [
            r"\b(?:ask|tell|prompt)\s+claude\s+(?:to\s+)?(.+)",
            r"\bopen\s+claude\s+(?:and\s+)?(?:ask\s+|to\s+)?(.+)"
        ]
        self.chrome_tab_patterns = [
            r"\b(?:open\s+(?:a\s+)?new\s+tab(?:\s+in\s+chrome)?|chrome\s+new\s+tab)(?:\s+(?:for|to|with)\s+(.+))?",
            r"\bopen\s+(?:a\s+)?(?:chrome\s+)?tab\s+(?:for|to|with)\s+(.+)"
        ]
        self.tab_switch_patterns = [
            r"\b(?:click\s+on\s+the|go\s+to\s+the|switch\s+to\s+the)\s+(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|\d+(?:st|nd|rd|th)?)\s+tab\b",
            r"\b(?:switch|go\s+to)\s+(?:browser\s+)?tab\s+(\d+)\b"
        ]
        self.briefing_patterns = [
            r"\b(executive briefing|morning briefing|daily briefing|status briefing|give me (my|a) briefing|brief me)\b"
        ]
        self.personas = ["jarvis", "friday", "edith", "brian", "ava", "emma", "ryan", "christopher", "jenny", "guy", "aria", "neerja", "prabhat", "eric"]

        # Emotion patterns
        self.emotion_patterns = {
            "frustrated": [
                r"\b(annoyed|frustrated|angry|damn|shit|fuck|broken|hate|stupid|idiot|stop failing|tired of|doesn't work|fail|not that good|bad)\b",
                r"!{2,}",
                r"\b(why (is it|isn't it|won't it))\b"
            ],
            "urgent": [
                r"\b(quick|hurry|asap|urgent|now|immediately|fast|rush|emergency|right now)\b"
            ],
            "excited": [
                r"\b(awesome|great|amazing|love|cool|wow|fantastic|incredible|super|yay|lets go)\b"
            ],
            "stressed": [
                r"\b(stressed|overwhelmed|exhausted|burnout|too much|cant handle|tired)\b"
            ],
            "confused": [
                r"\b(confused|lost|dont understand|what do you mean|huh|how come|no idea)\b"
            ]
        }

    def normalize_speech(self, text: str) -> str:
        """Fixes common phonetic transcription errors from microphone."""
        t = text
        # Fix browser name transcription
        t = re.sub(r"\b(braver|braille)\b", "brave", t, flags=re.IGNORECASE)
        # Fix politician / entity names
        t = re.sub(r"\b(s\.?j\.?\s*shankar|s\.?\s*j\.?\s*shankar)\b", "S. Jaishankar", t, flags=re.IGNORECASE)
        # Fix Antigravity transcription
        t = re.sub(r"\b(anti[\s-]*grabity|anti[\s-]+gravity)\b", "antigravity", t, flags=re.IGNORECASE)
        # Fix Aria transcription errors
        t = re.sub(r"\b(abia|arria)\b", "aria", t, flags=re.IGNORECASE)
        # Fix hyphens transcription error
        t = re.sub(r"\b(high fence|high fences)\b", "hyphens", t, flags=re.IGNORECASE)
        # Fix JARVIS / Friday / Edith phonetic transcriptions
        t = re.sub(r"\b(jarvis|jarves|jharvis|travis)\b", "jarvis", t, flags=re.IGNORECASE)
        t = re.sub(r"\b(edit|edeth|edith's)\b", "edith", t, flags=re.IGNORECASE)
        t = re.sub(r"\b(eva|aiva)\b", "ava", t, flags=re.IGNORECASE)
        # Fix common conversational grammar
        t = re.sub(r"\bpost[\s-]+fo\b", "post for", t, flags=re.IGNORECASE)
        return t

    def analyze(self, text: str) -> Dict[str, Any]:
        """Classifies intent, sentiment, and emotional tone."""
        clean = self.normalize_speech(text.strip())
        lower = clean.lower()

        # 1. Check for Voice Exit / Termination Command
        for pat in self.exit_patterns:
            if re.search(pat, lower):
                return {
                    "intent": "EXIT",
                    "emotion": "neutral",
                    "action_required": False,
                    "normalized_text": clean,
                    "guidance": "Terminate assistant and exit shell."
                }

        # 2. Check for Immediate Stop / Barge-in
        for pat in self.stop_patterns:
            if re.search(pat, lower):
                return {
                    "intent": "INTERRUPT",
                    "emotion": "neutral",
                    "action_required": False,
                    "normalized_text": clean,
                    "guidance": "User commanded stop. Acknowledge briefly and stand by."
                }

        # 3. Voice Persona Switch intent (0ms LLM overhead) - High Priority
        # 3a. Named Personas & phonetic matches
        for p in self.personas:
            p_pat = rf"(?:\b(?:slash\s+persona|persona|voice|switch|change|set|use|activate|put\s+in|want|be|talk|speak|sound|like)\b.*?(\b{p}\b))|(\b{p}\b.*?\b(?:voice|persona)\b)"
            if re.search(p_pat, lower):
                return {
                    "intent": "PERSONA_SWITCH",
                    "emotion": "neutral",
                    "target_persona": p,
                    "action_required": True,
                    "normalized_text": clean,
                    "guidance": f"Switch active voice persona to {p}."
                }

        # 3b. Voice characteristic aliases (female, male, indian)
        voice_aliases = {
            "female": "jenny",
            "woman": "jenny",
            "girl": "jenny",
            "male": "guy",
            "man": "guy",
            "guy": "guy",
            "indian": "neerja",
            "india": "neerja"
        }
        for alias, target in voice_aliases.items():
            if re.search(rf"\b(?:switch|change|use|set|be|want|give\s+me)\b.*?\b{alias}\s+voice\b", lower) or re.search(rf"\b{alias}\s+voice\b", lower):
                return {
                    "intent": "PERSONA_SWITCH",
                    "emotion": "neutral",
                    "target_persona": target,
                    "action_required": True,
                    "normalized_text": clean,
                    "guidance": f"Switch active voice persona to {target}."
                }

        # 3c. Generic voice switch requests (e.g. "change the voice", "switch voice", "different voice")
        generic_voice_pat = r"\b(?:change|switch|next|different|swap|toggle)\s+(?:the\s+)?(?:voice|persona|tone)\b"
        if re.search(generic_voice_pat, lower) or "change the voice" in lower or "switch voice" in lower:
            return {
                "intent": "PERSONA_SWITCH",
                "emotion": "neutral",
                "target_persona": "toggle",
                "action_required": True,
                "normalized_text": clean,
                "guidance": "Switch active voice persona to alternate voice."
            }

        # 4. Browser Tab Switch intent (0ms LLM overhead)
        tab_names = {
            "first": 1, "1st": 1, "1": 1, "one": 1,
            "second": 2, "2nd": 2, "2": 2, "two": 2,
            "third": 3, "3rd": 3, "3": 3, "three": 3,
            "fourth": 4, "4th": 4, "4": 4, "four": 4,
            "fifth": 5, "5th": 5, "5": 5, "five": 5,
            "sixth": 6, "6th": 6, "6": 6, "six": 6,
            "seventh": 7, "7th": 7, "7": 7, "seven": 7,
            "eighth": 8, "8th": 8, "8": 8, "eight": 8,
            "ninth": 9, "9th": 9, "9": 9, "nine": 9
        }
        for pat in self.tab_switch_patterns:
            m = re.search(pat, lower)
            if m:
                raw_tab = m.group(1).lower().strip()
                tab_idx = tab_names.get(raw_tab, 1)
                try:
                    tab_idx = int(raw_tab)
                except ValueError:
                    pass
                return {
                    "intent": "BROWSER_TAB_SWITCH",
                    "emotion": "neutral",
                    "tab_number": tab_idx,
                    "action_required": True,
                    "normalized_text": clean,
                    "guidance": f"Switch to browser tab {tab_idx}."
                }

        # 5. Check for Real Live News Intent
        is_news = any(re.search(trig, lower) for trig in self.news_triggers)
        if is_news:
            topic = "world breaking news"
            # Extract specific topic after 'about' or 'on'
            m_topic = re.search(r"\b(?:news|updates?)\s+(?:about|on|regarding|for)\s+([a-zA-Z0-9\s]{2,40})", lower)
            if m_topic:
                cand = m_topic.group(1).strip()
                cand = re.sub(r"\b(?:and|or|in\s+chrome|from|by|today|the\s+world|now|please)\b.*", "", cand).strip()
                if cand and cand not in ["the world", "today", "google chrome", "chrome", "it", "me", "world"]:
                    topic = cand

            return {
                "intent": "NEWS",
                "emotion": "informative",
                "news_topic": topic,
                "action_required": True,
                "normalized_text": clean,
                "guidance": f"Fetch real live news for '{topic}' and summarize clearly."
            }

        # 6. Check for Pure Greeting / Acknowledgement (NO TOOLS)
        is_greeting = any(re.search(pat, lower) for pat in self.greeting_patterns)
        has_substantive_action = any(
            re.search(rf"\b{kw}\b", lower) for kw in [
                "news", "headline", "headlines", "world", "chrome", "claude", "tab",
                "open", "launch", "close", "play", "screenshot", "mute", "volume",
                "briefing", "persona", "switch", "change", "write", "code", "run",
                "antigravity", "linkedin"
            ]
        )
        if is_greeting and not has_substantive_action:
            return {
                "intent": "GREETING",
                "emotion": "friendly",
                "action_required": False,
                "normalized_text": clean,
                "guidance": "Natural conversational greeting. Do not execute any tools. Be warm and brief."
            }

        # 5. Check for Media / Music intent
        media_match = re.search(r"\b(?:play|listen to|put on)\s+(?:the\s+)?(?:song\s+)?(?:called\s+)?(.+)", lower)
        if media_match or ("play" in lower and any(w in lower for w in ["song", "music", "adele", "youtube", "spotify"])):
            if media_match:
                raw_query = media_match.group(1).strip()
                song_query = re.sub(r"\s+(?:in|on|using)\s+(?:brave|chrome|youtube|spotify|browser).*", "", raw_query).strip()
            else:
                song_query = re.sub(r"^(?:please\s+)?(?:can you\s+)?play\s+", "", lower).strip()
                song_query = re.sub(r"\s+(?:in|on|using)\s+(?:brave|chrome|youtube|spotify|browser).*", "", song_query).strip()

            return {
                "intent": "MEDIA_PLAY",
                "emotion": "relaxed",
                "media_query": song_query,
                "action_required": True,
                "normalized_text": clean,
                "guidance": "Play the requested media or song on YouTube or browser."
            }

        # Fast direct system actions (0ms LLM overhead)
        for pat in self.screenshot_patterns:
            if re.search(pat, lower):
                return {
                    "intent": "SCREENSHOT",
                    "emotion": "neutral",
                    "action_required": True,
                    "normalized_text": clean,
                    "guidance": "Take a desktop screenshot immediately."
                }

        for pat in self.desktop_patterns:
            if re.search(pat, lower):
                return {
                    "intent": "DESKTOP_TOGGLE",
                    "emotion": "neutral",
                    "action_required": True,
                    "normalized_text": clean,
                    "guidance": "Toggle desktop display."
                }

        for pat in self.mute_patterns:
            if re.search(pat, lower):
                return {
                    "intent": "VOLUME_MUTE",
                    "emotion": "neutral",
                    "action_required": True,
                    "normalized_text": clean,
                    "guidance": "Toggle audio mute."
                }

        # Claude AI Web Automation intent (0ms LLM overhead)
        for pat in self.claude_patterns:
            m = re.search(pat, lower)
            if m:
                c_prompt = m.group(1).strip()
                return {
                    "intent": "CLAUDE_PROMPT",
                    "emotion": "neutral",
                    "claude_prompt": c_prompt,
                    "action_required": True,
                    "normalized_text": clean,
                    "guidance": "Open Claude AI in Chrome and submit user prompt."
                }

        # Chrome new tab intent (0ms LLM overhead)
        for pat in self.chrome_tab_patterns:
            m = re.search(pat, lower)
            if m:
                target = m.group(1).strip() if (m.lastindex and m.group(1)) else ""
                return {
                    "intent": "CHROME_TAB",
                    "emotion": "neutral",
                    "target": target,
                    "action_required": True,
                    "normalized_text": clean,
                    "guidance": "Open a new tab in Google Chrome."
                }

        # Executive Briefing intent (0ms LLM overhead)
        for pat in self.briefing_patterns:
            if re.search(pat, lower):
                return {
                    "intent": "BRIEFING",
                    "emotion": "informative",
                    "action_required": True,
                    "normalized_text": clean,
                    "guidance": "Deliver the executive briefing."
                }

        # 7. Analyze Emotional State
        detected_emotions = []
        for emotion, patterns in self.emotion_patterns.items():
            for pat in patterns:
                if re.search(pat, lower):
                    detected_emotions.append(emotion)
                    break

        primary_emotion = "neutral"
        if "frustrated" in detected_emotions:
            primary_emotion = "frustrated"
        elif "stressed" in detected_emotions:
            primary_emotion = "stressed"
        elif "urgent" in detected_emotions:
            primary_emotion = "urgent"
        elif "excited" in detected_emotions:
            primary_emotion = "excited"
        elif "confused" in detected_emotions:
            primary_emotion = "confused"

        # Determine general intent
        system_keywords = ["open", "close", "launch", "file", "folder", "volume", "battery", "cpu", "ram", "script", "powershell", "search", "create"]
        if any(kw in lower for kw in system_keywords):
            intent = "SYSTEM_CONTROL"
        elif len(clean.split()) > 40 or "explain in depth" in lower:
            intent = "DEEP_REASONING"
        else:
            intent = "CONVERSATION"

        guidance_map = {
            "frustrated": "The user is frustrated or dissatisfied. Be calm, supportive, cut all filler, and solve the problem cleanly.",
            "stressed": "The user is stressed or overwhelmed. Be comforting, clear, and reassuring. Keep speech gentle and brief.",
            "urgent": "The user is in a hurry. Skip pleasantries. Execute immediately with 1-sentence confirmation.",
            "excited": "The user is enthusiastic. Match their positive energy!",
            "confused": "The user is confused. Be clear and give a direct explanation.",
            "neutral": "Direct, helpful, and concise conversational assistant."
        }

        return {
            "intent": intent,
            "emotion": primary_emotion,
            "action_required": intent in ["SYSTEM_CONTROL", "NEWS", "MEDIA_PLAY"],
            "normalized_text": clean,
            "guidance": guidance_map.get(primary_emotion, guidance_map["neutral"])
        }

if __name__ == "__main__":
    analyzer = CognitiveIntentAnalyzer()
    samples = [
        "exit.",
        "No, stop the program, exit out of this shell, you can go home now.",
        "search for today's latest news.",
        "Can you give me a whole summary of it like what is happening currently in India and what Rahul Gandhi is trying to do to Marco Rubio and S.J. Shankar is trying to defend everything out.",
        "All right.",
        "Do the same thing on braille."
    ]
    for s in samples:
        res = analyzer.analyze(s)
        print(f"\nPrompt: '{s}'")
        print(f"  -> Normalized: '{res['normalized_text']}'")
        print(f"  -> Intent:     {res['intent']}")
