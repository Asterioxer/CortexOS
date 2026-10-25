"""
Cognitive Sentiment & Affective Tone Tracker for CortexOS.
Integrates emotional awareness, urgency scoring, and speech normalization from voice-lab.
"""
import re
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

@dataclass
class SentimentProfile:
    primary_emotion: str
    urgency_score: float
    recommended_temperature: float
    recommended_style: str
    is_exit_intent: bool = False
    is_stop_intent: bool = False
    detected_intents: List[str] = field(default_factory=list)

class CognitiveSentimentTracker:
    """
    Real-time emotional and intentional tone analyzer.
    Adjusts cognitive temperature, response style, and working memory posture.
    """
    def __init__(self):
        # Exit / Shutdown trigger phrases
        self.exit_patterns = [
            r"^(exit|quit|stop the program|exit the program|close the assistant|go home|shutdown|terminate|bye)\b",
            r"\b(exit the session|stop running|quit now|exit out)\b"
        ]

        # Stop / Barge-in trigger phrases
        self.stop_patterns = [
            r"^(stop|quiet|shut up|hush|silence|cancel|never mind|wait|hold on|pause)\b",
            r"\b(shut up|be quiet|stop talking|cancel that|hold on)\b"
        ]

        # Emotion patterns
        self.emotion_patterns = {
            "frustrated": [
                r"\b(annoyed|frustrated|angry|damn|shit|fuck|broken|hate|stupid|idiot|stop failing|tired of|doesn't work|fail|bad|crap|worthless|terrible)\b",
                r"!{2,}",
                r"\b(why (is it|isn't it|won't it|cant you))\b",
                r"\b(not working|does not work|keeps failing)\b"
            ],
            "urgent": [
                r"\b(quick|hurry|asap|urgent|now|immediately|fast|rush|emergency|right now|at once|straight away)\b"
            ],
            "excited": [
                r"\b(awesome|great|amazing|love|cool|wow|fantastic|incredible|super|yay|lets go|brilliant|legend)\b"
            ],
            "stressed": [
                r"\b(stressed|overwhelmed|exhausted|burnout|too much|cant handle|tired|anxious|headache)\b"
            ],
            "confused": [
                r"\b(confused|lost|dont understand|what do you mean|huh|how come|no idea|cant see|cant tell)\b"
            ],
            "grateful": [
                r"\b(thanks|thank you|appreciate|helpful|nice work|good job|perfect|cheers)\b"
            ]
        }

    def normalize_speech(self, text: str) -> str:
        """Fixes common phonetic transcription errors from microphone."""
        if not text:
            return ""
        t = text
        # Browser / tech names
        t = re.sub(r"\b(braver|braille)\b", "brave", t, flags=re.IGNORECASE)
        t = re.sub(r"\b(power shell|powershell)\b", "powershell", t, flags=re.IGNORECASE)
        t = re.sub(r"\b(vs code|visual studio code)\b", "vscode", t, flags=re.IGNORECASE)
        t = re.sub(r"\b(cortex os|cortex-os)\b", "CortexOS", t, flags=re.IGNORECASE)
        t = re.sub(r"\b(jarvis|jarvis's)\b", "JARVIS", t, flags=re.IGNORECASE)
        return t.strip()

    def analyze(self, user_input: str) -> SentimentProfile:
        """
        Analyzes emotional tone, urgency score, and recommended cognitive parameters.
        """
        clean_text = self.normalize_speech(user_input)
        lower = clean_text.lower()
        
        # 1. Exit / Stop Intent
        is_exit = any(bool(re.search(p, lower)) for p in self.exit_patterns)
        is_stop = any(bool(re.search(p, lower)) for p in self.stop_patterns)

        # 2. Score emotions
        emotion_scores: Dict[str, int] = {}
        detected_intents: List[str] = []

        for emotion, patterns in self.emotion_patterns.items():
            count = 0
            for pattern in patterns:
                if re.search(pattern, lower):
                    count += 1
            if count > 0:
                emotion_scores[emotion] = count

        # Primary emotion resolution
        primary = "neutral"
        if emotion_scores:
            primary = max(emotion_scores.items(), key=lambda x: x[1])[0]

        # 3. Urgency and Temperature mapping
        urgency = 0.2
        rec_temp = 0.40
        style = "rich_technical"

        if primary == "frustrated":
            urgency = 0.85
            rec_temp = 0.15
            style = "concise_direct"
            detected_intents.append("frustration_mitigation")
        elif primary == "urgent":
            urgency = 0.95
            rec_temp = 0.10
            style = "rapid_execution"
            detected_intents.append("high_priority")
        elif primary == "stressed":
            urgency = 0.60
            rec_temp = 0.25
            style = "calm_empathetic"
            detected_intents.append("stress_relief")
        elif primary == "excited":
            urgency = 0.40
            rec_temp = 0.55
            style = "energetic_affirming"
            detected_intents.append("high_engagement")
        elif primary == "confused":
            urgency = 0.50
            rec_temp = 0.30
            style = "structured_explanatory"
            detected_intents.append("clarification")
        elif primary == "grateful":
            urgency = 0.10
            rec_temp = 0.45
            style = "courteous_concise"

        if is_exit:
            detected_intents.append("exit_intent")
        if is_stop:
            detected_intents.append("stop_barge_in")

        return SentimentProfile(
            primary_emotion=primary,
            urgency_score=round(urgency, 2),
            recommended_temperature=rec_temp,
            recommended_style=style,
            is_exit_intent=is_exit,
            is_stop_intent=is_stop,
            detected_intents=detected_intents
        )
