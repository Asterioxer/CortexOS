import psutil
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.responses import HTMLResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Ensure cortex root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cortex.main import build_cortex_stack
from cortex.embodiment.voice import voice_engine

app = FastAPI(title="CortexOS Real-Time Cognitive Dashboard")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared cognitive stack
stack = build_cortex_stack()
active_websockets: List[WebSocket] = []
ambient_daemon_active = False

# Pydantic Request Models
class BlockUpdateRequest(BaseModel):
    value: str

class GraphAssertRequest(BaseModel):
    source: str
    target: str
    relation: str
    layer: str = "semantic"
    provenance: str = "user_asserted"

class SkillRunRequest(BaseModel):
    name: str
    args: Optional[List[str]] = None

class SkillSynthesizeRequest(BaseModel):
    description: str

class GovernanceTestRequest(BaseModel):
    action: str
    resource: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class CheckpointCreateRequest(BaseModel):
    label: Optional[str] = "manual"

class CheckpointRestoreRequest(BaseModel):
    task_id: str
    label: Optional[str] = "pre"

class TerminalRunRequest(BaseModel):
    command: str
    timeout: Optional[int] = 30

class MediaControlRequest(BaseModel):
    command: str = "toggle"

class VoiceSpeakRequest(BaseModel):
    text: str
    persona: Optional[str] = None

class VoicePersonaRequest(BaseModel):
    persona: str

class VoiceToggleRequest(BaseModel):
    enabled: bool


HTML_DASHBOARD = r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CortexOS | Autonomous Cognitive Operating System</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&family=Orbitron:wght@500;700;900&display=swap" rel="stylesheet">
    <!-- Three.js + OrbitControls + Tween.js for Super Smooth 3D Graphics -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/tween.js/18.6.4/tween.umd.js"></script>
    <style>
        :root {
            --bg-dark: #070a13;
            --bg-card: rgba(13, 20, 36, 0.72);
            --bg-card-hover: rgba(18, 28, 51, 0.85);
            --border-panel: rgba(56, 189, 248, 0.22);
            --border-glow: rgba(56, 189, 248, 0.5);
            --border-subtle: rgba(255, 255, 255, 0.08);
            --accent-cyan: #00e5ff;
            --accent-blue: #38bdf8;
            --accent-green: #10b981;
            --accent-yellow: #f59e0b;
            --accent-red: #ef4444;
            --accent-purple: #c084fc;
            --text-main: #f1f5f9;
            --text-dim: #94a3b8;
            --font-mono: 'JetBrains Mono', monospace;
            --font-display: 'Orbitron', 'Inter', sans-serif;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background: #060911;
            color: var(--text-main);
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            position: relative;
            user-select: none;
        }

        /* Ambient Background Canvas */
        #webgl-bg-canvas {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: 0;
            pointer-events: none;
        }

        /* Cybernetic Header HUD */
        header {
            height: 64px;
            background: rgba(10, 15, 29, 0.88);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--border-panel);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 20px;
            z-index: 20;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.55);
        }
        .header-left {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .btn-side-toggle {
            background: rgba(0, 229, 255, 0.12);
            border: 1px solid var(--border-panel);
            color: var(--accent-cyan);
            width: 36px;
            height: 36px;
            border-radius: 8px;
            font-family: var(--font-mono);
            font-size: 1.1rem;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .btn-side-toggle:hover {
            background: rgba(0, 229, 255, 0.25);
            box-shadow: 0 0 12px rgba(0, 229, 255, 0.35);
            transform: scale(1.05);
        }
        .btn-side-toggle.active {
            background: rgba(0, 229, 255, 0.25);
            border-color: var(--accent-cyan);
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            font-family: var(--font-display);
            font-weight: 700;
            font-size: 1.05rem;
            color: var(--accent-cyan);
            letter-spacing: 1px;
            text-shadow: 0 0 14px rgba(0, 229, 255, 0.45);
        }
        .conn-pill {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.72rem;
            font-family: var(--font-mono);
            padding: 3px 8px;
            border-radius: 12px;
            background: rgba(16, 185, 129, 0.15);
            border: 1px solid rgba(16, 185, 129, 0.3);
            color: var(--accent-green);
            transition: all 0.3s ease;
        }
        .conn-pill.reconnecting {
            background: rgba(245, 158, 11, 0.15);
            border-color: rgba(245, 158, 11, 0.3);
            color: var(--accent-yellow);
        }
        .conn-pill.offline {
            background: rgba(239, 68, 68, 0.15);
            border-color: rgba(239, 68, 68, 0.3);
            color: var(--accent-red);
        }
        .pulse-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: currentColor;
            box-shadow: 0 0 8px currentColor;
            animation: pulse-glow 2s infinite;
        }
        @keyframes pulse-glow {
            0% { transform: scale(0.85); opacity: 0.6; }
            50% { transform: scale(1.2); opacity: 1; }
            100% { transform: scale(0.85); opacity: 0.6; }
        }

        .ticker-bar {
            display: flex;
            align-items: center;
            gap: 12px;
            font-family: var(--font-mono);
            font-size: 0.82rem;
        }
        .ticker-item {
            display: flex;
            align-items: center;
            gap: 6px;
            background: rgba(18, 28, 51, 0.75);
            backdrop-filter: blur(8px);
            padding: 5px 12px;
            border-radius: 8px;
            border: 1px solid var(--border-panel);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
        }
        .ticker-item span.val { color: var(--accent-cyan); font-weight: 700; text-shadow: 0 0 8px rgba(0, 229, 255, 0.3); }

        /* Media Equalizer Animation */
        .eq-bars {
            display: inline-flex;
            align-items: flex-end;
            gap: 2px;
            height: 12px;
            margin-right: 4px;
        }
        .eq-bar {
            width: 2px;
            background: var(--accent-cyan);
            border-radius: 1px;
            animation: eq-bounce 1.2s ease-in-out infinite;
        }
        .eq-bar:nth-child(2) { animation-delay: 0.2s; }
        .eq-bar:nth-child(3) { animation-delay: 0.4s; }
        @keyframes eq-bounce { 0%, 100% { height: 3px; } 50% { height: 12px; } }

        .btn-ambient {
            background: rgba(0, 229, 255, 0.12);
            border: 1px solid var(--accent-cyan);
            color: var(--accent-cyan);
            padding: 6px 14px;
            border-radius: 8px;
            font-family: var(--font-mono);
            font-size: 0.78rem;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .btn-ambient:hover { background: rgba(0, 229, 255, 0.25); box-shadow: 0 0 12px rgba(0, 229, 255, 0.3); }
        .btn-ambient.active {
            background: rgba(16, 185, 129, 0.2);
            border-color: var(--accent-green);
            color: var(--accent-green);
            box-shadow: 0 0 12px rgba(16, 185, 129, 0.3);
        }
        .btn-sleep {
            background: rgba(192, 132, 252, 0.15);
            border: 1px solid var(--accent-purple);
            color: var(--accent-purple);
            padding: 6px 14px;
            border-radius: 8px;
            font-family: var(--font-mono);
            font-size: 0.78rem;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .btn-sleep:hover { background: rgba(192, 132, 252, 0.3); box-shadow: 0 0 14px rgba(192, 132, 252, 0.35); }
        .btn-panic {
            background: rgba(239, 68, 68, 0.18);
            border: 1px solid var(--accent-red);
            color: var(--accent-red);
            padding: 6px 14px;
            border-radius: 8px;
            font-family: var(--font-mono);
            font-size: 0.78rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-panic:hover { background: rgba(239, 68, 68, 0.35); box-shadow: 0 0 16px rgba(239, 68, 68, 0.4); }

        /* Main Workspace Layout with Smooth Collapsible Sidebar */
        main {
            flex: 1;
            display: grid;
            grid-template-columns: 270px 1fr;
            overflow: hidden;
            position: relative;
            z-index: 10;
            transition: grid-template-columns 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        }
        main.sidebar-collapsed {
            grid-template-columns: 0px 1fr !important;
        }
        main.sidebar-collapsed aside.nav-sidebar {
            padding: 0;
            overflow: hidden;
            border-right: none;
            opacity: 0;
            pointer-events: none;
            width: 0;
        }

        /* Sidebar Navigation */
        aside.nav-sidebar {
            background: rgba(10, 15, 29, 0.78);
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            border-right: 1px solid var(--border-panel);
            padding: 20px 16px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            z-index: 15;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .nav-btn {
            background: transparent;
            border: 1px solid transparent;
            color: var(--text-dim);
            padding: 12px 18px;
            border-radius: 10px;
            text-align: left;
            font-size: 0.92rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .nav-btn .nav-label {
            display: flex;
            align-items: center;
            gap: 14px;
        }
        .nav-btn .icon { font-size: 1.15rem; transition: transform 0.2s ease; }
        .nav-btn .kbd-hint {
            font-size: 0.68rem;
            font-family: var(--font-mono);
            color: rgba(255, 255, 255, 0.25);
            background: rgba(255, 255, 255, 0.05);
            padding: 2px 6px;
            border-radius: 4px;
        }
        .nav-btn:hover {
            background: rgba(0, 229, 255, 0.08);
            color: var(--text-main);
            transform: translateX(4px);
        }
        .nav-btn:hover .icon { transform: scale(1.2); }
        .nav-btn.active {
            background: linear-gradient(90deg, rgba(0, 229, 255, 0.18), rgba(56, 189, 248, 0.08));
            color: var(--accent-cyan);
            border: 1px solid rgba(0, 229, 255, 0.35);
            box-shadow: 0 0 20px rgba(0, 229, 255, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.1);
            font-weight: 600;
        }
        .nav-btn.active .kbd-hint { color: var(--accent-cyan); background: rgba(0, 229, 255, 0.15); }

        /* Panes Container */
        .content-area {
            flex: 1;
            height: 100%;
            overflow: hidden;
            position: relative;
        }
        .pane-view {
            display: none;
            width: 100%;
            height: 100%;
        }

        /* 3D Holographic Card Tilt Effect */
        .tilt-card {
            transform-style: preserve-3d;
            perspective: 1000px;
            transition: transform 0.12s ease-out, box-shadow 0.2s ease, border-color 0.2s ease;
            position: relative;
            overflow: hidden;
        }
        .tilt-card::after {
            content: '';
            position: absolute;
            inset: 0;
            background: radial-gradient(circle at var(--mouse-x, 50%) var(--mouse-y, 50%), rgba(0, 229, 255, 0.12), transparent 70%);
            opacity: 0;
            transition: opacity 0.3s;
            pointer-events: none;
        }
        .tilt-card:hover::after { opacity: 1; }
        .tilt-card:hover {
            border-color: var(--border-glow);
            box-shadow: 0 16px 36px -8px rgba(0, 229, 255, 0.2), 0 0 16px rgba(56, 189, 248, 0.15);
        }

        /* PANE 1: Cognitive Stage */
        #pane-stage.active {
            display: grid;
            grid-template-columns: 1fr 370px;
            height: 100%;
            overflow: hidden;
        }
        section.chat-center {
            display: flex;
            flex-direction: column;
            height: 100%;
            overflow: hidden;
            background: rgba(8, 12, 24, 0.45);
            position: relative;
        }
        .chat-messages {
            flex: 1;
            padding: 26px 30px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 20px;
            user-select: text;
        }
        .message-bubble {
            max-width: 84%;
            padding: 16px 22px;
            border-radius: 14px;
            line-height: 1.6;
            font-size: 0.96rem;
            animation: fadeIn 0.25s cubic-bezier(0.16, 1, 0.3, 1);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
            position: relative;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px) scale(0.98); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }
        .msg-user {
            align-self: flex-end;
            background: linear-gradient(135deg, #1d4ed8, #2563eb);
            color: #fff;
            border-bottom-right-radius: 3px;
            border: 1px solid rgba(255, 255, 255, 0.18);
            box-shadow: 0 8px 22px rgba(37, 99, 235, 0.35);
        }
        .msg-cortex {
            align-self: flex-start;
            background: rgba(18, 28, 51, 0.88);
            border: 1px solid var(--border-panel);
            color: var(--text-main);
            border-bottom-left-radius: 3px;
        }

        /* Real-Time Thinking State Bubble */
        .thinking-bubble {
            align-self: flex-start;
            display: flex;
            align-items: center;
            gap: 14px;
            background: rgba(18, 28, 51, 0.85);
            border: 1px solid rgba(0, 229, 255, 0.4);
            border-radius: 14px;
            padding: 14px 20px;
            box-shadow: 0 0 20px rgba(0, 229, 255, 0.2);
            animation: fadeIn 0.2s ease;
        }
        .thinking-spinner {
            position: relative;
            width: 24px;
            height: 24px;
        }
        .spinner-ring {
            width: 100%;
            height: 100%;
            border: 2px solid transparent;
            border-top-color: var(--accent-cyan);
            border-bottom-color: var(--accent-purple);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        .spinner-core {
            position: absolute;
            top: 50%; left: 50%;
            width: 8px; height: 8px;
            background: var(--accent-cyan);
            border-radius: 50%;
            transform: translate(-50%, -50%);
            box-shadow: 0 0 8px var(--accent-cyan);
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .thinking-text { display: flex; flex-direction: column; gap: 3px; }
        .thinking-title {
            font-family: var(--font-display);
            font-size: 0.78rem;
            color: var(--accent-cyan);
            letter-spacing: 0.5px;
            font-weight: 700;
        }
        .thinking-step {
            font-family: var(--font-mono);
            font-size: 0.82rem;
            color: var(--text-dim);
            transition: all 0.3s ease;
        }

        /* Markdown Code Boxes in Chat */
        .code-block-wrap {
            position: relative;
            margin: 10px 0;
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--border-panel);
            background: #000;
        }
        .code-block-head {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(15, 23, 42, 0.95);
            padding: 6px 12px;
            font-family: var(--font-mono);
            font-size: 0.72rem;
            color: var(--text-dim);
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }
        .btn-copy {
            background: rgba(0, 229, 255, 0.1);
            border: 1px solid rgba(0, 229, 255, 0.3);
            color: var(--accent-cyan);
            padding: 2px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-family: var(--font-mono);
            font-size: 0.7rem;
            transition: all 0.2s;
        }
        .btn-copy:hover { background: rgba(0, 229, 255, 0.25); }
        .code-block-body {
            padding: 12px 14px;
            font-family: var(--font-mono);
            font-size: 0.82rem;
            color: #38bdf8;
            overflow-x: auto;
            white-space: pre;
            line-height: 1.45;
        }

        /* Perspective Thought Details */
        .thought-card {
            margin-top: 12px;
            background: rgba(10, 16, 30, 0.92);
            border-left: 3px solid var(--accent-cyan);
            border-radius: 6px;
            padding: 10px 14px;
            font-size: 0.84rem;
            font-family: var(--font-mono);
            color: var(--text-dim);
            box-shadow: inset 0 0 14px rgba(0, 0, 0, 0.5);
        }
        .thought-card summary { cursor: pointer; color: var(--accent-cyan); font-weight: 600; outline: none; }
        .persp-badge {
            display: inline-block;
            font-size: 0.72rem;
            padding: 1px 6px;
            border-radius: 4px;
            font-weight: 700;
            margin-right: 6px;
        }
        .persp-analytic { background: rgba(56, 189, 248, 0.2); color: var(--accent-blue); }
        .persp-pragmatic { background: rgba(16, 185, 129, 0.2); color: var(--accent-green); }
        .persp-cautious { background: rgba(245, 158, 11, 0.2); color: var(--accent-yellow); }

        /* Quick-Prompt Suggestion Chips */
        .quick-chips {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 26px 0;
            overflow-x: auto;
            scrollbar-width: none;
            background: rgba(10, 15, 29, 0.9);
        }
        .quick-chip {
            background: rgba(18, 28, 51, 0.8);
            border: 1px solid var(--border-panel);
            color: var(--text-dim);
            padding: 5px 12px;
            border-radius: 14px;
            font-size: 0.78rem;
            font-family: var(--font-mono);
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .quick-chip:hover {
            background: rgba(0, 229, 255, 0.15);
            border-color: var(--accent-cyan);
            color: var(--accent-cyan);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 229, 255, 0.2);
        }

        .chat-input-bar {
            padding: 14px 26px 18px;
            background: rgba(10, 15, 29, 0.95);
            backdrop-filter: blur(18px);
            border-top: 1px solid var(--border-panel);
            display: flex;
            gap: 12px;
            z-index: 5;
        }
        .chat-input {
            flex: 1;
            background: rgba(18, 28, 51, 0.8);
            border: 1px solid var(--border-panel);
            color: #fff;
            padding: 14px 20px;
            border-radius: 10px;
            font-size: 0.95rem;
            outline: none;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            user-select: text;
        }
        .chat-input:focus {
            border-color: var(--accent-cyan);
            box-shadow: 0 0 16px rgba(0, 229, 255, 0.25);
            background: rgba(22, 34, 60, 0.95);
        }
        .btn-send {
            background: linear-gradient(135deg, #0284c7, #0ea5e9);
            color: #fff;
            border: none;
            padding: 0 28px;
            border-radius: 10px;
            font-weight: 600;
            font-size: 0.95rem;
            cursor: pointer;
            transition: all 0.2s;
            box-shadow: 0 4px 14px rgba(14, 165, 233, 0.35);
        }
        .btn-send:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(14, 165, 233, 0.5);
        }
        .btn-mic {
            background: rgba(18, 28, 51, 0.85);
            border: 1px solid var(--border-panel);
            color: var(--accent-cyan);
            width: 48px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.15rem;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }
        .btn-mic:hover {
            border-color: var(--accent-cyan);
            box-shadow: 0 0 14px rgba(0, 229, 255, 0.3);
            transform: scale(1.05);
        }
        .btn-mic.listening {
            background: rgba(239, 68, 68, 0.25);
            border-color: var(--accent-red);
            color: #fff;
            animation: micPulse 1.2s infinite ease-in-out;
        }
        @keyframes micPulse {
            0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.6); }
            70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
            100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
        }
        .btn-voice-bubble {
            background: rgba(0, 229, 255, 0.12);
            border: 1px solid rgba(0, 229, 255, 0.35);
            color: var(--accent-cyan);
            border-radius: 4px;
            padding: 3px 9px;
            font-size: 0.72rem;
            font-family: var(--font-mono);
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 5px;
            margin-top: 8px;
            transition: all 0.15s ease;
        }
        .btn-voice-bubble:hover {
            background: rgba(0, 229, 255, 0.25);
            box-shadow: 0 0 10px rgba(0, 229, 255, 0.3);
        }
        .btn-persp-voice {
            background: rgba(0, 229, 255, 0.1);
            border: 1px solid rgba(0, 229, 255, 0.25);
            color: var(--accent-cyan);
            border-radius: 3px;
            padding: 1px 6px;
            font-size: 0.65rem;
            font-family: var(--font-mono);
            cursor: pointer;
            margin-left: 8px;
            transition: all 0.15s ease;
        }
        .btn-persp-voice:hover {
            background: rgba(0, 229, 255, 0.28);
            box-shadow: 0 0 8px rgba(0, 229, 255, 0.3);
        }

        /* Cognitive Stage Sidebar / Inspector */
        aside.state-inspector {
            background: rgba(10, 15, 29, 0.75);
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            border-left: 1px solid var(--border-panel);
            padding: 22px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 16px;
            z-index: 5;
        }
        .block-card {
            background: var(--bg-card);
            border: 1px solid var(--border-panel);
            border-radius: 10px;
            padding: 14px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
            user-select: text;
        }
        .block-card h4 {
            font-family: var(--font-mono);
            font-size: 0.82rem;
            color: var(--accent-purple);
            text-transform: uppercase;
            margin-bottom: 6px;
            letter-spacing: 0.5px;
        }
        .block-card p {
            font-size: 0.84rem;
            color: var(--text-dim);
            line-height: 1.45;
            max-height: 110px;
            overflow-y: auto;
        }

        /* Generic Scrollable Pane */
        .pane-scrollable {
            display: none;
            flex-direction: column;
            height: 100%;
            overflow-y: auto;
            scroll-behavior: smooth;
            padding: 28px 36px 120px 36px;
            gap: 24px;
            z-index: 5;
            user-select: text;
        }
        .pane-scrollable.active { display: flex; }
        .btn-subtle {
            background: rgba(18, 28, 51, 0.7);
            border: 1px solid var(--border-panel);
            color: var(--accent-cyan);
            padding: 4px 10px;
            border-radius: 6px;
            font-family: var(--font-mono);
            font-size: 0.74rem;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }
        .btn-subtle:hover {
            background: rgba(0, 229, 255, 0.2);
            border-color: var(--accent-cyan);
            box-shadow: 0 0 10px rgba(0, 229, 255, 0.3);
            transform: scale(1.02);
        }
        .pane-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 1px solid var(--border-panel);
            padding-bottom: 18px;
        }
        .pane-title {
            font-size: 1.45rem;
            font-weight: 700;
            color: var(--text-main);
            display: flex;
            align-items: center;
            gap: 12px;
            font-family: var(--font-display);
            letter-spacing: 0.5px;
        }
        .pane-desc {
            font-size: 0.88rem;
            color: var(--text-dim);
            margin-top: 6px;
        }
        .btn-action {
            background: rgba(0, 229, 255, 0.12);
            border: 1px solid var(--accent-cyan);
            color: var(--accent-cyan);
            padding: 8px 18px;
            border-radius: 8px;
            font-family: var(--font-mono);
            font-size: 0.84rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .btn-action:hover {
            background: rgba(0, 229, 255, 0.25);
            box-shadow: 0 0 16px rgba(0, 229, 255, 0.35);
            transform: translateY(-1px);
        }

        /* Working Memory Styles */
        .mem-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 24px;
        }
        .mem-card {
            background: var(--bg-card);
            border: 1px solid var(--border-panel);
            border-radius: 12px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 14px;
            backdrop-filter: blur(12px);
        }
        .mem-card-head {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .mem-label {
            font-family: var(--font-mono);
            font-size: 0.98rem;
            font-weight: 700;
            color: var(--accent-cyan);
        }
        .mem-char-badge {
            font-family: var(--font-mono);
            font-size: 0.78rem;
            padding: 3px 10px;
            border-radius: 12px;
            background: rgba(18, 28, 51, 0.85);
            border: 1px solid var(--border-panel);
            color: var(--text-dim);
        }
        .mem-progress {
            width: 100%;
            height: 5px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 3px;
            overflow: hidden;
        }
        .mem-progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #00e5ff, #3b82f6);
            width: 0%;
            transition: width 0.3s ease;
            box-shadow: 0 0 8px rgba(0, 229, 255, 0.5);
        }
        .mem-textarea {
            width: 100%;
            height: 180px;
            background: rgba(8, 12, 24, 0.75);
            border: 1px solid var(--border-panel);
            border-radius: 8px;
            padding: 14px;
            font-family: var(--font-mono);
            font-size: 0.86rem;
            color: var(--text-main);
            outline: none;
            resize: vertical;
            line-height: 1.45;
            user-select: text;
        }
        .mem-textarea:focus { border-color: var(--accent-cyan); box-shadow: 0 0 12px rgba(0, 229, 255, 0.2); }
        .mem-card-foot {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .mem-status {
            font-size: 0.8rem;
            color: var(--accent-green);
            display: none;
        }

        /* 3D Bi-Temporal Graph Pane */
        .graph-card {
            background: var(--bg-card);
            border: 1px solid var(--border-panel);
            border-radius: 12px;
            padding: 22px;
            display: flex;
            flex-direction: column;
            gap: 16px;
            backdrop-filter: blur(14px);
        }
        #graph-3d-container {
            position: relative;
            width: 100%;
            height: 440px;
            border-radius: 10px;
            overflow: hidden;
            border: 1px solid var(--border-panel);
            background: radial-gradient(circle at center, #0e172a 0%, #060911 100%);
            box-shadow: inset 0 0 40px rgba(0, 0, 0, 0.8);
            transition: height 0.3s ease;
        }
        #graph-3d-container.maximized {
            height: 680px;
        }
        #graph-3d-viewport {
            width: 100%;
            height: 100%;
        }
        #graph-3d-hud {
            position: absolute;
            top: 14px;
            left: 18px;
            font-family: var(--font-mono);
            font-size: 0.78rem;
            color: var(--accent-cyan);
            background: rgba(10, 15, 29, 0.8);
            padding: 6px 14px;
            border-radius: 8px;
            border: 1px solid var(--border-panel);
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .graph-search-input {
            background: rgba(6, 9, 17, 0.8);
            border: 1px solid rgba(0, 229, 255, 0.3);
            border-radius: 4px;
            color: #fff;
            padding: 3px 8px;
            font-family: var(--font-mono);
            font-size: 0.74rem;
            outline: none;
            width: 140px;
        }
        .graph-search-input:focus { border-color: var(--accent-cyan); box-shadow: 0 0 8px rgba(0, 229, 255, 0.3); }
        #graph-node-details {
            position: absolute;
            bottom: 14px;
            right: 18px;
            background: rgba(10, 15, 29, 0.9);
            border: 1px solid var(--border-panel);
            padding: 12px 18px;
            border-radius: 8px;
            font-family: var(--font-mono);
            font-size: 0.8rem;
            color: #fff;
            display: none;
            backdrop-filter: blur(12px);
            max-width: 320px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
        }
        .filter-tags { display: flex; gap: 8px; flex-wrap: wrap; }
        .filter-tag {
            background: rgba(18, 28, 51, 0.85);
            border: 1px solid var(--border-panel);
            color: var(--text-dim);
            padding: 5px 12px;
            border-radius: 6px;
            font-size: 0.8rem;
            cursor: pointer;
            font-family: var(--font-mono);
            transition: all 0.2s;
        }
        .filter-tag:hover { color: var(--text-main); }
        .filter-tag.active {
            background: rgba(0, 229, 255, 0.2);
            border-color: var(--accent-cyan);
            color: var(--accent-cyan);
            box-shadow: 0 0 10px rgba(0, 229, 255, 0.3);
        }
        .data-table-wrap {
            max-height: 380px;
            overflow-y: auto;
            border: 1px solid var(--border-panel);
            border-radius: 8px;
            background: rgba(8, 12, 24, 0.6);
        }
        table.cortex-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.84rem;
            font-family: var(--font-mono);
        }
        table.cortex-table th {
            background: rgba(10, 15, 29, 0.95);
            padding: 12px 14px;
            text-align: left;
            border-bottom: 1px solid var(--border-panel);
            color: var(--text-dim);
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 2;
        }
        table.cortex-table td {
            padding: 10px 14px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
            color: var(--text-main);
        }
        table.cortex-table tr:hover td { background: rgba(0, 229, 255, 0.06); }
        .layer-badge {
            font-size: 0.74rem;
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .layer-semantic { background: rgba(0, 229, 255, 0.18); color: var(--accent-cyan); }
        .layer-causal { background: rgba(245, 158, 11, 0.18); color: var(--accent-yellow); }
        .layer-temporal { background: rgba(192, 132, 252, 0.18); color: var(--accent-purple); }
        .layer-entity { background: rgba(16, 185, 129, 0.18); color: var(--accent-green); }

        .form-row {
            display: grid;
            grid-template-columns: repeat(4, 1fr) auto;
            gap: 12px;
            align-items: center;
        }
        .form-input {
            background: rgba(8, 12, 24, 0.8);
            border: 1px solid var(--border-panel);
            color: #fff;
            padding: 10px 14px;
            border-radius: 8px;
            font-size: 0.84rem;
            font-family: var(--font-mono);
            outline: none;
        }
        .form-input:focus { border-color: var(--accent-cyan); box-shadow: 0 0 10px rgba(0, 229, 255, 0.2); }

        /* Skills Pane */
        .curriculum-banner {
            background: linear-gradient(90deg, rgba(56, 189, 248, 0.15), rgba(192, 132, 252, 0.15));
            border: 1px solid rgba(56, 189, 248, 0.3);
            border-radius: 10px;
            padding: 16px 22px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            backdrop-filter: blur(12px);
        }
        .curriculum-title {
            font-size: 0.88rem;
            font-weight: 700;
            color: var(--accent-cyan);
            font-family: var(--font-mono);
        }
        .curriculum-task {
            font-size: 0.94rem;
            color: var(--text-main);
            margin-top: 4px;
        }
        .synth-bar {
            display: flex;
            gap: 14px;
            background: var(--bg-card);
            border: 1px solid var(--border-panel);
            padding: 16px;
            border-radius: 10px;
            backdrop-filter: blur(12px);
        }
        .synth-input {
            flex: 1;
            background: rgba(8, 12, 24, 0.8);
            border: 1px solid var(--border-panel);
            color: #fff;
            padding: 12px 18px;
            border-radius: 8px;
            font-size: 0.92rem;
            outline: none;
        }
        .synth-input:focus { border-color: var(--accent-cyan); box-shadow: 0 0 12px rgba(0, 229, 255, 0.25); }
        .skills-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 24px;
        }
        .skill-card {
            background: var(--bg-card);
            border: 1px solid var(--border-panel);
            border-radius: 12px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 14px;
            backdrop-filter: blur(12px);
        }
        .skill-head {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .skill-name {
            font-family: var(--font-mono);
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--accent-cyan);
        }
        .skill-score {
            font-family: var(--font-mono);
            font-size: 0.82rem;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 6px;
            background: rgba(16, 185, 129, 0.2);
            color: var(--accent-green);
            border: 1px solid rgba(16, 185, 129, 0.35);
        }
        .skill-doc {
            font-size: 0.88rem;
            color: var(--text-dim);
            line-height: 1.45;
        }
        .skill-accordions {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .skill-details {
            background: rgba(8, 12, 24, 0.65);
            border: 1px solid var(--border-panel);
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 0.82rem;
            font-family: var(--font-mono);
        }
        .skill-details summary { cursor: pointer; color: var(--accent-purple); font-weight: 600; outline: none; }
        .skill-code-box {
            margin-top: 10px;
            max-height: 220px;
            overflow-y: auto;
            white-space: pre;
            color: #38bdf8;
            font-size: 0.8rem;
        }
        .skill-output-box {
            display: none;
            background: #000;
            border: 1px solid rgba(16, 185, 129, 0.35);
            border-radius: 8px;
            padding: 12px 16px;
            font-family: var(--font-mono);
            font-size: 0.82rem;
            color: var(--accent-green);
            max-height: 200px;
            overflow-y: auto;
            white-space: pre-wrap;
            box-shadow: inset 0 0 16px rgba(0, 0, 0, 0.8);
        }

        /* Governance Pane */
        .gov-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
        }
        .gov-card {
            background: var(--bg-card);
            border: 1px solid var(--border-panel);
            border-radius: 12px;
            padding: 22px;
            display: flex;
            flex-direction: column;
            gap: 16px;
            backdrop-filter: blur(12px);
        }
        .gov-card h3 {
            font-size: 1.05rem;
            font-weight: 600;
            color: var(--accent-cyan);
            font-family: var(--font-mono);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .code-display {
            background: rgba(8, 12, 24, 0.85);
            border: 1px solid var(--border-panel);
            border-radius: 8px;
            padding: 16px;
            font-family: var(--font-mono);
            font-size: 0.82rem;
            color: var(--text-dim);
            max-height: 280px;
            overflow-y: auto;
            white-space: pre;
        }
        .pdp-tester {
            display: flex;
            flex-direction: column;
            gap: 14px;
        }
        .pdp-result {
            display: none;
            padding: 14px;
            border-radius: 8px;
            font-family: var(--font-mono);
            font-size: 0.86rem;
        }
        .verdict-allow { background: rgba(16, 185, 129, 0.18); border: 1px solid var(--accent-green); color: var(--accent-green); }
        .verdict-escalate { background: rgba(245, 158, 11, 0.18); border: 1px solid var(--accent-yellow); color: var(--accent-yellow); }
        .verdict-deny { background: rgba(239, 68, 68, 0.18); border: 1px solid var(--accent-red); color: var(--accent-red); }

        .btn-restore {
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid var(--accent-red);
            color: var(--accent-red);
            padding: 4px 10px;
            border-radius: 6px;
            font-family: var(--font-mono);
            font-size: 0.76rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-restore:hover { background: rgba(239, 68, 68, 0.35); }

        /* ==================== 6. EXECUTION & DAEMONS PANE STYLES ==================== */
        .exec-card {
            background: var(--bg-card);
            border: 1px solid var(--border-panel);
            border-radius: 12px;
            padding: 22px;
            display: flex;
            flex-direction: column;
            gap: 16px;
            backdrop-filter: blur(14px);
        }
        /* 9-Stage Pipeline Stepper */
        .pipeline-stepper {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 14px;
        }
        .pipe-stage-card {
            background: rgba(8, 12, 24, 0.7);
            border: 1px solid var(--border-panel);
            border-radius: 10px;
            padding: 14px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            position: relative;
        }
        .pipe-stage-card:hover {
            border-color: var(--accent-cyan);
            background: rgba(18, 28, 51, 0.85);
            box-shadow: 0 4px 16px rgba(0, 229, 255, 0.15);
        }
        .pipe-stage-head {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .pipe-num {
            font-family: var(--font-display);
            font-size: 0.76rem;
            color: var(--accent-cyan);
            font-weight: 700;
        }
        .pipe-status-pill {
            font-family: var(--font-mono);
            font-size: 0.68rem;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 700;
            text-transform: uppercase;
        }
        .pipe-status-active { background: rgba(0, 229, 255, 0.2); color: var(--accent-cyan); }
        .pipe-status-completed { background: rgba(16, 185, 129, 0.2); color: var(--accent-green); }
        .pipe-status-ready { background: rgba(192, 132, 252, 0.2); color: var(--accent-purple); }
        .pipe-status-nominal { background: rgba(56, 189, 248, 0.2); color: var(--accent-blue); }
        .pipe-status-enforcing { background: rgba(245, 158, 11, 0.2); color: var(--accent-yellow); }
        .pipe-status-isolated { background: rgba(168, 85, 247, 0.2); color: var(--accent-purple); }
        .pipe-status-pinned { background: rgba(16, 185, 129, 0.2); color: var(--accent-green); }
        .pipe-status-synchronized { background: rgba(0, 229, 255, 0.2); color: var(--accent-cyan); }
        .pipe-title {
            font-family: var(--font-mono);
            font-size: 0.88rem;
            font-weight: 700;
            color: var(--text-main);
        }
        .pipe-comp {
            font-size: 0.74rem;
            color: var(--accent-blue);
            font-family: var(--font-mono);
        }
        .pipe-desc {
            font-size: 0.78rem;
            color: var(--text-dim);
            line-height: 1.4;
        }

        /* Live Terminal Box */
        .terminal-quick-cmds {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }
        .term-preset-btn {
            background: rgba(18, 28, 51, 0.85);
            border: 1px solid var(--border-panel);
            color: var(--text-dim);
            padding: 4px 10px;
            border-radius: 6px;
            font-family: var(--font-mono);
            font-size: 0.74rem;
            cursor: pointer;
            transition: all 0.15s;
        }
        .term-preset-btn:hover {
            color: var(--accent-cyan);
            border-color: var(--accent-cyan);
            background: rgba(0, 229, 255, 0.12);
        }
        .terminal-input-bar {
            display: flex;
            align-items: center;
            gap: 12px;
            background: rgba(6, 9, 17, 0.95);
            border: 1px solid var(--border-panel);
            border-radius: 8px;
            padding: 8px 14px;
        }
        .term-prompt {
            font-family: var(--font-mono);
            font-size: 0.84rem;
            color: var(--accent-green);
            font-weight: 700;
            white-space: nowrap;
        }
        .terminal-input {
            flex: 1;
            background: transparent;
            border: none;
            color: #fff;
            font-family: var(--font-mono);
            font-size: 0.86rem;
            outline: none;
        }
        .terminal-screen {
            background: #000;
            border: 1px solid rgba(0, 229, 255, 0.3);
            border-radius: 8px;
            padding: 16px;
            font-family: var(--font-mono);
            font-size: 0.82rem;
            max-height: 260px;
            overflow-y: auto;
            white-space: pre-wrap;
            line-height: 1.5;
            box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.9);
        }
        .term-line-cmd { color: var(--accent-cyan); font-weight: 700; margin-top: 6px; }
        .term-line-stdout { color: var(--accent-green); }
        .term-line-stderr { color: var(--accent-red); }
        .term-line-meta { color: var(--text-dim); font-size: 0.74rem; margin-top: 4px; }

        /* Daemons Grid */
        .daemons-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 18px;
        }
        .daemon-card {
            background: var(--bg-card);
            border: 1px solid var(--border-panel);
            border-radius: 10px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            backdrop-filter: blur(12px);
        }
        .daemon-head {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .daemon-name {
            font-family: var(--font-mono);
            font-size: 0.84rem;
            font-weight: 700;
            color: var(--accent-cyan);
        }
        .daemon-badge {
            font-family: var(--font-mono);
            font-size: 0.7rem;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 700;
        }
        .daemon-running { background: rgba(16, 185, 129, 0.2); color: var(--accent-green); }
        .daemon-nominal { background: rgba(0, 229, 255, 0.2); color: var(--accent-cyan); }
        .daemon-paused { background: rgba(245, 158, 11, 0.2); color: var(--accent-yellow); }
        .daemon-metric {
            display: flex;
            justify-content: space-between;
            font-family: var(--font-mono);
            font-size: 0.76rem;
            color: var(--text-dim);
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
            padding-bottom: 4px;
        }
        .daemon-metric span.val { color: var(--text-main); font-weight: 600; }

        /* Process Search Input */
        .proc-search-input {
            background: rgba(6, 9, 17, 0.85);
            border: 1px solid var(--border-panel);
            color: #fff;
            padding: 6px 12px;
            border-radius: 6px;
            font-family: var(--font-mono);
            font-size: 0.8rem;
            outline: none;
            width: 200px;
        }
        .proc-search-input:focus { border-color: var(--accent-cyan); box-shadow: 0 0 10px rgba(0, 229, 255, 0.25); }

        /* Responsive Breakpoints */
        @media (max-width: 1080px) {
            .pipeline-stepper { grid-template-columns: repeat(2, 1fr); }
            .daemons-grid { grid-template-columns: repeat(2, 1fr); }
            .mem-grid, .skills-grid, .gov-grid { grid-template-columns: 1fr; }
        }
        @media (max-width: 768px) {
            main { grid-template-columns: 1fr; }
            aside.nav-sidebar { display: none; }
            .pipeline-stepper { grid-template-columns: 1fr; }
            .daemons-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <!-- Persistent Ambient 3D Three.js Canvas -->
    <canvas id="webgl-bg-canvas"></canvas>

    <header>
        <div class="header-left">
            <button class="btn-side-toggle" id="btn-side-toggle" onclick="toggleSidebar()" title="Toggle Navigation Sidebar (Ctrl+B)">☰</button>
            <div class="brand">
                <div class="conn-pill" id="conn-pill">
                    <div class="pulse-dot"></div>
                    <span id="conn-text">SYNCED</span>
                </div>
                <span>CORTEX-OS // COGNITIVE RUNTIME</span>
            </div>
        </div>
        <div class="ticker-bar">
            <div class="ticker-item">TICK <span class="val" id="tick-id">#0</span></div>
            <div class="ticker-item">H(W) <span class="val" id="entropy-val">1.00</span></div>
            <div class="ticker-item">TEMP <span class="val" id="temp-val">0.40</span></div>
            <div class="ticker-item">UQ <span class="val" id="uq-val" style="color:var(--accent-green)">PASS</span></div>
            <div class="ticker-item" id="ticker-media" style="cursor:pointer;" onclick="pollLiveMedia()" title="Click to refresh audio">
                <div class="eq-bars">
                    <span class="eq-bar"></span>
                    <span class="eq-bar"></span>
                    <span class="eq-bar"></span>
                </div>
                <span class="val" id="media-ticker-text" style="max-width:160px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">Detecting media...</span>
                <button onclick="controlMedia('previous', event)" style="background:transparent; border:none; color:var(--text-dim); cursor:pointer; font-size:0.75rem;" title="Previous track">⏮</button>
                <button onclick="controlMedia('toggle', event)" style="background:transparent; border:none; color:var(--accent-cyan); cursor:pointer; font-size:0.85rem;" title="Play/Pause">⏯</button>
                <button onclick="controlMedia('next', event)" style="background:transparent; border:none; color:var(--text-dim); cursor:pointer; font-size:0.75rem;" title="Next track">⏭</button>
            </div>
            <div class="ticker-item" id="ticker-voice" title="Neural Voice Persona & Instant Barge-In Control">
                <span id="voice-status-icon">🎙️</span>
                <select id="voice-persona-select" onchange="switchVoicePersona(this.value)" style="background:rgba(13,20,36,0.85); border:1px solid var(--border-panel); color:var(--accent-cyan); font-family:var(--font-mono); font-size:0.72rem; border-radius:4px; padding:2px 5px; outline:none; cursor:pointer;">
                    <option value="jarvis">JARVIS (Baritone)</option>
                    <option value="friday">Friday (Companion)</option>
                    <option value="christopher">Christopher (Studio)</option>
                    <option value="edith">Edith (Tactical)</option>
                    <option value="neerja">Neerja (Indian EN)</option>
                    <option value="jenny">Jenny (Warm)</option>
                    <option value="guy">Guy (Direct)</option>
                </select>
                <button id="btn-voice-toggle" onclick="toggleVoiceSpeech()" style="background:transparent; border:none; color:var(--accent-cyan); cursor:pointer; font-size:0.85rem;" title="Toggle Speech Output">🔊</button>
                <button id="btn-voice-bargein" onclick="bargeInStopVoice()" style="background:rgba(239,68,68,0.25); border:1px solid rgba(239,68,68,0.5); color:var(--accent-red); cursor:pointer; font-size:0.68rem; font-weight:700; border-radius:3px; padding:2px 6px;" title="Instant Sub-10ms Barge-In (Stop Speaking)">HALT</button>
                <button id="btn-voice-greet" onclick="triggerSystemGreeting()" style="background:rgba(0,229,255,0.12); border:1px solid rgba(0,229,255,0.35); color:var(--accent-cyan); cursor:pointer; font-size:0.68rem; font-weight:700; border-radius:3px; padding:2px 7px;" title="Interactive Voice Welcome">👋 Greet</button>
            </div>
            <button class="btn-ambient" id="btn-ambient" onclick="toggleAmbient()">AMBIENT: OFF</button>
            <button class="btn-sleep" onclick="triggerSleep()">DIGITAL SLEEP</button>
            <button class="btn-panic" id="btn-panic" onclick="togglePanicKillswitch()">🚨 PANIC STOP</button>
        </div>
    </header>

    <main>
        <!-- Sidebar Navigation -->
        <aside class="nav-sidebar">
            <button class="nav-btn active" id="tab-stage" onclick="switchTab('stage')">
                <span class="nav-label"><span class="icon">💬</span> Cognitive Stage</span>
                <span class="kbd-hint">^1</span>
            </button>
            <button class="nav-btn" id="tab-memory" onclick="switchTab('memory')">
                <span class="nav-label"><span class="icon">🧠</span> Working Memory</span>
                <span class="kbd-hint">^2</span>
            </button>
            <button class="nav-btn" id="tab-graph" onclick="switchTab('graph')">
                <span class="nav-label"><span class="icon">🕸️</span> Bi-Temporal Graph</span>
                <span class="kbd-hint">^3</span>
            </button>
            <button class="nav-btn" id="tab-skills" onclick="switchTab('skills')">
                <span class="nav-label"><span class="icon">⚡</span> Skill Crystallizer</span>
                <span class="kbd-hint">^4</span>
            </button>
            <button class="nav-btn" id="tab-governance" onclick="switchTab('governance')">
                <span class="nav-label"><span class="icon">🛡️</span> Cedar Governance</span>
                <span class="kbd-hint">^5</span>
            </button>
            <button class="nav-btn" id="tab-execution" onclick="switchTab('execution')">
                <span class="nav-label"><span class="icon">⚙️</span> Execution & Daemons</span>
                <span class="kbd-hint">^6</span>
            </button>
        </aside>

        <!-- Main Content Area with 6 Interchangeable Views -->
        <div class="content-area">
            
            <!-- PANE 1: COGNITIVE STAGE (Active Interactive Chat + Real-Time Telemetry Inspector) -->
            <div id="pane-stage" class="pane-view active">
                <section class="chat-center">
                    <div class="chat-messages" id="chat-messages">
                        <div class="message-bubble msg-cortex">
                            I am CortexOS, your laptop-resident cognitive operating system. My 4-tier memory substrate, GWA cognitive tick, and autopoietic procedural skill engine are synchronized and ready. How can I assist you?
                        </div>
                    </div>

                    <!-- Quick-Prompt Suggestion Chips -->
                    <div class="quick-chips">
                        <div class="quick-chip" onclick="quickPrompt('tell me about my system')">🖥️ System Telemetry</div>
                        <div class="quick-chip" onclick="quickPrompt('which applications are open')">📱 Open Applications</div>
                        <div class="quick-chip" onclick="quickPrompt('which song is being played')">🎵 Active Song</div>
                        <div class="quick-chip" onclick="quickPrompt('audit working tree')">🔍 Audit Git Tree</div>
                        <div class="quick-chip" onclick="switchTab('execution')">⚙️ View Execution Pipeline</div>
                        <div class="quick-chip" onclick="triggerSleep()">💤 Digital Sleep</div>
                    </div>

                    <div class="chat-input-bar">
                        <button id="btn-mic-toggle" class="btn-mic" onclick="toggleVoiceRecognition()" title="Voice Input (Click or Hold to Speak with Microphone)">
                            <span id="mic-icon">🎙️</span>
                        </button>
                        <input type="text" class="chat-input" id="chat-input" placeholder="Ask CortexOS or speak with your mic (e.g. 'tell me about my system', 'which song is playing?')..." onkeydown="if(event.key==='Enter') sendMessage()">
                        <button class="btn-send" onclick="sendMessage()">Send</button>
                    </div>
                </section>
                <aside class="state-inspector">
                    <!-- 3D Global Workspace Satellite Core Visualizer -->
                    <div id="stage-3d-box" style="height: 150px; position:relative; border-radius:10px; overflow:hidden; background:rgba(6,9,17,0.7); border:1px solid var(--border-panel); box-shadow: inset 0 0 20px rgba(0,0,0,0.8);">
                        <canvas id="stage-3d-canvas" style="width:100%; height:100%;"></canvas>
                        <div style="position:absolute; bottom:6px; left:10px; font-size:0.68rem; color:var(--accent-cyan); font-family:var(--font-mono);">GWA Orbit: 3 Perspectives (Analytic, Pragmatic, Cautious)</div>
                    </div>

                    <h3 style="font-size:0.9rem; letter-spacing:0.5px; text-transform:uppercase; color:var(--accent-cyan); font-family:var(--font-mono);">Working Memory</h3>
                    <div class="block-card tilt-card">
                        <h4>persona_self</h4>
                        <p id="block-persona">Autonomous cognitive OS embodied on this laptop.</p>
                    </div>
                    <div class="block-card tilt-card">
                        <h4>workspace_state</h4>
                        <p id="block-workspace">Active repository root monitored.</p>
                    </div>
                    <div class="block-card tilt-card">
                        <h4>scratchpad_stm</h4>
                        <p id="block-scratchpad">Awaiting prompt.</p>
                    </div>
                </aside>
            </div>

            <!-- PANE 2: WORKING MEMORY (Letta 4 Self-Editing In-Context Blocks) -->
            <div id="pane-memory" class="pane-scrollable">
                <div class="pane-header">
                    <div>
                        <div class="pane-title"><span>🧠</span> Working Memory Blocks (Letta Architecture)</div>
                        <div class="pane-desc">4 character-bounded self-editing in-context blocks injected at every cognitive tick. Edit and patch values directly below.</div>
                    </div>
                    <button class="btn-action" onclick="loadMemoryPane()"><span>🔄</span> Refresh Blocks</button>
                </div>

                <!-- 3D Holographic Memory Prisms Header Box -->
                <div id="memory-3d-box" style="height: 130px; border-radius: 10px; overflow: hidden; background: rgba(6, 9, 17, 0.7); border: 1px solid var(--border-panel); position: relative; box-shadow: inset 0 0 20px rgba(0,0,0,0.8);">
                    <canvas id="memory-3d-canvas" style="width: 100%; height: 100%;"></canvas>
                    <div style="position: absolute; top: 8px; left: 14px; font-size: 0.76rem; color: var(--accent-cyan); font-family: var(--font-mono);">3D Holographic Memory Prisms (Character Capacity & Allocation)</div>
                </div>

                <div class="mem-grid">
                    <!-- persona_self -->
                    <div class="mem-card tilt-card">
                        <div class="mem-card-head">
                            <span class="mem-label">persona_self</span>
                            <span class="mem-char-badge" id="badge-persona_self">0 / 2000 chars</span>
                        </div>
                        <div class="mem-progress"><div class="mem-progress-bar" id="bar-persona_self"></div></div>
                        <textarea class="mem-textarea" id="mem-persona_self" placeholder="Core self-model directives..."></textarea>
                        <div class="mem-card-foot">
                            <button class="btn-action" onclick="saveBlock('persona_self')">💾 Save & Patch Block</button>
                            <span class="mem-status" id="status-persona_self">✓ Saved</span>
                        </div>
                    </div>

                    <!-- human_profile -->
                    <div class="mem-card tilt-card">
                        <div class="mem-card-head">
                            <span class="mem-label">human_profile</span>
                            <span class="mem-char-badge" id="badge-human_profile">0 / 1500 chars</span>
                        </div>
                        <div class="mem-progress"><div class="mem-progress-bar" id="bar-human_profile"></div></div>
                        <textarea class="mem-textarea" id="mem-human_profile" placeholder="User identity and preferences..."></textarea>
                        <div class="mem-card-foot">
                            <button class="btn-action" onclick="saveBlock('human_profile')">💾 Save & Patch Block</button>
                            <span class="mem-status" id="status-human_profile">✓ Saved</span>
                        </div>
                    </div>

                    <!-- workspace_state -->
                    <div class="mem-card tilt-card">
                        <div class="mem-card-head">
                            <span class="mem-label">workspace_state</span>
                            <span class="mem-char-badge" id="badge-workspace_state">0 / 2000 chars</span>
                        </div>
                        <div class="mem-progress"><div class="mem-progress-bar" id="bar-workspace_state"></div></div>
                        <textarea class="mem-textarea" id="mem-workspace_state" placeholder="Workspace status..."></textarea>
                        <div class="mem-card-foot">
                            <button class="btn-action" onclick="saveBlock('workspace_state')">💾 Save & Patch Block</button>
                            <span class="mem-status" id="status-workspace_state">✓ Saved</span>
                        </div>
                    </div>

                    <!-- scratchpad_stm -->
                    <div class="mem-card tilt-card">
                        <div class="mem-card-head">
                            <span class="mem-label">scratchpad_stm</span>
                            <span class="mem-char-badge" id="badge-scratchpad_stm">0 / 1000 chars</span>
                        </div>
                        <div class="mem-progress"><div class="mem-progress-bar" id="bar-scratchpad_stm"></div></div>
                        <textarea class="mem-textarea" id="mem-scratchpad_stm" placeholder="Short-term scratchpad memory..."></textarea>
                        <div class="mem-card-foot">
                            <button class="btn-action" onclick="saveBlock('scratchpad_stm')">💾 Save & Patch Block</button>
                            <span class="mem-status" id="status-scratchpad_stm">✓ Saved</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- PANE 3: BI-TEMPORAL KNOWLEDGE GRAPH & ENGRAMS (Full 3D WebGL Multi-Graph) -->
            <div id="pane-graph" class="pane-scrollable">
                <div class="pane-header">
                    <div>
                        <div class="pane-title"><span>🕸️</span> Bi-Temporal Knowledge Multi-Graph (MAGMA)</div>
                        <div class="pane-desc">4-layer graph substrate (Semantic, Temporal, Causal, Entity) with 3D force physics, valid_from/valid_to time horizons, and atomic sleep engrams.</div>
                    </div>
                    <button class="btn-action" onclick="loadGraphPane()"><span>🔄</span> Reload 3D Graph</button>
                </div>

                <!-- Assert New Edge Form -->
                <div class="graph-card tilt-card">
                    <h3 style="font-size:0.95rem; font-family:var(--font-mono); color:var(--accent-cyan);">➕ Assert New Fact / Relation</h3>
                    <div class="form-row">
                        <input type="text" class="form-input" id="assert-source" placeholder="Source Node (e.g. soham)">
                        <input type="text" class="form-input" id="assert-relation" placeholder="Relation (e.g. listens_to)">
                        <input type="text" class="form-input" id="assert-target" placeholder="Target Node (e.g. Maria Ermakova)">
                        <select class="form-input" id="assert-layer">
                            <option value="semantic">Semantic</option>
                            <option value="causal">Causal</option>
                            <option value="temporal">Temporal</option>
                            <option value="entity">Entity</option>
                        </select>
                        <button class="btn-action" onclick="assertFact()">Assert Fact</button>
                    </div>
                </div>

                <!-- Interactive 3D WebGL MAGMA Multi-Graph Canvas -->
                <div class="graph-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h3 style="font-size:0.95rem; font-family:var(--font-mono); color:var(--accent-cyan);">🌐 Interactive 3D WebGL Multi-Graph Universe</h3>
                        <div style="display:flex; gap:10px;">
                            <button class="btn-ambient" id="btn-graph-maximize" onclick="toggleGraphMaximize()" style="font-size:0.75rem; padding:4px 10px;">⛶ Expand</button>
                            <button class="btn-ambient" onclick="reset3DGraphCamera()" style="font-size:0.75rem; padding:4px 10px;">↺ Center</button>
                        </div>
                    </div>
                    <div id="graph-3d-container">
                        <div id="graph-3d-viewport"></div>
                        <div id="graph-3d-hud">
                            <span>🔍 Find Node:</span>
                            <input type="text" class="graph-search-input" id="graph-search-input" placeholder="Type node name..." oninput="searchGraphNode(this.value)">
                            <span style="opacity:0.7; font-size:0.72rem;">Drag: Rotate | Wheel: Zoom | Click: Inspect</span>
                        </div>
                        <div id="graph-node-details"></div>
                    </div>
                    <!-- Hidden legacy 2D canvas preserved for tests and fallback -->
                    <canvas id="graph-canvas" width="800" height="220" style="display:none;"></canvas>
                </div>

                <div class="graph-layout" style="display:grid; grid-template-columns: 1.2fr 0.8fr; gap:24px;">
                    <!-- Graph Relations Table -->
                    <div class="graph-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <h3 style="font-size:0.95rem; font-family:var(--font-mono); color:var(--text-main);">Verified Multi-Graph Relations</h3>
                            <div class="filter-tags">
                                <span class="filter-tag active" onclick="filterGraph('all', this)">ALL (<span id="count-all">0</span>)</span>
                                <span class="filter-tag" onclick="filterGraph('semantic', this)">SEMANTIC</span>
                                <span class="filter-tag" onclick="filterGraph('causal', this)">CAUSAL</span>
                                <span class="filter-tag" onclick="filterGraph('temporal', this)">TEMPORAL</span>
                            </div>
                        </div>
                        <div class="data-table-wrap">
                            <table class="cortex-table">
                                <thead>
                                    <tr>
                                        <th>Relation</th>
                                        <th>Layer</th>
                                        <th>Provenance</th>
                                    </tr>
                                </thead>
                                <tbody id="graph-edges-body">
                                    <tr><td colspan="3" style="text-align:center; color:var(--text-dim);">Loading relations...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Atomic Engrams -->
                    <div class="graph-card">
                        <h3 style="font-size:0.95rem; font-family:var(--font-mono); color:var(--text-main);">Atomic Engrams (Digital Sleep)</h3>
                        <div class="data-table-wrap">
                            <table class="cortex-table">
                                <thead>
                                    <tr>
                                        <th>Type</th>
                                        <th>Statement</th>
                                    </tr>
                                </thead>
                                <tbody id="engrams-body">
                                    <tr><td colspan="2" style="text-align:center; color:var(--text-dim);">Loading engrams...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- PANE 4: SKILL CRYSTALLIZER -->
            <div id="pane-skills" class="pane-scrollable">
                <div class="pane-header">
                    <div>
                        <div class="pane-title"><span>⚡</span> Autopoietic Skill Crystallizer (FRIDAY / Voyager)</div>
                        <div class="pane-desc">Autonomous tool synthesis, isolated kernel sandbox execution with Git checkpointing, Critic evaluation, and ATLAS procedural pamphlets.</div>
                    </div>
                    <button class="btn-action" onclick="loadSkillsPane()"><span>🔄</span> Refresh Library</button>
                </div>

                <!-- Curriculum Challenge Banner -->
                <div class="curriculum-banner tilt-card">
                    <div>
                        <div class="curriculum-title">🎯 ACTIVE CURRICULUM CHALLENGE (<span id="curr-level">BEGINNER</span>)</div>
                        <div class="curriculum-task" id="curr-task">Inspect active Git branch and verify working tree status.</div>
                    </div>
                    <button class="btn-action" onclick="synthesizeCurriculum()">Synthesize Tool for Goal</button>
                </div>

                <!-- Synthesize Form -->
                <div class="synth-bar tilt-card">
                    <input type="text" class="synth-input" id="synth-desc" placeholder="Describe a novel skill, automation, or task to synthesize and sandbox (e.g. Inspect GPU VRAM utilization)...">
                    <button class="btn-action" onclick="synthesizeCustomSkill()">⚡ Synthesize & Crystallize</button>
                </div>

                <!-- Crystallized Skills Catalog -->
                <div class="skills-grid" id="skills-grid">
                    <!-- Populated dynamically via JS -->
                </div>
            </div>

            <!-- PANE 5: CEDAR GOVERNANCE & CHECKPOINTS -->
            <div id="pane-governance" class="pane-scrollable">
                <div class="pane-header">
                    <div>
                        <div class="pane-title"><span>🛡️</span> Defense-in-Depth Governance & Kernel Sandboxing</div>
                        <div class="pane-desc">Sub-millisecond Policy Decision Point (ALLOW, ESCALATE, DENY) and deterministic shadow Git checkpoints (`refs/checkpoints/`).</div>
                    </div>
                    <div style="display:flex; gap:10px;">
                        <button class="btn-action" onclick="createManualCheckpoint()">📸 Take Snapshot</button>
                        <button class="btn-action" onclick="loadGovernancePane()"><span>🔄</span> Refresh</button>
                    </div>
                </div>

                <div class="gov-grid">
                    <!-- Sub-0.1ms Interactive PDP Tester -->
                    <div class="gov-card tilt-card">
                        <h3><span>⚡</span> Policy Decision Point (PDP) Live Tester</h3>
                        <div class="pdp-tester">
                            <label style="font-size:0.8rem; color:var(--text-dim); font-family:var(--font-mono);">Action to Test:</label>
                            <select class="form-input" id="pdp-action">
                                <option value="file_read">file_read (Somatosensory / Inspect)</option>
                                <option value="git_status">git_status (Read-Only)</option>
                                <option value="get_hardware_telemetry">get_hardware_telemetry (Sensor)</option>
                                <option value="command_run">command_run (Subprocess Command)</option>
                                <option value="git_push_remote">git_push_remote (Irreversible Push)</option>
                                <option value="delete_directory_recursive">delete_directory_recursive (Destructive)</option>
                            </select>
                            <label style="font-size:0.8rem; color:var(--text-dim); font-family:var(--font-mono);">Target Resource Path:</label>
                            <input type="text" class="form-input" id="pdp-resource" value="c:/Users/soham/Desktop/self-conscious/cortex/server.py">
                            <button class="btn-action" onclick="testPolicy()">Evaluate Policy Gate</button>
                            <div class="pdp-result" id="pdp-result-box"></div>
                        </div>
                    </div>

                    <!-- Cedar Policy Rules -->
                    <div class="gov-card tilt-card">
                        <h3><span>📜</span> Cedar Policy-as-Code (<span id="gov-cedar-path">config/policies.cedar</span>)</h3>
                        <div class="code-display" id="gov-policy-code">Loading Cedar policies...</div>
                    </div>
                </div>

                <!-- Git Shadow Checkpoints & Working Tree Diff -->
                <div class="gov-grid">
                    <!-- Checkpoints Table -->
                    <div class="gov-card tilt-card">
                        <h3><span>📌</span> Pinned Shadow Git Checkpoints (refs/checkpoints/)</h3>
                        <div class="data-table-wrap">
                            <table class="cortex-table">
                                <thead>
                                    <tr>
                                        <th>Ref / Label</th>
                                        <th>Commit SHA</th>
                                        <th>Action</th>
                                    </tr>
                                </thead>
                                <tbody id="checkpoints-body">
                                    <tr><td colspan="3" style="text-align:center; color:var(--text-dim);">Loading shadow checkpoints...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Working Tree Diff -->
                    <div class="gov-card tilt-card">
                        <h3><span>🔍</span> Working Tree Diff & Integrity Monitor</h3>
                        <div class="code-display" id="gov-working-diff" style="color:#10b981;">Checking working tree...</div>
                    </div>
                </div>
            </div>

            <!-- PANE 6: LIVE EXECUTION, DAEMONS & PIPELINE MONITOR -->
            <div id="pane-execution" class="pane-scrollable">
                <div class="pane-header">
                    <div>
                        <div class="pane-title"><span>⚙️</span> Live Execution, Daemons & Cognitive Pipeline Trace</div>
                        <div class="pane-desc">Real-time terminal execution in governed sandbox, background daemon inspection, child process tree monitoring, and 9-stage cognitive pipeline flow.</div>
                    </div>
                    <div style="display:flex; gap:10px; align-items:center;">
                        <button class="btn-action" onclick="loadExecutionPane()"><span>🔄</span> Refresh Telemetry</button>
                        <button class="btn-action" onclick="clearTerminalScreen()"><span>🧹</span> Clear Terminal</button>
                    </div>
                </div>

                <!-- 1. The 9-Stage Cognitive Pipeline Architecture Stepper -->
                <div class="exec-card tilt-card" id="card-pipeline-wrap">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                        <h3 style="font-size:0.95rem; font-family:var(--font-mono); color:var(--accent-cyan); display:flex; align-items:center; gap:8px;">
                            <span>🌌</span> End-to-End Cognitive Execution Pipeline Architecture
                        </h3>
                        <div style="display:flex; align-items:center; gap:12px;">
                            <span style="font-size:0.75rem; color:var(--text-dim); font-family:var(--font-mono);">Discrete Dynamical Flow (9 Verified Stages)</span>
                            <button class="btn-subtle" onclick="toggleSectionCollapse('pipeline-card-body', this)"><span>▾</span> Collapse</button>
                        </div>
                    </div>
                    <div id="pipeline-card-body" style="display:block;">
                        <div class="pipeline-stepper" id="pipeline-stepper-box">
                            <div class="pipe-stage-card">
                                <div class="pipe-stage-head"><span class="pipe-num">STAGE 01</span><span class="pipe-status-pill pipe-status-active">ACTIVE</span></div>
                                <div class="pipe-title">Somatosensory Perception</div>
                                <div class="pipe-comp">SystemSomatosensory & GSMTC Bus</div>
                                <div class="pipe-desc">Live Windows CPU/RAM/GPU VRAM telemetry, focused foreground window, and audio playback tracking.</div>
                            </div>
                            <div class="pipe-stage-card">
                                <div class="pipe-stage-head"><span class="pipe-num">STAGE 02</span><span class="pipe-status-pill pipe-status-completed">COMPLETED</span></div>
                                <div class="pipe-title">Working Memory & LTM Retrieval</div>
                                <div class="pipe-comp">Letta Blocks & Bi-Temporal MAGMA Graph</div>
                                <div class="pipe-desc">4 in-context character-bounded memory blocks compiled into prompt + Hybrid vector RAG.</div>
                            </div>
                            <div class="pipe-stage-card">
                                <div class="pipe-stage-head"><span class="pipe-num">STAGE 03</span><span class="pipe-status-pill pipe-status-ready">READY</span></div>
                                <div class="pipe-title">Tri-Perspective Divergent Generation</div>
                                <div class="pipe-comp">Global Workspace Agent Swarm</div>
                                <div class="pipe-desc">Specialist Nodes: Analytic, Pragmatic, and Cautious candidate thought generation.</div>
                            </div>
                            <div class="pipe-stage-card">
                                <div class="pipe-stage-head"><span class="pipe-num">STAGE 04</span><span class="pipe-status-pill pipe-status-ready">READY</span></div>
                                <div class="pipe-title">Convergent Critic & Shannon Entropy</div>
                                <div class="pipe-comp">IntrinsicDriveMonitor H(W)</div>
                                <div class="pipe-desc">Scoring proposals (-5 to +5). Entropy H(W) deadlock breaker dynamically regulates temperature.</div>
                            </div>
                            <div class="pipe-stage-card">
                                <div class="pipe-stage-head"><span class="pipe-num">STAGE 05</span><span class="pipe-status-pill pipe-status-nominal">NOMINAL</span></div>
                                <div class="pipe-title">Metacognitive Dual-Process Router</div>
                                <div class="pipe-comp">System 1 Reflex & HASSUM System 2 Gate</div>
                                <div class="pipe-desc">Sub-100ms fast reflex for hardware/media; HASSUM uncertainty gate for deep reasoning.</div>
                            </div>
                            <div class="pipe-stage-card">
                                <div class="pipe-stage-head"><span class="pipe-num">STAGE 06</span><span class="pipe-status-pill pipe-status-enforcing">ENFORCING</span></div>
                                <div class="pipe-title">Cedar Policy Decision Point (PDP)</div>
                                <div class="pipe-comp">PolicyEngine (policies.cedar)</div>
                                <div class="pipe-desc">Sub-0.1ms deterministic security gates: ALLOW, ESCALATE (human-in-the-loop hold), DENY.</div>
                            </div>
                            <div class="pipe-stage-card">
                                <div class="pipe-stage-head"><span class="pipe-num">STAGE 07</span><span class="pipe-status-pill pipe-status-pinned">PINNED</span></div>
                                <div class="pipe-title">Deterministic Shadow Git Checkpoint</div>
                                <div class="pipe-comp">GitShadowCheckpointManager</div>
                                <div class="pipe-desc">Captures modified and untracked workspace files into refs/checkpoints/ in &lt;1s.</div>
                            </div>
                            <div class="pipe-stage-card">
                                <div class="pipe-stage-head"><span class="pipe-num">STAGE 08</span><span class="pipe-status-pill pipe-status-isolated">ISOLATED</span></div>
                                <div class="pipe-title">Sandboxed OS Subprocess Execution</div>
                                <div class="pipe-comp">SandboxRunner</div>
                                <div class="pipe-desc">Sanitized execution environment with automated rollback on non-zero exit code or policy fault.</div>
                            </div>
                            <div class="pipe-stage-card">
                                <div class="pipe-stage-head"><span class="pipe-num">STAGE 09</span><span class="pipe-status-pill pipe-status-synchronized">SYNCHRONIZED</span></div>
                                <div class="pipe-title">State Transition & Memory Patch</div>
                                <div class="pipe-comp">Letta Core Memory Re-think & Episodic WAL</div>
                                <div class="pipe-desc">In-context memory block patch and lossless Tier 1 append-only SQLite transaction commit.</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- 2. Live Interactive Terminal & Subprocess Executor -->
                <div class="exec-card tilt-card" id="card-terminal-wrap">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                        <h3 style="font-size:0.95rem; font-family:var(--font-mono); color:var(--accent-cyan); display:flex; align-items:center; gap:8px;">
                            <span>💻</span> Live Sandboxed Terminal & Subprocess Runner
                        </h3>
                        <div style="display:flex; align-items:center; gap:12px;">
                            <span style="font-size:0.75rem; color:var(--text-dim); font-family:var(--font-mono);">Cedar Governed | Shadow Checkpointed | Auto-Rollback</span>
                            <button class="btn-subtle" onclick="toggleSectionCollapse('terminal-card-body', this)"><span>▾</span> Collapse</button>
                        </div>
                    </div>
                    <div id="terminal-card-body" style="display:flex; flex-direction:column; gap:14px;">
                        <div class="terminal-quick-cmds">
                            <span style="font-size:0.75rem; color:var(--text-dim); font-family:var(--font-mono); margin-right:4px;">Presets:</span>
                            <button class="term-preset-btn" onclick="runPresetTerminal('python -c &quot;import psutil; print(psutil.virtual_memory())&quot;')">psutil.virtual_memory()</button>
                            <button class="term-preset-btn" onclick="runPresetTerminal('git status')">git status</button>
                            <button class="term-preset-btn" onclick="runPresetTerminal('python cortex/skills/library/system_telemetry_reporter.py')">system_telemetry_reporter</button>
                            <button class="term-preset-btn" onclick="runPresetTerminal('python cortex/skills/library/process_resource_optimizer.py')">process_resource_optimizer</button>
                            <button class="term-preset-btn" onclick="runPresetTerminal('dir')">dir</button>
                        </div>
                        <div class="terminal-input-bar">
                            <span class="term-prompt">cortex@laptop:~$</span>
                            <input type="text" class="terminal-input" id="terminal-cmd-input" placeholder="Enter shell or python command to execute inside sandbox..." onkeydown="if(event.key==='Enter') executeTerminalCommand()">
                            <button class="btn-action" onclick="executeTerminalCommand()">▶ Run Command</button>
                        </div>
                        <div class="terminal-screen" id="terminal-screen-box">
                            <div class="term-line" style="color:var(--accent-green); font-weight:700;">[CortexOS Sandboxed Kernel Terminal // Ready]</div>
                            <div class="term-line" style="color:var(--text-dim);">All commands execute inside isolated sandbox with automated Git shadow checkpointing (refs/checkpoints/).</div>
                            <div class="term-line" style="color:var(--accent-cyan);">Try running presets above or type any command (e.g., 'git status', 'python --version', 'dir').</div>
                        </div>
                    </div>
                </div>

                <!-- 3. Active Daemons & Background Workers Grid -->
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:6px;">
                    <h3 style="font-size:0.95rem; font-family:var(--font-mono); color:var(--text-main); display:flex; align-items:center; gap:8px;">
                        <span>🤖</span> Active Background Daemons & Runtimes
                    </h3>
                    <span style="font-size:0.75rem; color:var(--text-dim); font-family:var(--font-mono);">4 Autonomous Supervisors</span>
                </div>
                <div class="daemons-grid" id="daemons-grid">
                    <!-- 1. Uvicorn -->
                    <div class="daemon-card tilt-card">
                        <div class="daemon-head"><span class="daemon-name">🌐 Web & WS Daemon</span><span class="daemon-badge daemon-running">RUNNING</span></div>
                        <div class="daemon-metric">PID: <span class="val">32364 (Port 8000)</span></div>
                        <div class="daemon-metric">CPU: <span class="val">0.0%</span></div>
                        <div class="daemon-metric">Memory RSS: <span class="val">89.46 MB</span></div>
                        <div class="daemon-metric">Threads: <span class="val">22</span></div>
                        <div class="daemon-metric">Status: <span class="val">High Availability Gateway</span></div>
                    </div>
                    <!-- 2. Ambient Tick -->
                    <div class="daemon-card tilt-card">
                        <div class="daemon-head"><span class="daemon-name">⏱️ Ambient Tick Worker</span><span class="daemon-badge daemon-running">ACTIVE</span></div>
                        <div class="daemon-metric">Frequency: <span class="val">Every 15s</span></div>
                        <div class="daemon-metric">Last Tick: <span class="val">#0</span></div>
                        <div class="daemon-metric">Mode: <span class="val">On-Demand Reactive</span></div>
                        <div class="daemon-metric">Duplex: <span class="val">1 Active WebSocket</span></div>
                        <div class="daemon-metric">Status: <span class="val">GWA Cognitive Tick Loop</span></div>
                    </div>
                    <!-- 3. StallBreaker -->
                    <div class="daemon-card tilt-card">
                        <div class="daemon-head"><span class="daemon-name">🛡️ StallBreaker Sentinel</span><span class="daemon-badge daemon-nominal">NOMINAL</span></div>
                        <div class="daemon-metric">Panic Switch: <span class="val">DISARMED</span></div>
                        <div class="daemon-metric">Stall Timeout: <span class="val">45.0s Hardware Gate</span></div>
                        <div class="daemon-metric">Status: <span class="val">Nominal Subsystem Bus</span></div>
                        <div class="daemon-metric">Circuit Breaker: <span class="val">Armed</span></div>
                    </div>
                    <!-- 4. Digital Sleep -->
                    <div class="daemon-card tilt-card">
                        <div class="daemon-head"><span class="daemon-name">💤 Sleep Daemon</span><span class="daemon-badge daemon-nominal">STANDBY</span></div>
                        <div class="daemon-metric">Engrams Stored: <span class="val">22 Atomic Engrams</span></div>
                        <div class="daemon-metric">Stage 1-4: <span class="val">WAL / Bigram / LoRA</span></div>
                        <div class="daemon-metric">Scheduler: <span class="val">AC Power & Idle State</span></div>
                        <div class="daemon-metric">Status: <span class="val">Memory Consolidation</span></div>
                    </div>
                </div>

                <!-- 4. Underlying Child Processes & Desktop Applications -->
                <div class="exec-card tilt-card" style="margin-bottom:40px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; flex-wrap:wrap; gap:10px;">
                        <h3 style="font-size:0.95rem; font-family:var(--font-mono); color:var(--text-main); display:flex; align-items:center; gap:8px;">
                            <span>🌳</span> Underlying Process Topology & Child Subprocesses
                        </h3>
                        <div style="display:flex; gap:10px; align-items:center; flex-wrap:wrap;">
                            <input type="text" class="proc-search-input" id="proc-search-input" placeholder="Filter processes..." oninput="filterProcessTable(this.value)">
                            <div class="filter-tags">
                                <span class="filter-tag active" id="ptag-cortex" onclick="toggleProcessTab('cortex', this)">CORTEX CHILDREN</span>
                                <span class="filter-tag" id="ptag-desktop" onclick="toggleProcessTab('desktop', this)">DESKTOP APPS</span>
                                <span class="filter-tag" id="ptag-system" onclick="toggleProcessTab('system', this)">TOP SYSTEM PROCS</span>
                            </div>
                            <button class="btn-subtle" onclick="loadProcessesTelemetry()"><span>🔄</span> Refresh</button>
                        </div>
                    </div>
                    <div class="data-table-wrap" style="max-height:360px;">
                        <table class="cortex-table">
                            <thead>
                                <tr>
                                    <th>PID</th>
                                    <th>Process Name</th>
                                    <th>CPU %</th>
                                    <th>Memory (MB / %)</th>
                                    <th>Status</th>
                                    <th>Details / Cmdline</th>
                                </tr>
                            </thead>
                            <tbody id="processes-table-body">
                                <tr><td colspan="6" style="text-align:center; color:var(--text-dim); padding:20px;">Loading process telemetry...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

        </div>
    </main>

    <script>
        // ==================== 1. RESILIENT WEBSOCKET ROUTING ====================
        let socket = null;
        let activeTab = 'stage';
        let isReconnecting = false;
        let reconnectAttempts = 0;

        function toggleSidebar() {
            const mainEl = document.querySelector('main');
            const isCollapsed = mainEl.classList.toggle('sidebar-collapsed');
            const toggleBtn = document.getElementById('btn-side-toggle');
            if (toggleBtn) toggleBtn.classList.toggle('active', isCollapsed);
            setTimeout(onWindowResize, 260);
        }

        function connectWebSocket() {
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${wsProtocol}//${window.location.host}/ws`;
            
            try {
                socket = new WebSocket(wsUrl);
            } catch (err) {
                scheduleReconnect();
                return;
            }

            socket.onopen = () => {
                console.log('Connected to CortexOS WebSocket');
                reconnectAttempts = 0;
                isReconnecting = false;
                setConnectionStatus('SYNCED', 'online');
            };

            socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'state_update') {
                        updateTelemetry(data.state);
                    } else if (data.type === 'cortex_response') {
                        removeThinkingIndicator();
                        renderCortexResponse(data);
                        updateTelemetry(data.state);
                        trigger3DCognitivePulse(data.state ? data.state.entropy : 1.0);
                    } else if (data.type === 'hold_card') {
                        removeThinkingIndicator();
                        renderHoldCard(data);
                    } else if (data.type === 'ambient_tick') {
                        renderAmbientNotice(data);
                        updateTelemetry(data.state);
                        trigger3DCognitivePulse(data.state ? data.state.entropy : 1.0);
                    }
                } catch (e) {
                    console.error('WebSocket parse error:', e);
                }
            };

            socket.onclose = () => {
                scheduleReconnect();
            };

            socket.onerror = (err) => {
                console.warn('WebSocket error:', err);
                socket.close();
            };
        }

        function scheduleReconnect() {
            if (isReconnecting) return;
            isReconnecting = true;
            reconnectAttempts++;
            setConnectionStatus('RECONNECTING...', 'reconnecting');
            const delay = Math.min(1000 * Math.pow(1.5, reconnectAttempts), 6000);
            setTimeout(() => {
                isReconnecting = false;
                connectWebSocket();
            }, delay);
        }

        function setConnectionStatus(text, statusClass) {
            const pill = document.getElementById('conn-pill');
            const lbl = document.getElementById('conn-text');
            if (!pill || !lbl) return;
            pill.className = `conn-pill ${statusClass}`;
            lbl.innerText = text;
        }

        function updateTelemetry(st) {
            if (!st) return;
            document.getElementById('tick-id').innerText = '#' + (st.tick_id || 0);
            document.getElementById('entropy-val').innerText = (st.entropy || 1.0).toFixed(2);
            document.getElementById('temp-val').innerText = (st.temperature || 0.4).toFixed(2);
            if (st.blocks) {
                if (st.blocks.persona_self) document.getElementById('block-persona').innerText = st.blocks.persona_self.value.substring(0, 150) + '...';
                if (st.blocks.workspace_state) document.getElementById('block-workspace').innerText = st.blocks.workspace_state.value.substring(0, 150) + '...';
                if (st.blocks.scratchpad_stm) document.getElementById('block-scratchpad').innerText = st.blocks.scratchpad_stm.value.substring(0, 150) + '...';
            }
            if (window.updateMemoryPrismsFromState) {
                window.updateMemoryPrismsFromState(st.blocks);
            }
        }

        // Tab Switching Router
        function switchTab(tabName) {
            activeTab = tabName;
            const tabs = ['stage', 'memory', 'graph', 'skills', 'governance', 'execution'];
            tabs.forEach(t => {
                const btn = document.getElementById(`tab-${t}`);
                const pane = document.getElementById(`pane-${t}`);
                if (btn) btn.classList.toggle('active', t === tabName);
                if (pane) pane.classList.toggle('active', t === tabName);
            });

            if (tabName === 'stage') {
                requestAnimationFrame(onStageResize);
            } else if (tabName === 'memory') {
                loadMemoryPane();
                requestAnimationFrame(onMemoryResize);
            } else if (tabName === 'graph') {
                loadGraphPane();
                requestAnimationFrame(onGraphResize);
            } else if (tabName === 'skills') {
                loadSkillsPane();
            } else if (tabName === 'governance') {
                loadGovernancePane();
            } else if (tabName === 'execution') {
                loadExecutionPane();
            }
        }

        // ==================== 2. MASTER THREE.JS ENGINE ====================
        let bgScene, bgCamera, bgRenderer, bgParticles, bgCoreMesh, bgRingMesh, bgGrid;
        let mouseX = 0, mouseY = 0, targetRotX = 0, targetRotY = 0;

        function initBackground3D() {
            const canvas = document.getElementById('webgl-bg-canvas');
            bgScene = new THREE.Scene();
            bgScene.fog = new THREE.FogExp2(0x060911, 0.002);

            bgCamera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 1, 2000);
            bgCamera.position.z = 450;
            bgCamera.position.y = 80;

            bgRenderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true, powerPreference: 'high-performance' });
            bgRenderer.setSize(window.innerWidth, window.innerHeight);
            bgRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));

            bgGrid = new THREE.GridHelper(1600, 40, 0x00e5ff, 0x1e293b);
            bgGrid.position.y = -180;
            bgGrid.material.opacity = 0.22;
            bgGrid.material.transparent = true;
            bgScene.add(bgGrid);

            const particleCount = 550;
            const geom = new THREE.BufferGeometry();
            const positions = new Float32Array(particleCount * 3);
            for (let i = 0; i < particleCount * 3; i += 3) {
                positions[i] = (Math.random() - 0.5) * 1400;
                positions[i + 1] = (Math.random() - 0.5) * 800;
                positions[i + 2] = (Math.random() - 0.5) * 900;
            }
            geom.setAttribute('position', new THREE.BufferAttribute(positions, 3));
            const pMat = new THREE.PointsMaterial({
                color: 0x00e5ff,
                size: 3.0,
                transparent: true,
                opacity: 0.65,
                blending: THREE.AdditiveBlending
            });
            bgParticles = new THREE.Points(geom, pMat);
            bgScene.add(bgParticles);

            const coreGroup = new THREE.Group();
            coreGroup.position.set(280, 100, -100);

            const icoGeom = new THREE.IcosahedronGeometry(70, 1);
            const icoMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8, wireframe: true, transparent: true, opacity: 0.35 });
            bgCoreMesh = new THREE.Mesh(icoGeom, icoMat);
            coreGroup.add(bgCoreMesh);

            const innerGeom = new THREE.SphereGeometry(38, 20, 20);
            const innerMat = new THREE.MeshBasicMaterial({ color: 0x00e5ff, wireframe: true, transparent: true, opacity: 0.55 });
            const innerCore = new THREE.Mesh(innerGeom, innerMat);
            coreGroup.add(innerCore);

            const ringGeom = new THREE.RingGeometry(85, 95, 32);
            const ringMat = new THREE.MeshBasicMaterial({ color: 0xc084fc, side: THREE.DoubleSide, transparent: true, opacity: 0.35, wireframe: true });
            bgRingMesh = new THREE.Mesh(ringGeom, ringMat);
            bgRingMesh.rotation.x = Math.PI / 2.5;
            coreGroup.add(bgRingMesh);

            bgScene.add(coreGroup);

            window.addEventListener('resize', onWindowResize);
            document.addEventListener('mousemove', onMouseMove);
        }

        function onMouseMove(event) {
            mouseX = (event.clientX - window.innerWidth / 2) * 0.08;
            mouseY = (event.clientY - window.innerHeight / 2) * 0.08;
        }

        function onWindowResize() {
            if (bgCamera && bgRenderer) {
                bgCamera.aspect = window.innerWidth / window.innerHeight;
                bgCamera.updateProjectionMatrix();
                bgRenderer.setSize(window.innerWidth, window.innerHeight);
            }
            if (activeTab === 'stage') onStageResize();
            else if (activeTab === 'graph') onGraphResize();
            else if (activeTab === 'memory') onMemoryResize();
        }

        function trigger3DCognitivePulse(entropy) {
            if (!bgCoreMesh) return;
            new TWEEN.Tween(bgCoreMesh.scale)
                .to({ x: 1.35, y: 1.35, z: 1.35 }, 140)
                .yoyo(true)
                .repeat(1)
                .easing(TWEEN.Easing.Quadratic.Out)
                .start();

            if (entropy > 1.2 && bgCoreMesh.material) {
                bgCoreMesh.material.color.setHex(0xc084fc);
                setTimeout(() => { if (bgCoreMesh) bgCoreMesh.material.color.setHex(0x38bdf8); }, 800);
            }
        }

        // ==================== 3. COGNITIVE STAGE SATELLITES ====================
        let stageScene, stageCamera, stageRenderer;
        let satGroup, satAnalytic, satPragmatic, satCautious;
        let satAngle = 0;

        function initStage3D() {
            const canvas = document.getElementById('stage-3d-canvas');
            if (!canvas) return;
            const rect = canvas.getBoundingClientRect();
            const w = rect.width || 340;
            const h = rect.height || 150;

            stageScene = new THREE.Scene();
            stageCamera = new THREE.PerspectiveCamera(50, w / h, 0.1, 1000);
            stageCamera.position.set(0, 20, 110);
            stageCamera.lookAt(0, 0, 0);

            stageRenderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
            stageRenderer.setSize(w, h);
            stageRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));

            const coreGeom = new THREE.SphereGeometry(12, 18, 18);
            const coreMat = new THREE.MeshBasicMaterial({ color: 0x00e5ff, wireframe: true });
            const core = new THREE.Mesh(coreGeom, coreMat);
            stageScene.add(core);

            satGroup = new THREE.Group();
            stageScene.add(satGroup);

            const sGeom = new THREE.SphereGeometry(5, 14, 14);
            satAnalytic = new THREE.Mesh(sGeom, new THREE.MeshBasicMaterial({ color: 0x38bdf8 }));
            satPragmatic = new THREE.Mesh(sGeom, new THREE.MeshBasicMaterial({ color: 0x10b981 }));
            satCautious = new THREE.Mesh(sGeom, new THREE.MeshBasicMaterial({ color: 0xf59e0b }));

            satGroup.add(satAnalytic);
            satGroup.add(satPragmatic);
            satGroup.add(satCautious);
        }

        function onStageResize() {
            const canvas = document.getElementById('stage-3d-canvas');
            if (!canvas || !stageCamera || !stageRenderer) return;
            const w = canvas.clientWidth;
            const h = canvas.clientHeight;
            if (w === 0 || h === 0) return;
            stageCamera.aspect = w / h;
            stageCamera.updateProjectionMatrix();
            stageRenderer.setSize(w, h);
        }

        // ==================== 4. 3D BI-TEMPORAL MULTI-GRAPH UNIVERSE ====================
        let graphScene, graphCamera, graphRenderer, graphControls;
        let graphNodesGroup, graphEdgesGroup, graphRaycaster, graphMouse;
        let graphNodeMeshes = [];
        let currentGraphEdges = [];
        let isGraphInitialized = false;

        function ensureGraph3DInit() {
            if (isGraphInitialized) return;
            const container = document.getElementById('graph-3d-viewport');
            if (!container || container.clientWidth === 0) return;

            graphScene = new THREE.Scene();
            graphCamera = new THREE.PerspectiveCamera(50, container.clientWidth / container.clientHeight, 1, 3000);
            graphCamera.position.set(0, 120, 360);

            graphRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
            graphRenderer.setSize(container.clientWidth, container.clientHeight);
            graphRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));
            container.appendChild(graphRenderer.domElement);

            graphControls = new THREE.OrbitControls(graphCamera, graphRenderer.domElement);
            graphControls.enableDamping = true;
            graphControls.dampingFactor = 0.06;
            graphControls.autoRotate = true;
            graphControls.autoRotateSpeed = 0.6;
            graphControls.maxDistance = 800;
            graphControls.minDistance = 60;

            const ambLight = new THREE.AmbientLight(0xffffff, 0.9);
            graphScene.add(ambLight);

            graphNodesGroup = new THREE.Group();
            graphEdgesGroup = new THREE.Group();
            graphScene.add(graphNodesGroup);
            graphScene.add(graphEdgesGroup);

            graphRaycaster = new THREE.Raycaster();
            graphMouse = new THREE.Vector2();

            graphRenderer.domElement.addEventListener('mousemove', onGraphMouseMove);
            graphRenderer.domElement.addEventListener('click', onGraphClick);

            isGraphInitialized = true;
            if (currentGraphEdges.length > 0) {
                render3DGraph(currentGraphEdges);
            }
        }

        function onGraphResize() {
            ensureGraph3DInit();
            const container = document.getElementById('graph-3d-viewport');
            if (!container || !graphCamera || !graphRenderer) return;
            const w = container.clientWidth;
            const h = container.clientHeight;
            if (w === 0 || h === 0) return;
            graphCamera.aspect = w / h;
            graphCamera.updateProjectionMatrix();
            graphRenderer.setSize(w, h);
        }

        function toggleGraphMaximize() {
            const container = document.getElementById('graph-3d-container');
            const btn = document.getElementById('btn-graph-maximize');
            if (!container) return;
            container.classList.toggle('maximized');
            btn.innerText = container.classList.contains('maximized') ? '🗗 Minimize' : '⛶ Expand';
            setTimeout(onGraphResize, 100);
        }

        function reset3DGraphCamera() {
            if (!graphCamera || !graphControls) return;
            new TWEEN.Tween(graphCamera.position)
                .to({ x: 0, y: 120, z: 360 }, 700)
                .easing(TWEEN.Easing.Cubic.Out)
                .start();
            graphControls.target.set(0, 0, 0);
        }

        function searchGraphNode(query) {
            query = (query || '').trim().toLowerCase();
            if (!query) return;
            const match = graphNodeMeshes.find(m => m.userData.id.toLowerCase().includes(query));
            if (match && graphControls && graphCamera) {
                const pos = match.position;
                new TWEEN.Tween(graphCamera.position)
                    .to({ x: pos.x + 35, y: pos.y + 25, z: pos.z + 80 }, 600)
                    .easing(TWEEN.Easing.Cubic.Out)
                    .start();
                graphControls.target.copy(pos);
            }
        }

        function onGraphMouseMove(event) {
            if (!graphRenderer || !graphCamera) return;
            const rect = graphRenderer.domElement.getBoundingClientRect();
            graphMouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
            graphMouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

            graphRaycaster.setFromCamera(graphMouse, graphCamera);
            const intersects = graphRaycaster.intersectObjects(graphNodeMeshes);
            const hud = document.getElementById('graph-node-details');

            if (intersects.length > 0) {
                const nodeData = intersects[0].object.userData;
                hud.style.display = 'block';
                const lyr = (nodeData.layer || 'semantic').toLowerCase();
                hud.innerHTML = `
                    <div style="font-weight:700; color:var(--accent-cyan); font-size:0.86rem; margin-bottom:2px;">Node: ${escapeHtml(nodeData.id)}</div>
                    <div><b>Layer:</b> <span class="layer-badge layer-${lyr}">${nodeData.layer}</span></div>
                    <div style="margin-top:4px; font-size:0.74rem; color:var(--text-dim);">Click node to focus & inspect links.</div>
                `;
            } else {
                hud.style.display = 'none';
            }
        }

        function onGraphClick(event) {
            if (!graphRenderer || !graphCamera) return;
            const rect = graphRenderer.domElement.getBoundingClientRect();
            graphMouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
            graphMouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

            graphRaycaster.setFromCamera(graphMouse, graphCamera);
            const intersects = graphRaycaster.intersectObjects(graphNodeMeshes);
            if (intersects.length > 0) {
                const targetMesh = intersects[0].object;
                const pos = targetMesh.position;
                new TWEEN.Tween(graphCamera.position)
                    .to({ x: pos.x + 30, y: pos.y + 25, z: pos.z + 70 }, 600)
                    .easing(TWEEN.Easing.Cubic.Out)
                    .start();
                graphControls.target.copy(pos);
            }
        }

        function makeTextSprite(message, colorHex) {
            const canvas = document.createElement('canvas');
            canvas.width = 256;
            canvas.height = 64;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = 'rgba(10, 15, 29, 0.75)';
            ctx.roundRect ? ctx.roundRect(0, 0, 256, 64, 8) : ctx.fillRect(0, 0, 256, 64);
            ctx.fill();
            ctx.strokeStyle = colorHex || '#00e5ff';
            ctx.lineWidth = 3;
            ctx.stroke();

            ctx.font = 'bold 22px "JetBrains Mono", monospace';
            ctx.fillStyle = '#ffffff';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            const displayMsg = message.length > 14 ? message.substring(0, 12) + '..' : message;
            ctx.fillText(displayMsg, 128, 32);

            const texture = new THREE.CanvasTexture(canvas);
            const spriteMaterial = new THREE.SpriteMaterial({ map: texture, transparent: true });
            const sprite = new THREE.Sprite(spriteMaterial);
            sprite.scale.set(30, 8, 1);
            return sprite;
        }

        function render3DGraph(edges) {
            drawGraphCanvas(edges);
            if (!isGraphInitialized) ensureGraph3DInit();
            if (!graphScene) return;

            while (graphNodesGroup.children.length > 0) graphNodesGroup.remove(graphNodesGroup.children[0]);
            while (graphEdgesGroup.children.length > 0) graphEdgesGroup.remove(graphEdgesGroup.children[0]);
            graphNodeMeshes = [];

            if (!edges || edges.length === 0) return;

            const nodeMap = new Map();
            edges.forEach(e => {
                if (!nodeMap.has(e.source_id)) nodeMap.set(e.source_id, { id: e.source_id, layer: e.layer });
                if (!nodeMap.has(e.target_id)) nodeMap.set(e.target_id, { id: e.target_id, layer: e.layer });
            });

            const nodes = Array.from(nodeMap.values());
            const radius = 130;
            const count = nodes.length;

            nodes.forEach((n, idx) => {
                const phi = Math.acos(-1 + (2 * idx) / count);
                const theta = Math.sqrt(count * Math.PI) * phi;
                n.x = radius * Math.cos(theta) * Math.sin(phi);
                n.y = radius * Math.sin(theta) * Math.sin(phi);
                n.z = radius * Math.cos(phi);

                let colHex = 0x00e5ff;
                let cssCol = '#00e5ff';
                const lyr = (n.layer || 'semantic').toLowerCase();
                if (lyr === 'causal') { colHex = 0xf59e0b; cssCol = '#f59e0b'; }
                else if (lyr === 'temporal') { colHex = 0xc084fc; cssCol = '#c084fc'; }
                else if (lyr === 'entity') { colHex = 0x10b981; cssCol = '#10b981'; }

                const sGeom = new THREE.SphereGeometry(6.5, 20, 20);
                const sMat = new THREE.MeshBasicMaterial({ color: colHex });
                const mesh = new THREE.Mesh(sGeom, sMat);
                mesh.position.set(n.x, n.y, n.z);
                mesh.userData = n;
                graphNodesGroup.add(mesh);
                graphNodeMeshes.push(mesh);

                const haloGeom = new THREE.RingGeometry(8, 9.5, 20);
                const haloMat = new THREE.MeshBasicMaterial({ color: colHex, side: THREE.DoubleSide, transparent: true, opacity: 0.6 });
                const halo = new THREE.Mesh(haloGeom, haloMat);
                halo.position.set(n.x, n.y, n.z);
                graphNodesGroup.add(halo);

                const sprite = makeTextSprite(n.id, cssCol);
                sprite.position.set(n.x, n.y + 14, n.z);
                graphNodesGroup.add(sprite);
            });

            const posLookup = new Map(nodes.map(n => [n.id, n]));

            edges.forEach(e => {
                const src = posLookup.get(e.source_id);
                const tgt = posLookup.get(e.target_id);
                if (!src || !tgt) return;

                const points = [
                    new THREE.Vector3(src.x, src.y, src.z),
                    new THREE.Vector3(tgt.x, tgt.y, tgt.z)
                ];
                const lineGeom = new THREE.BufferGeometry().setFromPoints(points);
                let colHex = 0x00e5ff;
                const lyr = (e.layer || 'semantic').toLowerCase();
                if (lyr === 'causal') colHex = 0xf59e0b;
                else if (lyr === 'temporal') colHex = 0xc084fc;

                const lineMat = new THREE.LineBasicMaterial({ color: colHex, transparent: true, opacity: 0.5, linewidth: 2 });
                const line = new THREE.Line(lineGeom, lineMat);
                graphEdgesGroup.add(line);
            });
        }

        // ==================== 5. WORKING MEMORY PRISMS ====================
        let memScene, memCamera, memRenderer;
        let memPrisms = [];
        let isMemInitialized = false;

        function ensureMemory3DInit() {
            if (isMemInitialized) return;
            const canvas = document.getElementById('memory-3d-canvas');
            if (!canvas || canvas.clientWidth === 0) return;

            const w = canvas.clientWidth || 600;
            const h = canvas.clientHeight || 130;

            memScene = new THREE.Scene();
            memCamera = new THREE.PerspectiveCamera(45, w / h, 1, 1000);
            memCamera.position.set(0, 35, 120);
            memCamera.lookAt(0, 0, 0);

            memRenderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
            memRenderer.setSize(w, h);
            memRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5));

            const grid = new THREE.GridHelper(300, 20, 0x00e5ff, 0x1e293b);
            grid.position.y = -15;
            memScene.add(grid);

            const blockNames = ['persona_self', 'human_profile', 'workspace_state', 'scratchpad_stm'];
            const colors = [0x00e5ff, 0x38bdf8, 0xc084fc, 0x10b981];
            memPrisms = [];

            blockNames.forEach((name, i) => {
                const geom = new THREE.CylinderGeometry(8, 8, 26, 6);
                const mat = new THREE.MeshBasicMaterial({ color: colors[i], wireframe: true, transparent: true, opacity: 0.85 });
                const prism = new THREE.Mesh(geom, mat);
                prism.position.set(-105 + i * 70, 0, 0);
                prism.userData = { name: name, baseHeight: 26 };
                memScene.add(prism);
                memPrisms.push(prism);
            });

            isMemInitialized = true;
        }

        function onMemoryResize() {
            ensureMemory3DInit();
            const canvas = document.getElementById('memory-3d-canvas');
            if (!canvas || !memCamera || !memRenderer) return;
            const w = canvas.clientWidth;
            const h = canvas.clientHeight;
            if (w === 0 || h === 0) return;
            memCamera.aspect = w / h;
            memCamera.updateProjectionMatrix();
            memRenderer.setSize(w, h);
        }

        window.updateMemoryPrismsFromState = function(blocks) {
            if (!blocks || memPrisms.length === 0) return;
            memPrisms.forEach(p => {
                const b = blocks[p.userData.name];
                if (b && b.value) {
                    const ratio = Math.min(2.5, Math.max(0.4, b.value.length / 500));
                    p.scale.y = ratio;
                }
            });
        };

        // ==================== UNIFIED HIGH-FRAMERATE ANIMATION LOOP ====================
        function masterRenderLoop() {
            requestAnimationFrame(masterRenderLoop);
            TWEEN.update();

            if (bgParticles) {
                bgParticles.rotation.y += 0.0006;
                bgParticles.rotation.x += 0.0003;
            }
            if (bgCoreMesh) {
                bgCoreMesh.rotation.x += 0.008;
                bgCoreMesh.rotation.y += 0.012;
            }
            if (bgRingMesh) {
                bgRingMesh.rotation.z += 0.015;
            }

            targetRotX += (mouseX - targetRotX) * 0.04;
            targetRotY += (mouseY - targetRotY) * 0.04;
            if (bgCamera) {
                bgCamera.position.x = targetRotX * 0.5;
                bgCamera.position.y = 80 - targetRotY * 0.3;
                bgCamera.lookAt(0, 0, 0);
            }
            if (bgRenderer && bgScene && bgCamera) {
                bgRenderer.render(bgScene, bgCamera);
            }

            if (activeTab === 'stage') {
                satAngle += 0.025;
                const radius = 42;
                if (satAnalytic) satAnalytic.position.set(radius * Math.cos(satAngle), 8 * Math.sin(satAngle * 2), radius * Math.sin(satAngle));
                if (satPragmatic) satPragmatic.position.set(radius * Math.cos(satAngle + 2.09), 8 * Math.sin((satAngle + 2.09) * 2), radius * Math.sin(satAngle + 2.09));
                if (satCautious) satCautious.position.set(radius * Math.cos(satAngle + 4.18), 8 * Math.sin((satAngle + 4.18) * 2), radius * Math.sin(satAngle + 4.18));
                if (satGroup) satGroup.rotation.y += 0.005;
                if (stageRenderer && stageScene && stageCamera) {
                    stageRenderer.render(stageScene, stageCamera);
                }
            } else if (activeTab === 'graph') {
                if (graphControls) graphControls.update();
                if (graphRenderer && graphScene && graphCamera) {
                    graphRenderer.render(graphScene, graphCamera);
                }
            } else if (activeTab === 'memory') {
                memPrisms.forEach((p, idx) => {
                    p.rotation.y += 0.015;
                    p.position.y = Math.sin(Date.now() * 0.003 + idx) * 3;
                });
                if (memRenderer && memScene && memCamera) {
                    memRenderer.render(memScene, memCamera);
                }
            }
        }

        // ==================== 6. EVENT-DELEGATED 3D CARD TILT ====================
        function initDelegatedTiltPhysics() {
            document.addEventListener('pointermove', (e) => {
                const card = e.target.closest('.tilt-card');
                if (!card) return;
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                const centerX = rect.width / 2;
                const centerY = rect.height / 2;
                const rotX = ((y - centerY) / centerY) * -8;
                const rotY = ((x - centerX) / centerX) * 8;
                card.style.setProperty('--mouse-x', `${(x / rect.width * 100).toFixed(1)}%`);
                card.style.setProperty('--mouse-y', `${(y / rect.height * 100).toFixed(1)}%`);
                card.style.transform = `perspective(1000px) rotateX(${rotX.toFixed(2)}deg) rotateY(${rotY.toFixed(2)}deg) scale3d(1.01, 1.01, 1.01)`;
            });

            document.addEventListener('pointerout', (e) => {
                const card = e.target.closest('.tilt-card');
                if (!card || card.contains(e.relatedTarget)) return;
                card.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)`;
            });
        }

        // ==================== 7. CHAT, THINKING INDICATOR & MARKDOWN ====================
        let thinkingStepsInterval = null;

        function sendMessage() {
            const input = document.getElementById('chat-input');
            const text = input.value.trim();
            if (!text) return;
            
            appendMessage(text, 'msg-user');
            input.value = '';

            showThinkingIndicator();

            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({ type: 'user_message', content: text }));
            } else {
                removeThinkingIndicator();
                appendMessage('WebSocket not connected. Reconnecting in background...', 'msg-cortex');
                connectWebSocket();
            }
        }

        function quickPrompt(text) {
            const input = document.getElementById('chat-input');
            if (input) {
                input.value = text;
                sendMessage();
            }
        }

        function showThinkingIndicator() {
            removeThinkingIndicator();
            const container = document.getElementById('chat-messages');
            const bubble = document.createElement('div');
            bubble.id = 'cortex-thinking-indicator';
            bubble.className = 'thinking-bubble';
            bubble.innerHTML = `
                <div class="thinking-spinner">
                    <div class="spinner-ring"></div>
                    <div class="spinner-core"></div>
                </div>
                <div class="thinking-text">
                    <div class="thinking-title">CORTEX COGNITIVE ARBITRATION</div>
                    <div class="thinking-step" id="thinking-step-lbl">Evaluating specialist perspectives (Analytic, Pragmatic, Cautious)...</div>
                </div>
            `;
            container.appendChild(bubble);
            container.scrollTop = container.scrollHeight;

            const steps = [
                'Evaluating specialist perspectives (Analytic, Pragmatic, Cautious)...',
                'Consulting somatosensory bus & hardware telemetry...',
                'Evaluating Cedar PDP sub-millisecond policy gate...',
                'Running GWA convergent Critic arbitration...',
                'Synthesizing final response...'
            ];
            let stepIdx = 0;
            thinkingStepsInterval = setInterval(() => {
                stepIdx = (stepIdx + 1) % steps.length;
                const lbl = document.getElementById('thinking-step-lbl');
                if (lbl) lbl.innerText = steps[stepIdx];
            }, 800);
        }

        function removeThinkingIndicator() {
            if (thinkingStepsInterval) {
                clearInterval(thinkingStepsInterval);
                thinkingStepsInterval = null;
            }
            const ind = document.getElementById('cortex-thinking-indicator');
            if (ind) ind.remove();
        }

        function appendMessage(text, className) {
            const container = document.getElementById('chat-messages');
            const div = document.createElement('div');
            div.className = `message-bubble ${className}`;
            div.innerText = text;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
            return div;
        }

        function formatMarkdown(text) {
            if (!text) return '';
            let out = escapeHtml(text);

            out = out.replace(/```([a-zA-Z0-9_\-]+)?\n([\s\S]*?)```/g, (match, lang, code) => {
                const langName = lang || 'shell';
                const id = 'code-' + Math.random().toString(36).substring(2, 9);
                return `
                    <div class="code-block-wrap">
                        <div class="code-block-head">
                            <span>${langName}</span>
                            <button class="btn-copy" onclick="copyCode('${id}', this)">📋 Copy</button>
                        </div>
                        <div class="code-block-body" id="${id}">${code}</div>
                    </div>
                `;
            });

            out = out.replace(/`([^`]+)`/g, '<code style="background:rgba(255,255,255,0.08); padding:2px 6px; border-radius:4px; color:#38bdf8; font-family:var(--font-mono); font-size:0.86rem;">$1</code>');
            out = out.replace(/\*\*([^*]+)\*\*/g, '<b style="color:#fff;">$1</b>');
            out = out.replace(/^(\s*)-\s+(.*)$/gm, '<div style="margin-left:14px;">• $2</div>');
            out = out.replace(/\n/g, '<br>');

            return out;
        }

        function copyCode(id, btn) {
            const el = document.getElementById(id);
            if (!el) return;
            navigator.clipboard.writeText(el.innerText).then(() => {
                btn.innerText = '✓ Copied!';
                btn.style.color = '#10b981';
                setTimeout(() => { btn.innerText = '📋 Copy'; btn.style.color = 'var(--accent-cyan)'; }, 2000);
            });
        }

        function renderCortexResponse(data) {
            const container = document.getElementById('chat-messages');
            const div = document.createElement('div');
            div.className = 'message-bubble msg-cortex';
            div.innerHTML = `<div>${formatMarkdown(data.response)}</div>
            <div style="display:flex; align-items:center; gap:8px; margin-top:8px;">
                <button class="btn-voice-bubble" onclick="playVoiceAudio(this)" data-text="${encodeURIComponent(data.response)}" data-persona="${data.persona || ''}">
                    <span>🔊</span> Speak
                </button>
            </div>`;
            
            if (data.candidates && data.candidates.length > 0) {
                const thoughtDetails = document.createElement('details');
                thoughtDetails.className = 'thought-card';
                thoughtDetails.innerHTML = `<summary>[Inner Monologue / 3 Perspectives]</summary>` +
                    data.candidates.map(c => {
                        const perspLower = (c.perspective || '').toLowerCase();
                        let badgeClass = 'persp-analytic';
                        if (perspLower.includes('pragmatic')) badgeClass = 'persp-pragmatic';
                        else if (perspLower.includes('cautious')) badgeClass = 'persp-cautious';
                        return `<div style="margin-top:5px; display:flex; align-items:flex-start; justify-content:space-between; gap:6px;">
                            <div>
                                <span class="persp-badge ${badgeClass}">${escapeHtml(c.perspective)}</span>
                                <span>${escapeHtml(c.thought_text)}</span>
                                <b style="color:var(--accent-cyan);">(${c.score > 0 ? '+' : ''}${c.score})</b>
                            </div>
                            <button class="btn-persp-voice" onclick="playPerspectiveVoice('${escapeHtml(c.perspective)}', '${escapeHtml(c.thought_text)}', event)" title="Hear ${escapeHtml(c.perspective)} agent voice">🗣️</button>
                        </div>`;
                    }).join('');
                div.appendChild(thoughtDetails);
            }
            if (data.action_result && data.action_result.stdout && (data.action_result.action === 'command_run' || data.action_result.action === 'crystallize_skill')) {
                const outBox = document.createElement('div');
                outBox.style = 'margin-top:10px; font-family:var(--font-mono); font-size:0.8rem; background:rgba(0,0,0,0.6); border:1px solid rgba(16,185,129,0.3); padding:8px 12px; border-radius:6px; color:#10b981; max-height:160px; overflow-y:auto; white-space:pre-wrap;';
                outBox.innerText = '$ ' + data.action_result.stdout;
                div.appendChild(outBox);
            }

            container.appendChild(div);
            container.scrollTop = container.scrollHeight;

            // Auto-speak response if voice speech is active
            if (voiceSpeechEnabled && data.response && data.speak !== false) {
                playVoiceAudioForText(data.response, data.persona);
            }
        }

        function renderHoldCard(data) {
            const container = document.getElementById('chat-messages');
            const div = document.createElement('div');
            div.className = 'hold-card';
            div.innerHTML = `
                <h4>⚠️ Human-in-the-Loop Hold (Governance Circuit Breaker)</h4>
                <p><b>Action:</b> ${JSON.stringify(data.card.action)}</p>
                <p><b>Reason:</b> ${data.card.reason}</p>
                <div class="hold-actions">
                    <button class="btn-approve" onclick="resolveHold(true, this)">Approve & Execute</button>
                    <button class="btn-reject" onclick="resolveHold(false, this)">Reject</button>
                </div>
            `;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        }

        function resolveHold(approved, btn) {
            socket.send(JSON.stringify({ type: 'hold_decision', approved: approved }));
            btn.parentElement.innerHTML = approved ? '<span style="color:#10b981">Approved</span>' : '<span style="color:#ef4444">Rejected</span>';
        }

        function renderAmbientNotice(data) {
            const container = document.getElementById('chat-messages');
            const div = document.createElement('div');
            div.style = 'font-size:0.8rem; color:#94a3b8; font-style:italic; padding:6px 14px; background:rgba(0,229,255,0.06); border-left:3px solid #00e5ff; border-radius:4px; margin-top:8px;';
            div.innerText = `[Ambient Cognitive Notice]: ${data.notice}`;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
        }

        function toggleAmbient() {
            const btn = document.getElementById('btn-ambient');
            const willBeActive = !btn.classList.contains('active');
            btn.classList.toggle('active');
            btn.innerText = willBeActive ? 'AMBIENT: ON (15s)' : 'AMBIENT: OFF';
            socket.send(JSON.stringify({ type: 'toggle_ambient', active: willBeActive }));
        }

        async function triggerSleep() {
            appendMessage('Initiating 4-Stage Asynchronous Digital Sleep...', 'msg-cortex');
            const res = await fetch('/api/sleep', { method: 'POST' });
            const data = await res.json();
            appendMessage(`Digital Sleep Consolidation complete in ${data.report.duration_seconds}s! Extracted engrams: ${data.report.engrams_extracted}, pre-computed files: ${data.report.codebase_files_analyzed}.`, 'msg-cortex');
        }

        function escapeHtml(str) {
            if (!str) return '';
            return String(str)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#039;');
        }

        // ==================== 8. WORKING MEMORY FUNCTIONS ====================
        async function loadMemoryPane() {
            try {
                const res = await fetch('/api/blocks');
                const blocks = await res.json();
                for (const [key, b] of Object.entries(blocks)) {
                    const txt = document.getElementById(`mem-${key}`);
                    const badge = document.getElementById(`badge-${key}`);
                    const bar = document.getElementById(`bar-${key}`);
                    if (txt) txt.value = b.value;
                    if (badge) badge.innerText = `${b.char_count} / ${b.char_limit} chars`;
                    if (bar) bar.style.width = `${Math.min(100, (b.char_count / b.char_limit) * 100)}%`;
                }
                if (window.updateMemoryPrismsFromState) {
                    window.updateMemoryPrismsFromState(blocks);
                }
            } catch (e) {
                console.error('Failed to load blocks:', e);
            }
        }

        async function saveBlock(label) {
            const txt = document.getElementById(`mem-${label}`);
            const status = document.getElementById(`status-${label}`);
            if (!txt) return;

            try {
                const res = await fetch(`/api/blocks/${label}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ value: txt.value })
                });
                const data = await res.json();
                if (data.status === 'SUCCESS') {
                    const badge = document.getElementById(`badge-${label}`);
                    const bar = document.getElementById(`bar-${label}`);
                    if (badge) badge.innerText = `${data.char_count} / ${data.char_limit} chars`;
                    if (bar) bar.style.width = `${Math.min(100, (data.char_count / data.char_limit) * 100)}%`;
                    if (status) {
                        status.style.display = 'inline';
                        setTimeout(() => { status.style.display = 'none'; }, 2500);
                    }
                }
            } catch (e) {
                alert('Failed to update block: ' + e);
            }
        }

        // ==================== 9. BI-TEMPORAL GRAPH FUNCTIONS ====================
        async function loadGraphPane() {
            try {
                const res = await fetch('/api/graph');
                const data = await res.json();
                currentGraphEdges = data.edges || [];
                
                const countAll = document.getElementById('count-all');
                if (countAll) countAll.innerText = currentGraphEdges.length;

                renderGraphEdges(currentGraphEdges);

                const engramsBody = document.getElementById('engrams-body');
                if (data.engrams && data.engrams.length > 0) {
                    engramsBody.innerHTML = data.engrams.map(e => `
                        <tr>
                            <td><span class="layer-badge layer-temporal">${e.semantic_type}</span></td>
                            <td>${escapeHtml(e.statement)}</td>
                        </tr>
                    `).join('');
                } else {
                    engramsBody.innerHTML = `<tr><td colspan="2" style="text-align:center; color:var(--text-dim);">No atomic engrams recorded yet. Run a digital sleep cycle!</td></tr>`;
                }
            } catch (e) {
                console.error('Failed to load graph:', e);
            }
        }

        function renderGraphEdges(edges) {
            render3DGraph(edges);
            const tbody = document.getElementById('graph-edges-body');
            if (!edges || edges.length === 0) {
                tbody.innerHTML = `<tr><td colspan="3" style="text-align:center; color:var(--text-dim);">No graph edges found.</td></tr>`;
                return;
            }
            tbody.innerHTML = edges.map(edge => {
                const layerClass = `layer-${(edge.layer || 'semantic').toLowerCase()}`;
                return `
                    <tr>
                        <td><b>${escapeHtml(edge.source_id)}</b> ➔ <span style="color:var(--accent-cyan); font-weight:600;">[${escapeHtml(edge.relation)}]</span> ➔ <b>${escapeHtml(edge.target_id)}</b></td>
                        <td><span class="layer-badge ${layerClass}">${edge.layer}</span></td>
                        <td style="color:var(--text-dim); font-size:0.75rem;">${escapeHtml(edge.provenance_ref)}</td>
                    </tr>
                `;
            }).join('');
        }

        function drawGraphCanvas(edges) {
            const canvas = document.getElementById('graph-canvas');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
        }

        function filterGraph(layer, btn) {
            document.querySelectorAll('.filter-tag').forEach(t => t.classList.remove('active'));
            btn.classList.add('active');
            if (layer === 'all') {
                renderGraphEdges(currentGraphEdges);
            } else {
                const filtered = currentGraphEdges.filter(e => (e.layer || '').toLowerCase() === layer.toLowerCase());
                renderGraphEdges(filtered);
            }
        }

        async function assertFact() {
            const src = document.getElementById('assert-source').value.trim();
            const rel = document.getElementById('assert-relation').value.trim();
            const tgt = document.getElementById('assert-target').value.trim();
            const lyr = document.getElementById('assert-layer').value;

            if (!src || !rel || !tgt) {
                alert('Please provide Source, Relation, and Target');
                return;
            }

            try {
                const res = await fetch('/api/graph/assert', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ source: src, target: tgt, relation: rel, layer: lyr, provenance: 'user_asserted' })
                });
                const data = await res.json();
                if (data.status === 'SUCCESS') {
                    document.getElementById('assert-source').value = '';
                    document.getElementById('assert-relation').value = '';
                    document.getElementById('assert-target').value = '';
                    loadGraphPane();
                }
            } catch (e) {
                alert('Failed to assert fact: ' + e);
            }
        }

        // ==================== 10. SKILL CRYSTALLIZER FUNCTIONS ====================
        async function loadSkillsPane() {
            try {
                const res = await fetch('/api/skills');
                const data = await res.json();

                if (data.curriculum_challenge) {
                    document.getElementById('curr-level').innerText = (data.curriculum_challenge.level || 'BEGINNER').toUpperCase();
                    document.getElementById('curr-task').innerText = data.curriculum_challenge.task || '';
                }

                const grid = document.getElementById('skills-grid');
                if (!data.skills || data.skills.length === 0) {
                    grid.innerHTML = `<div style="grid-column: span 2; text-align:center; color:var(--text-dim); padding:40px;">No crystallized procedural skills in library yet. Use the synthesizer above!</div>`;
                    return;
                }

                grid.innerHTML = data.skills.map((s, idx) => `
                    <div class="skill-card tilt-card">
                        <div class="skill-head">
                            <span class="skill-name">⚡ ${s.name}</span>
                            <span class="skill-score">Score: ${s.reusability_score}/10</span>
                        </div>
                        <div class="skill-doc">${escapeHtml(s.docstring)}</div>
                        <div class="skill-accordions">
                            <details class="skill-details">
                                <summary>ATLAS Procedural Pamphlet</summary>
                                <div style="margin-top:6px; color:var(--text-dim);">${escapeHtml(s.atlas_pamphlet)}</div>
                            </details>
                            <details class="skill-details">
                                <summary>Source Code (${s.file_path})</summary>
                                <div class="skill-code-box">${escapeHtml(s.code || '# Code unavailable on disk')}</div>
                            </details>
                        </div>
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:6px;">
                            <button class="btn-action" onclick="runSkill('${s.name}', ${idx})">▶ Test Run Tool</button>
                            <span style="font-size:0.75rem; color:var(--text-dim); font-family:var(--font-mono);">Sandbox Checkpointed</span>
                        </div>
                        <div class="skill-output-box" id="skill-out-${idx}"></div>
                    </div>
                `).join('');
            } catch (e) {
                console.error('Failed to load skills:', e);
            }
        }

        async function runSkill(skillName, idx) {
            const outBox = document.getElementById(`skill-out-${idx}`);
            outBox.style.display = 'block';
            outBox.innerText = `[Sandbox]: Initializing shadow Git checkpoint & executing ${skillName}...\n`;

            try {
                const res = await fetch('/api/skills/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: skillName })
                });
                const data = await res.json();
                if (data.status === 'SUCCESS') {
                    outBox.innerText = `$ python cortex/skills/library/${skillName}.py\n\n` + (data.stdout || '(Executed with 0 stdout)');
                } else {
                    outBox.style.color = '#ef4444';
                    outBox.innerText = `[Execution ${data.status}]: Exit Code ${data.exit_code}\n` + (data.stderr || data.stdout || '');
                }
            } catch (e) {
                outBox.style.color = '#ef4444';
                outBox.innerText = `Error running skill: ` + e;
            }
        }

        async function synthesizeCustomSkill() {
            const desc = document.getElementById('synth-desc').value.trim();
            if (!desc) { alert('Please enter a task description'); return; }
            await triggerSkillSynthesis(desc);
        }

        async function synthesizeCurriculum() {
            const task = document.getElementById('curr-task').innerText.trim();
            await triggerSkillSynthesis(task);
        }

        async function triggerSkillSynthesis(desc) {
            switchTab('stage');
            appendMessage(`Synthesizing autopoietic skill: "${desc}"...`, 'msg-user');
            showThinkingIndicator();

            try {
                const res = await fetch('/api/skills/synthesize', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ description: desc })
                });
                const data = await res.json();
                removeThinkingIndicator();
                appendMessage(`Skill Synthesis Result:\n${data.stdout || JSON.stringify(data)}`, 'msg-cortex');
            } catch (e) {
                removeThinkingIndicator();
                appendMessage(`Synthesis Error: ${e}`, 'msg-cortex');
            }
        }

        // ==================== 11. CEDAR GOVERNANCE FUNCTIONS ====================
        async function loadGovernancePane() {
            try {
                const res = await fetch('/api/governance');
                const data = await res.json();

                document.getElementById('gov-cedar-path').innerText = data.cedar_path || 'config/policies.cedar';
                document.getElementById('gov-policy-code').innerText = data.policy_code || '# No custom policies configured';
                document.getElementById('gov-working-diff').innerText = data.working_tree_diff || 'Working tree clean.';

                const tbody = document.getElementById('checkpoints-body');
                if (!data.checkpoints || data.checkpoints.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="3" style="text-align:center; color:var(--text-dim);">No shadow checkpoints recorded yet.</td></tr>`;
                    return;
                }

                tbody.innerHTML = data.checkpoints.slice(0, 15).map(cp => `
                    <tr>
                        <td><b>${escapeHtml(cp.label)}</b> <span style="font-size:0.75rem; color:var(--text-dim);">(${escapeHtml(cp.task_id)})</span></td>
                        <td><code>${escapeHtml(cp.sha)}</code></td>
                        <td><button class="btn-restore" onclick="restoreCheckpoint('${cp.task_id}', '${cp.label}')">↺ Rollback</button></td>
                    </tr>
                `).join('');
            } catch (e) {
                console.error('Failed to load governance:', e);
            }
        }

        async function testPolicy() {
            const action = document.getElementById('pdp-action').value;
            const resPath = document.getElementById('pdp-resource').value.trim();
            const resultBox = document.getElementById('pdp-result-box');

            try {
                const res = await fetch('/api/governance/test', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: action, resource: resPath })
                });
                const data = await res.json();
                resultBox.style.display = 'block';

                let verdictClass = 'verdict-allow';
                if (data.verdict === 'ESCALATE') verdictClass = 'verdict-escalate';
                else if (data.verdict === 'DENY') verdictClass = 'verdict-deny';

                resultBox.className = `pdp-result ${verdictClass}`;
                resultBox.innerHTML = `
                    <div style="font-weight:700; font-size:0.95rem; margin-bottom:4px;">VERDICT: ${data.verdict} (${data.evaluation_time_ms.toFixed(2)} ms)</div>
                    <div><b>Reason:</b> ${data.reason}</div>
                    <div style="margin-top:4px; font-size:0.78rem; opacity:0.85;">Blast Radius: ${data.blast_radius} | Reversibility: ${data.reversibility}</div>
                `;
            } catch (e) {
                alert('Policy test failed: ' + e);
            }
        }

        async function createManualCheckpoint() {
            try {
                const res = await fetch('/api/governance/checkpoint', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ label: 'manual' })
                });
                const data = await res.json();
                if (data.status === 'SUCCESS') {
                    alert(`Created shadow checkpoint ${data.sha} under ${data.ref}`);
                    loadGovernancePane();
                }
            } catch (e) {
                alert('Checkpoint failed: ' + e);
            }
        }

        async function restoreCheckpoint(taskId, label) {
            if (!confirm(`Are you sure you want to deterministically rollback working tree to checkpoint ${taskId}/${label}?`)) {
                return;
            }
            try {
                const res = await fetch('/api/governance/restore', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ task_id: taskId, label: label })
                });
                const data = await res.json();
                if (data.status === 'SUCCESS') {
                    alert('Working tree restored successfully!');
                    loadGovernancePane();
                }
            } catch (e) {
                alert('Rollback failed: ' + e);
            }
        }

        // ==================== 12. LIVE EXECUTION & DAEMONS MODULE ====================
        let currentProcessTelemetry = { cortex_children: [], desktop_applications: [], system_processes: [] };
        let activeProcessTab = 'cortex';

        function toggleSectionCollapse(bodyId, btnEl) {
            const el = document.getElementById(bodyId);
            if (!el) return;
            const isHidden = (el.style.display === 'none');
            el.style.display = isHidden ? (bodyId.includes('terminal') ? 'flex' : 'block') : 'none';
            if (btnEl) btnEl.innerHTML = isHidden ? '<span>▾</span> Collapse' : '<span>▸</span> Expand';
        }

        async function loadExecutionPane() {
            loadPipelineStepper();
            loadDaemonsTelemetry();
            loadProcessesTelemetry();
        }

        async function loadPipelineStepper() {
            try {
                const res = await fetch('/api/execution/pipeline');
                const data = await res.json();
                const container = document.getElementById('pipeline-stepper-box');
                if (!container || !data.stages) return;

                container.innerHTML = data.stages.map(s => {
                    const statusClass = `pipe-status-${s.status.toLowerCase()}`;
                    return `
                        <div class="pipe-stage-card">
                            <div class="pipe-stage-head">
                                <span class="pipe-num">STAGE 0${s.stage}</span>
                                <span class="pipe-status-pill ${statusClass}">${s.status}</span>
                            </div>
                            <div class="pipe-title">${escapeHtml(s.name)}</div>
                            <div class="pipe-comp">${escapeHtml(s.component)}</div>
                            <div class="pipe-desc">${escapeHtml(s.details)}</div>
                        </div>
                    `;
                }).join('');
            } catch (e) {
                console.error('Failed to load pipeline:', e);
            }
        }

        async function loadDaemonsTelemetry() {
            try {
                const res = await fetch('/api/execution/daemons');
                const data = await res.json();
                const grid = document.getElementById('daemons-grid');
                if (!grid) return;

                grid.innerHTML = `
                    <!-- 1. Uvicorn -->
                    <div class="daemon-card tilt-card">
                        <div class="daemon-head">
                            <span class="daemon-name">🤖 Web & WS Daemon</span>
                            <span class="daemon-badge daemon-running">${data.uvicorn_server.status}</span>
                        </div>
                        <div class="daemon-metric">PID: <span class="val">${data.uvicorn_server.pid} (Port ${data.uvicorn_server.port})</span></div>
                        <div class="daemon-metric">CPU: <span class="val">${data.uvicorn_server.cpu_percent}%</span></div>
                        <div class="daemon-metric">Memory RSS: <span class="val">${data.uvicorn_server.memory_mb} MB</span></div>
                        <div class="daemon-metric">Threads: <span class="val">${data.uvicorn_server.threads}</span></div>
                        <div class="daemon-metric">Uptime: <span class="val">${data.uvicorn_server.uptime_seconds}s</span></div>
                    </div>

                    <!-- 2. Ambient Loop -->
                    <div class="daemon-card tilt-card">
                        <div class="daemon-head">
                            <span class="daemon-name">⏱️ Ambient Tick Worker</span>
                            <span class="daemon-badge ${data.ambient_worker.active ? 'daemon-running' : 'daemon-paused'}">${data.ambient_worker.status}</span>
                        </div>
                        <div class="daemon-metric">Frequency: <span class="val">Every ${data.ambient_worker.interval_seconds}s</span></div>
                        <div class="daemon-metric">Last Tick: <span class="val">#${data.ambient_worker.last_tick_id}</span></div>
                        <div class="daemon-metric">Mode: <span class="val">${data.ambient_worker.active ? 'Autonomous Continuous' : 'On-Demand Reactive'}</span></div>
                        <div class="daemon-metric">Duplex: <span class="val">${data.uvicorn_server.websocket_clients} Active WebSocket(s)</span></div>
                    </div>

                    <!-- 3. StallBreaker -->
                    <div class="daemon-card tilt-card">
                        <div class="daemon-head">
                            <span class="daemon-name">🛡️ StallBreaker Sentinel</span>
                            <span class="daemon-badge ${data.stall_breaker.panic_active ? 'daemon-paused' : 'daemon-nominal'}">${data.stall_breaker.status}</span>
                        </div>
                        <div class="daemon-metric">Panic Switch: <span class="val">${data.stall_breaker.panic_active ? 'ACTIVATED' : 'DISARMED'}</span></div>
                        <div class="daemon-metric">Stall Timeout: <span class="val">45.0s Hardware Gate</span></div>
                        <div class="daemon-metric">Status: <span class="val">${escapeHtml(data.stall_breaker.reason || 'Nominal Subsystem Bus')}</span></div>
                    </div>

                    <!-- 4. Digital Sleep Daemon -->
                    <div class="daemon-card tilt-card">
                        <div class="daemon-head">
                            <span class="daemon-name">💤 Sleep Daemon</span>
                            <span class="daemon-badge daemon-nominal">STANDBY</span>
                        </div>
                        <div class="daemon-metric">Engrams Stored: <span class="val">${data.sleep_daemon.engrams_consolidated} Atomic Engrams</span></div>
                        <div class="daemon-metric">Stage 1-4: <span class="val">WAL / Bigram / LoRA</span></div>
                        <div class="daemon-metric">Scheduler: <span class="val">AC Power & Idle State</span></div>
                    </div>
                `;
            } catch (e) {
                console.error('Failed to load daemons:', e);
            }
        }

        async function loadProcessesTelemetry() {
            try {
                const res = await fetch('/api/execution/processes');
                currentProcessTelemetry = await res.json();
                if (activeProcessTab === 'cortex' && (!currentProcessTelemetry.cortex_children || currentProcessTelemetry.cortex_children.length === 0)) {
                    if (currentProcessTelemetry.desktop_applications && currentProcessTelemetry.desktop_applications.length > 0) {
                        activeProcessTab = 'desktop';
                        document.querySelectorAll('#pane-execution .filter-tag').forEach(t => t.classList.remove('active'));
                        const ptag = document.getElementById('ptag-desktop');
                        if (ptag) ptag.classList.add('active');
                    }
                }
                renderProcessTable();
            } catch (e) {
                console.error('Failed to load processes:', e);
            }
        }

        function toggleProcessTab(tabName, el) {
            activeProcessTab = tabName;
            document.querySelectorAll('#pane-execution .filter-tag').forEach(t => t.classList.remove('active'));
            el.classList.add('active');
            renderProcessTable();
        }

        function filterProcessTable(query) {
            renderProcessTable(query);
        }

        function renderProcessTable(filterQuery) {
            const tbody = document.getElementById('processes-table-body');
            if (!tbody) return;

            let procs = [];
            if (activeProcessTab === 'cortex') {
                procs = currentProcessTelemetry.cortex_children || [];
            } else if (activeProcessTab === 'desktop') {
                procs = currentProcessTelemetry.desktop_applications || [];
            } else {
                procs = currentProcessTelemetry.system_processes || [];
            }

            const q = (filterQuery || document.getElementById('proc-search-input').value || '').toLowerCase().trim();
            if (q) {
                procs = procs.filter(p => (p.name || '').toLowerCase().includes(q) || String(p.pid || '').includes(q));
            }

            if (procs.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--text-dim); padding:20px;">No matching processes active in ${activeProcessTab.toUpperCase()} scope.</td></tr>`;
                return;
            }

            tbody.innerHTML = procs.map(p => {
                const pidStr = p.pid ? `<code>${p.pid}</code>` : (p.process_count ? `<b>${p.process_count} instances</b>` : '-');
                const memStr = p.mem_mb ? `${p.mem_mb} MB` : (p.mem_pct ? `${p.mem_pct}%` : '-');
                const cpuStr = p.cpu_pct !== undefined ? `${p.cpu_pct}%` : '0.0%';
                const statusStr = `<span class="layer-badge layer-entity">${p.status || 'running'}</span>`;
                const details = p.cmdline || p.exe || 'Native Win32 Subprocess';

                return `
                    <tr>
                        <td>${pidStr}</td>
                        <td><b>${escapeHtml(p.name)}</b></td>
                        <td><span style="color:var(--accent-cyan); font-weight:600;">${cpuStr}</span></td>
                        <td>${memStr}</td>
                        <td>${statusStr}</td>
                        <td style="color:var(--text-dim); font-size:0.75rem; max-width:280px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${escapeHtml(details)}">${escapeHtml(details)}</td>
                    </tr>
                `;
            }).join('');
        }

        // Terminal Execution in Governed Sandbox
        function runPresetTerminal(cmd) {
            const input = document.getElementById('terminal-cmd-input');
            if (input) {
                input.value = cmd;
                executeTerminalCommand();
            }
        }

        async function executeTerminalCommand() {
            const input = document.getElementById('terminal-cmd-input');
            const cmd = input.value.trim();
            if (!cmd) return;

            const screen = document.getElementById('terminal-screen-box');
            appendTerminalLine(`cortex@laptop:~$ ${cmd}`, 'term-line-cmd');
            input.value = '';

            try {
                const res = await fetch('/api/execution/terminal', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command: cmd })
                });
                const data = await res.json();
                
                if (data.status === 'DENIED') {
                    appendTerminalLine(`[Cedar Policy DENY]: ${data.stderr}`, 'term-line-stderr');
                } else if (data.status === 'FAILED_ROLLED_BACK') {
                    appendTerminalLine(`[Exit Code ${data.exit_code} - Rolled back to checkpoint ${data.checkpoint_sha}]:\n${data.stderr || data.stdout}`, 'term-line-stderr');
                } else {
                    if (data.stdout) appendTerminalLine(data.stdout, 'term-line-stdout');
                    if (data.stderr) appendTerminalLine(data.stderr, 'term-line-stderr');
                    appendTerminalLine(`✓ Executed in ${data.execution_time_ms} ms (Pre-checkpoint: ${data.checkpoint_sha || 'N/A'}, Exit 0)`, 'term-line-meta');
                }
            } catch (e) {
                appendTerminalLine(`Terminal Error: ${e}`, 'term-line-stderr');
            }

            screen.scrollTop = screen.scrollHeight;
            loadProcessesTelemetry();
        }

        function appendTerminalLine(text, className) {
            const screen = document.getElementById('terminal-screen-box');
            const div = document.createElement('div');
            div.className = className;
            div.innerText = text;
            screen.appendChild(div);
            screen.scrollTop = screen.scrollHeight;
        }

        function clearTerminalScreen() {
            const screen = document.getElementById('terminal-screen-box');
            if (screen) {
                screen.innerHTML = `<div class="term-line" style="color:var(--text-dim);">[Terminal cleared. Ready for sandbox execution.]</div>`;
            }
        }

        // ==================== 13. MEDIA & PANIC CONTROLS ====================
        async function pollLiveMedia() {
            try {
                const res = await fetch('/api/media');
                const data = await res.json();
                const ticker = document.getElementById('media-ticker-text');
                if (!ticker) return;
                if (data.title && data.title !== 'Unknown Title') {
                    ticker.innerText = `${data.title} - ${data.artist || ''}`;
                    ticker.style.color = '#10b981';
                } else {
                    ticker.innerText = 'No active audio';
                    ticker.style.color = 'var(--text-dim)';
                }
            } catch (e) {}
        }
        setInterval(pollLiveMedia, 6000);
        pollLiveMedia();

        async function controlMedia(cmd, evt) {
            if (evt) evt.stopPropagation();
            try {
                await fetch('/api/media/control', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command: cmd })
                });
                setTimeout(pollLiveMedia, 800);
            } catch (e) {
                console.error('Media control failed:', e);
            }
        }

        // ==================== VOICE PERSONA & BARGE-IN ====================
        let voiceSpeechEnabled = true;
        let currentPlayingAudio = null;
        let isVoiceSpeaking = false;
        let recognition = null;
        let isRecognizing = false;

        function stopCurrentVoiceAudio() {
            if (currentPlayingAudio) {
                try {
                    currentPlayingAudio.onplay = null;
                    currentPlayingAudio.onended = null;
                    currentPlayingAudio.onerror = null;
                    currentPlayingAudio.pause();
                    currentPlayingAudio.currentTime = 0;
                } catch (e) {}
                currentPlayingAudio = null;
            }
            if (window.speechSynthesis) {
                try { window.speechSynthesis.cancel(); } catch (e) {}
            }
            isVoiceSpeaking = false;
            const icon = document.getElementById('voice-status-icon');
            if (icon) icon.innerText = voiceSpeechEnabled ? '🎙️' : '🔇';
        }

        function cleanTextForSpeech(text) {
            if (!text) return '';
            return text
                .replace(/```[\s\S]*?```/g, ' [Code executed in background] ')
                .replace(/`([^`]+)`/g, '$1')
                .replace(/https?:\/\/\S+/g, '')
                .replace(/file:\/\/\/\S+/g, '')
                .replace(/^[*#-]+\s+/gm, '')
                .replace(/[*_]{1,3}([^*_]+)[*_]{1,3}/g, '$1')
                .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
                .replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '')
                .replace(/\s+/g, ' ')
                .trim();
        }

        async function playVoiceAudioForText(text, persona) {
            if (!voiceSpeechEnabled) return;
            const clean = cleanTextForSpeech(text);
            if (!clean) return;

            stopCurrentVoiceAudio();

            const targetPersona = persona || document.getElementById('voice-persona-select')?.value || 'jarvis';
            const audioUrl = `/api/voice/audio?text=${encodeURIComponent(clean)}&persona=${encodeURIComponent(targetPersona)}`;

            const icon = document.getElementById('voice-status-icon');
            if (icon) icon.innerText = '🗣️';
            isVoiceSpeaking = true;

            let fallbackTriggered = false;
            const triggerFallback = () => {
                if (fallbackTriggered) return;
                fallbackTriggered = true;
                if (currentPlayingAudio) {
                    try {
                        currentPlayingAudio.onplay = null;
                        currentPlayingAudio.onended = null;
                        currentPlayingAudio.onerror = null;
                        currentPlayingAudio.pause();
                    } catch (e) {}
                    currentPlayingAudio = null;
                }
                speakWebSpeechSynthesis(clean, targetPersona);
            };

            try {
                const audio = new Audio(audioUrl);
                currentPlayingAudio = audio;

                audio.onplay = () => {
                    isVoiceSpeaking = true;
                    if (icon) icon.innerText = '🗣️';
                };
                audio.onended = () => {
                    stopCurrentVoiceAudio();
                };
                audio.onerror = () => {
                    if (currentPlayingAudio === audio) {
                        triggerFallback();
                    }
                };

                const playPromise = audio.play();
                if (playPromise !== undefined) {
                    playPromise.catch((err) => {
                        console.warn('Audio play failed, falling back to Web Speech:', err);
                        if (currentPlayingAudio === audio) {
                            triggerFallback();
                        }
                    });
                }
            } catch (err) {
                triggerFallback();
            }
        }

        function speakWebSpeechSynthesis(cleanText, persona) {
            if (!window.speechSynthesis) {
                stopCurrentVoiceAudio();
                return;
            }
            window.speechSynthesis.cancel();

            const utter = new SpeechSynthesisUtterance(cleanText);
            const voices = window.speechSynthesis.getVoices();
            let selectedVoice = null;
            const p = (persona || '').toLowerCase();

            if (p.includes('jarvis') || p.includes('analytic')) {
                selectedVoice = voices.find(v => (v.lang === 'en-GB' || v.lang.startsWith('en')) && (v.name.includes('Ryan') || v.name.includes('George') || v.name.includes('David') || v.name.includes('Oliver') || v.name.includes('Male')));
                utter.rate = 1.02;
                utter.pitch = 0.95;
            } else if (p.includes('friday') || p.includes('cautious')) {
                selectedVoice = voices.find(v => (v.name.includes('Ava') || v.name.includes('Zira') || v.name.includes('Jenny') || (v.lang.startsWith('en') && v.name.includes('Female'))));
                utter.rate = 1.0;
                utter.pitch = 1.06;
            } else if (p.includes('pragmatic') || p.includes('guy')) {
                selectedVoice = voices.find(v => (v.name.includes('Guy') || v.name.includes('Christopher') || (v.lang === 'en-US' && v.name.includes('Male'))));
                utter.rate = 1.08;
                utter.pitch = 1.0;
            }

            if (!selectedVoice) {
                selectedVoice = voices.find(v => v.lang.startsWith('en')) || voices[0];
            }
            if (selectedVoice) utter.voice = selectedVoice;

            utter.onstart = () => {
                isVoiceSpeaking = true;
                const icon = document.getElementById('voice-status-icon');
                if (icon) icon.innerText = '🗣️';
            };
            utter.onend = () => {
                stopCurrentVoiceAudio();
            };
            utter.onerror = () => {
                stopCurrentVoiceAudio();
            };

            window.speechSynthesis.speak(utter);
        }

        function playVoiceAudio(btn) {
            const rawText = decodeURIComponent(btn.getAttribute('data-text') || '');
            const persona = btn.getAttribute('data-persona') || '';
            playVoiceAudioForText(rawText, persona);
        }

        function playPerspectiveVoice(perspective, thoughtText, event) {
            if (event) event.stopPropagation();
            let persona = 'jarvis';
            const pLower = perspective.toLowerCase();
            if (pLower.includes('analytic')) persona = 'edith';
            else if (pLower.includes('pragmatic')) persona = 'guy';
            else if (pLower.includes('cautious')) persona = 'friday';

            const spoken = `${perspective} Agent proposal: ${thoughtText}`;
            playVoiceAudioForText(spoken, persona);
        }

        function toggleVoiceRecognition() {
            const micBtn = document.getElementById('btn-mic-toggle');
            const micIcon = document.getElementById('mic-icon');
            const input = document.getElementById('chat-input');

            const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRec) {
                alert('Web Speech Recognition is not supported in this browser. Please use Google Chrome, Edge, or Brave.');
                return;
            }

            if (isRecognizing && recognition) {
                recognition.stop();
                return;
            }

            try {
                recognition = new SpeechRec();
                recognition.continuous = false;
                recognition.interimResults = true;
                recognition.lang = 'en-US';

                recognition.onstart = () => {
                    isRecognizing = true;
                    if (micBtn) micBtn.classList.add('listening');
                    if (micIcon) micIcon.innerText = '🔴';
                    if (input) input.placeholder = 'Listening... Speak your command to CortexOS now.';
                    stopCurrentVoiceAudio();
                    bargeInStopVoice();
                };

                recognition.onresult = (event) => {
                    let transcript = '';
                    for (let i = event.resultIndex; i < event.results.length; ++i) {
                        transcript += event.results[i][0].transcript;
                    }
                    if (input) input.value = transcript;
                };

                recognition.onerror = (event) => {
                    console.warn('Speech recognition error:', event.error);
                    isRecognizing = false;
                    if (micBtn) micBtn.classList.remove('listening');
                    if (micIcon) micIcon.innerText = '🎙️';
                    if (input) input.placeholder = "Ask CortexOS or speak with your mic (e.g. 'tell me about my system', 'which song is playing?')...";
                };

                recognition.onend = () => {
                    isRecognizing = false;
                    if (micBtn) micBtn.classList.remove('listening');
                    if (micIcon) micIcon.innerText = '🎙️';
                    if (input) {
                        input.placeholder = "Ask CortexOS or speak with your mic (e.g. 'tell me about my system', 'which song is playing?')...";
                        const query = input.value.trim();
                        if (query.length > 2) {
                            sendMessage();
                        }
                    }
                };

                recognition.start();
            } catch (e) {
                console.error('Failed to start speech recognition:', e);
                isRecognizing = false;
                if (micBtn) micBtn.classList.remove('listening');
                if (micIcon) micIcon.innerText = '🎙️';
            }
        }

        function triggerSystemGreeting() {
            const greeting = "Greetings Soham. CortexOS is synchronized and monitoring your laptop. All memory and cognitive subsystems are ready. How can I assist you?";
            appendMessage(greeting, 'msg-cortex');
            playVoiceAudioForText(greeting, document.getElementById('voice-persona-select')?.value || 'jarvis');
        }

        async function switchVoicePersona(persona) {
            try {
                const res = await fetch('/api/voice/persona', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ persona: persona })
                });
                const d = await res.json();
                if (d.status === 'SUCCESS') {
                    appendMessage(`🎙️ Neural voice persona switched to **${persona.toUpperCase()}** (${d.description}).`, 'msg-cortex');
                    playVoiceAudioForText(`Neural voice switched to ${persona}. Systems nominal.`, persona);
                }
            } catch (e) {
                console.error('Failed to switch voice persona:', e);
            }
        }

        async function bargeInStopVoice() {
            stopCurrentVoiceAudio();
            try {
                await fetch('/api/voice/stop', { method: 'POST' });
                const icon = document.getElementById('voice-status-icon');
                if (icon) {
                    icon.innerText = '⏹️';
                    setTimeout(() => { icon.innerText = voiceSpeechEnabled ? '🎙️' : '🔇'; }, 1000);
                }
            } catch (e) {}
        }

        async function toggleVoiceSpeech() {
            voiceSpeechEnabled = !voiceSpeechEnabled;
            if (!voiceSpeechEnabled) stopCurrentVoiceAudio();
            try {
                await fetch('/api/voice/toggle', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ enabled: voiceSpeechEnabled })
                });
                const btn = document.getElementById('btn-voice-toggle');
                const icon = document.getElementById('voice-status-icon');
                if (btn) btn.innerText = voiceSpeechEnabled ? '🔊' : '🔈';
                if (icon) icon.innerText = voiceSpeechEnabled ? '🎙️' : '🔇';
                appendMessage(`Neural voice speech output is now **${voiceSpeechEnabled ? 'ACTIVE' : 'MUTED'}**.`, 'msg-cortex');
                if (voiceSpeechEnabled) {
                    playVoiceAudioForText("Voice output enabled.", document.getElementById('voice-persona-select')?.value || 'jarvis');
                }
            } catch (e) {}
        }

        async function togglePanicKillswitch() {
            const btn = document.getElementById('btn-panic');
            const isPanic = btn.innerText.includes('RESET');
            if (isPanic) {
                await fetch('/api/governance/reset_panic', { method: 'POST' });
                btn.innerText = '🚨 PANIC STOP';
                btn.style.background = 'rgba(239, 68, 68, 0.18)';
                btn.style.color = 'var(--accent-red)';
                appendMessage('Operator reset panic switch. Normal cognitive ticks resumed.', 'msg-cortex');
            } else {
                if (!confirm('Activate Emergency Hardware Panic Switch? This halts all autonomous actions immediately.')) return;
                await fetch('/api/governance/panic', { method: 'POST' });
                btn.innerText = '🛡️ RESET PANIC';
                btn.style.background = '#ef4444';
                btn.style.color = '#fff';
                appendMessage('🚨 EMERGENCY PANIC KILLSWITCH TRIGGERED! All autonomous execution and actions are frozen.', 'msg-cortex');
            }
        }

        // Keyboard Navigation Shortcuts
        window.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === '1') { e.preventDefault(); switchTab('stage'); }
            else if (e.ctrlKey && e.key === '2') { e.preventDefault(); switchTab('memory'); }
            else if (e.ctrlKey && e.key === '3') { e.preventDefault(); switchTab('graph'); }
            else if (e.ctrlKey && e.key === '4') { e.preventDefault(); switchTab('skills'); }
            else if (e.ctrlKey && e.key === '5') { e.preventDefault(); switchTab('governance'); }
            else if (e.ctrlKey && e.key === '6') { e.preventDefault(); switchTab('execution'); }
            else if (e.ctrlKey && e.key.toLowerCase() === 'b') { e.preventDefault(); toggleSidebar(); }
            else if (e.ctrlKey && e.key.toLowerCase() === 'k') {
                e.preventDefault();
                switchTab('stage');
                document.getElementById('chat-input').focus();
            }
        });

        // Initialize Everything on Window Load
        window.addEventListener('DOMContentLoaded', () => {
            connectWebSocket();
            initBackground3D();
            initStage3D();
            initDelegatedTiltPhysics();
            masterRenderLoop();
        });
    </script>
</body>
</html>
"""

# ==================== REST API ENDPOINTS ====================

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    return HTMLResponse(content=HTML_DASHBOARD)

@app.get("/api/status")
async def get_status():
    wm = stack["wm"]
    engine = stack["engine"]
    somato = engine.somato
    return {
        "tick_id": engine.state.tick_id,
        "entropy": 1.0,
        "temperature": engine.state.current_temperature,
        "blocks": {k: {"label": b.label, "value": b.value, "limit": b.char_limit} for k, b in wm.blocks.items()},
        "policy": stack["policy"].cedar_path,
        "telemetry": somato.get_hardware_telemetry()
    }

# Live Media Playback & Controls
@app.get("/api/media")
async def get_live_media():
    somato = stack["engine"].somato
    return await somato.get_active_media_playback()

@app.post("/api/media/control")
async def control_live_media(req: MediaControlRequest):
    somato = stack["engine"].somato
    return await somato.control_media_playback(req.command)

# 1. Working Memory Endpoints
@app.get("/api/blocks")
async def get_blocks():
    wm = stack["wm"]
    return {
        label: {
            "label": b.label,
            "value": b.value,
            "char_limit": b.char_limit,
            "char_count": len(b.value)
        }
        for label, b in wm.blocks.items()
    }

@app.post("/api/blocks/{label}")
async def update_block(label: str, req: BlockUpdateRequest):
    wm = stack["wm"]
    if label not in wm.blocks:
        raise HTTPException(status_code=404, detail=f"Block '{label}' not found.")
    wm.update_block(label, req.value)
    b = wm.blocks[label]
    return {
        "status": "SUCCESS",
        "label": label,
        "value": b.value,
        "char_limit": b.char_limit,
        "char_count": len(b.value)
    }

# 2. Bi-Temporal Knowledge Graph Endpoints
@app.get("/api/graph")
async def get_graph():
    memory = stack["memory"]
    edges = memory.get_all_graph_edges(limit=100)
    engrams = memory.get_recent_engrams(limit=50)
    return {
        "edges": edges,
        "engrams": engrams,
        "total_edges": len(edges),
        "total_engrams": len(engrams)
    }

@app.post("/api/graph/assert")
async def assert_graph_edge(req: GraphAssertRequest):
    memory = stack["memory"]
    edge_id = memory.add_graph_edge(
        source=req.source,
        target=req.target,
        relation=req.relation,
        layer=req.layer,
        provenance=req.provenance
    )
    return {"status": "SUCCESS", "edge_id": edge_id}

# 3. Procedural Skill Crystallizer Endpoints
@app.get("/api/skills")
async def get_skills():
    memory = stack["memory"]
    crystallizer = stack["skills"]
    skills = memory.get_all_skills()
    enriched = []
    for s in skills:
        code = ""
        p = Path(s["file_path"])
        if p.exists():
            try:
                code = p.read_text(encoding="utf-8")
            except Exception:
                pass
        enriched.append({
            **s,
            "code": code
        })
    challenge = crystallizer.curriculum.get_next_challenge()
    return {
        "skills": enriched,
        "curriculum_challenge": challenge
    }

@app.post("/api/skills/run")
async def run_skill(req: SkillRunRequest):
    memory = stack["memory"]
    sandbox = stack["sandbox"]
    skills = memory.get_all_skills()
    matching = [s for s in skills if s["name"] == req.name]
    if not matching:
        fallback = Path("cortex/skills/library") / f"{req.name}.py"
        if fallback.exists():
            skill_path = str(fallback)
        else:
            raise HTTPException(status_code=404, detail=f"Skill '{req.name}' not found.")
    else:
        skill_path = matching[0]["file_path"]

    task_id = f"manual-exec-{req.name}-{int(time.time())}"
    result = await sandbox.run_verified_skill(
        task_id=task_id,
        skill_path=skill_path,
        args={"cli_args": req.args or []}
    )
    return {
        "status": result.get("status", "UNKNOWN"),
        "exit_code": result.get("exit_code", -1),
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr", "")
    }

@app.post("/api/skills/synthesize")
async def synthesize_skill(req: SkillSynthesizeRequest):
    crystallizer = stack["skills"]
    task = {
        "action": "crystallize_skill",
        "description": req.description
    }
    result = await crystallizer.execute_or_synthesize(task)
    return result

# 4. Cedar Governance & Checkpoints Endpoints
@app.get("/api/governance")
async def get_governance():
    sandbox = stack["sandbox"]
    policy_engine = stack["policy"]
    policy_code = ""
    if os.path.exists(policy_engine.cedar_path):
        try:
            with open(policy_engine.cedar_path, "r", encoding="utf-8") as f:
                policy_code = f.read()
        except Exception:
            pass
    checkpoints = sandbox.checkpoint_mgr.list_checkpoints()
    diff = sandbox.checkpoint_mgr.get_working_tree_diff()
    return {
        "cedar_path": policy_engine.cedar_path,
        "policy_code": policy_code,
        "checkpoints": checkpoints,
        "working_tree_diff": diff
    }

@app.post("/api/governance/test")
async def test_governance_policy(req: GovernanceTestRequest):
    policy_engine = stack["policy"]
    action_dict = {"action": req.action, "resource": req.resource or ""}
    evaluation = policy_engine.evaluate(action_dict, context=req.context or {})
    return {
        "verdict": evaluation.status.value,
        "reason": evaluation.reason,
        "evaluation_time_ms": evaluation.evaluation_time_ms,
        "reversibility": evaluation.reversibility,
        "blast_radius": evaluation.blast_radius
    }

@app.post("/api/governance/checkpoint")
async def create_checkpoint(req: CheckpointCreateRequest):
    sandbox = stack["sandbox"]
    task_id = f"manual-{int(time.time())}"
    label = req.label or "user"
    sha = sandbox.checkpoint_mgr.create_checkpoint(task_id, label=label)
    return {
        "status": "SUCCESS",
        "task_id": task_id,
        "label": label,
        "sha": sha[:10],
        "ref": f"refs/checkpoints/{task_id}/{label}"
    }

@app.post("/api/governance/restore")
async def restore_checkpoint(req: CheckpointRestoreRequest):
    sandbox = stack["sandbox"]
    try:
        success = sandbox.checkpoint_mgr.restore_checkpoint(req.task_id, req.label or "pre")
        return {"status": "SUCCESS" if success else "FAILED"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/governance/panic")
async def get_panic_status():
    breaker = stack["engine"].stall_breaker
    return {"panic_active": breaker.is_panic_triggered(), "panic_reason": breaker.panic_reason}

@app.post("/api/governance/panic")
async def trigger_panic():
    breaker = stack["engine"].stall_breaker
    sandbox = stack["sandbox"]
    breaker.trigger_panic("Emergency operator killswitch from Web Dashboard")
    task_id = f"panic-{int(time.time())}"
    sha = sandbox.checkpoint_mgr.create_checkpoint(task_id, label="panic_snapshot")
    return {"status": "PANIC_TRIGGERED", "checkpoint_sha": sha[:10]}

@app.post("/api/governance/reset_panic")
async def reset_panic():
    breaker = stack["engine"].stall_breaker
    breaker.reset_panic()
    return {"status": "PANIC_RESET"}

# 5. Sleep Consolidation Endpoint
@app.post("/api/sleep")
async def trigger_sleep():
    report = await stack["sleep"].run_consolidation_cycle()
    return {"status": "SUCCESS", "report": report.__dict__}


# 6. Live Execution, Terminal Sandbox, Daemons & Child Processes
@app.post("/api/execution/terminal")
async def run_terminal_command(req: TerminalRunRequest):
    sandbox = stack["sandbox"]
    res = await sandbox.run_command_in_sandbox(req.command, timeout=req.timeout or 30)
    return res

@app.get("/api/execution/daemons")
async def get_daemons_status():
    proc = psutil.Process(os.getpid())
    engine = stack["engine"]
    breaker = engine.stall_breaker
    memory = stack["memory"]
    
    uptime_sec = round(time.time() - proc.create_time(), 1)
    
    try:
        cpu_pct = proc.cpu_percent(interval=0.01)
        mem_mb = round(proc.memory_info().rss / (1024 * 1024), 2)
        threads = proc.num_threads()
    except Exception:
        cpu_pct, mem_mb, threads = 0.0, 0.0, 1

    engrams_count = len(memory.get_recent_engrams(limit=500))

    return {
        "uvicorn_server": {
            "name": "FastAPI / Uvicorn Cognitive Gateway",
            "pid": os.getpid(),
            "port": 8000,
            "status": "RUNNING",
            "uptime_seconds": uptime_sec,
            "cpu_percent": cpu_pct,
            "memory_mb": mem_mb,
            "threads": threads,
            "websocket_clients": len(active_websockets)
        },
        "ambient_worker": {
            "name": "Ambient Cognitive Tick Daemon (GWA)",
            "status": "RUNNING" if ambient_daemon_active else "PAUSED",
            "interval_seconds": 15,
            "last_tick_id": engine.state.tick_id,
            "active": ambient_daemon_active
        },
        "stall_breaker": {
            "name": "Hardware StallBreaker Panic Sentinel",
            "status": "TRIGGERED" if breaker.is_panic_triggered() else "NOMINAL",
            "panic_active": breaker.is_panic_triggered(),
            "reason": breaker.panic_reason
        },
        "sleep_daemon": {
            "name": "Asynchronous Digital Sleep Consolidation Daemon",
            "status": "STANDBY (Idle-Scheduled)",
            "engrams_consolidated": engrams_count,
            "last_cycle_status": "READY"
        }
    }

@app.get("/api/execution/processes")
async def get_processes_telemetry():
    proc = psutil.Process(os.getpid())
    somato = stack["engine"].somato
    
    cortex_children = []
    try:
        for child in proc.children(recursive=True):
            try:
                cortex_children.append({
                    "pid": child.pid,
                    "ppid": child.ppid(),
                    "name": child.name(),
                    "status": child.status(),
                    "cpu_pct": round(child.cpu_percent(interval=None), 1),
                    "mem_mb": round(child.memory_info().rss / (1024 * 1024), 2),
                    "cmdline": " ".join(child.cmdline()[:4]) if child.cmdline() else ""
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception:
        pass

    system_procs = somato.get_processes(top_n=20, sort_by="memory")
    desktop_apps = somato.get_user_applications(top_n=10)

    return {
        "cortex_pid": os.getpid(),
        "cortex_children": cortex_children,
        "desktop_applications": desktop_apps,
        "system_processes": system_procs,
        "total_system_processes": len(psutil.pids())
    }

@app.get("/api/execution/pipeline")
async def get_pipeline_trace():
    engine = stack["engine"]
    state = engine.state
    wm = stack["wm"]
    
    return {
        "tick_id": state.tick_id,
        "entropy": 1.0,
        "temperature": state.current_temperature,
        "stages": [
            {
                "stage": 1,
                "name": "Somatosensory Perception",
                "component": "SystemSomatosensory & GSMTC Bus",
                "status": "ACTIVE",
                "details": "Monitoring Windows telemetry, GPU VRAM, active window, and audio playback."
            },
            {
                "stage": 2,
                "name": "Working Memory & LTM Retrieval",
                "component": "Letta Blocks & Bi-Temporal MAGMA Graph",
                "status": "COMPLETED",
                "details": f"4 in-context blocks compiled ({len(wm.compile())} chars) + Hybrid RAG."
            },
            {
                "stage": 3,
                "name": "Tri-Perspective Divergent Generation",
                "component": "Global Workspace Agent Swarm",
                "status": "READY",
                "details": "Specialist Nodes: Analytic, Pragmatic, and Cautious candidate generation."
            },
            {
                "stage": 4,
                "name": "Convergent Critic Scoring & Shannon Entropy",
                "component": "IntrinsicDriveMonitor H(W)",
                "status": "READY",
                "details": f"Evaluates candidates from -5 to +5. H(W) regulated temperature={state.current_temperature:.2f}."
            },
            {
                "stage": 5,
                "name": "Metacognitive Dual-Process Router",
                "component": "System 1 Reflex & HASSUM System 2 Gate",
                "status": "NOMINAL",
                "details": "Sub-100ms reflex routing for hardware/media; HASSUM uncertainty gate for deep tasks."
            },
            {
                "stage": 6,
                "name": "Cedar Policy Decision Point (PDP)",
                "component": "PolicyEngine (policies.cedar)",
                "status": "ENFORCING",
                "details": "Sub-0.1ms deterministic security gates: ALLOW, ESCALATE, DENY."
            },
            {
                "stage": 7,
                "name": "Deterministic Shadow Git Checkpoint",
                "component": "GitShadowCheckpointManager",
                "status": "PINNED",
                "details": "Captures modified & untracked files into refs/checkpoints/ in <1s."
            },
            {
                "stage": 8,
                "name": "Sandboxed OS Subprocess Execution",
                "component": "SandboxRunner",
                "status": "ISOLATED",
                "details": "Sanitized environment execution with automated rollback on non-zero exit."
            },
            {
                "stage": 9,
                "name": "State Transition & Working Memory Patch",
                "component": "Letta Core Memory Re-think & Episodic WAL",
                "status": "SYNCHRONIZED",
                "details": "In-context block patch and lossless Tier 1 append-only SQLite commit."
            }
        ]
    }


# ==================== VOICE REST API ENDPOINTS ====================

@app.get("/api/voice/status")
async def get_voice_status():
    return {
        "enabled": voice_engine.enabled,
        "is_speaking": voice_engine.is_speaking,
        "active_persona": voice_engine.active_persona,
        "personas": voice_engine.list_personas()
    }

@app.post("/api/voice/speak")
async def speak_text(req: VoiceSpeakRequest):
    voice_engine.speak(req.text, persona=req.persona)
    return {"status": "SUCCESS", "message": "Speech playback dispatched."}

@app.post("/api/voice/stop")
async def stop_voice_playback():
    voice_engine.stop()
    return {"status": "SUCCESS", "message": "Speech halted immediately (barge-in)."}

@app.post("/api/voice/persona")
async def set_voice_persona(req: VoicePersonaRequest):
    res = voice_engine.set_persona(req.persona)
    return res

@app.post("/api/voice/toggle")
async def toggle_voice(req: VoiceToggleRequest):
    voice_engine.enabled = req.enabled
    return {"status": "SUCCESS", "enabled": voice_engine.enabled}

@app.get("/api/voice/briefing")
async def get_briefing():
    from cortex.embodiment.session_sentinel import ExecutiveBriefing
    briefing = ExecutiveBriefing(username="Soham")
    return {"status": "SUCCESS", "briefing": briefing.generate()}

@app.post("/api/voice/briefing")
async def deliver_briefing():
    from cortex.embodiment.session_sentinel import ExecutiveBriefing
    briefing = ExecutiveBriefing(username="Soham")
    text = briefing.generate()
    if voice_engine.enabled:
        voice_engine.speak(text)
    return {"status": "SUCCESS", "briefing": text, "spoken": voice_engine.enabled}

@app.get("/api/voice/audio")
async def get_voice_audio(text: str = Query(...), persona: Optional[str] = Query(None)):
    """Streams synthesized MP3 audio for high-fidelity in-browser playback."""
    audio_bytes = await voice_engine.synthesize_audio_async(text, persona=persona)
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Could not synthesize speech.")
    return Response(content=audio_bytes, media_type="audio/mpeg")


# ==================== WEBSOCKET STREAMING ====================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global ambient_daemon_active
    await websocket.accept()
    active_websockets.append(websocket)

    # Initial state sync
    engine = stack["engine"]
    wm = stack["wm"]
    await websocket.send_json({
        "type": "state_update",
        "state": {
            "tick_id": engine.state.tick_id,
            "entropy": 1.0,
            "temperature": engine.state.current_temperature,
            "blocks": {k: {"value": b.value} for k, b in wm.blocks.items()}
        }
    })

    last_pending_prompt: Optional[str] = None

    try:
        while True:
            raw_text = await websocket.receive_text()
            data = json.loads(raw_text)
            msg_type = data.get("type")

            if msg_type == "user_message":
                user_prompt = data.get("content", "")
                last_pending_prompt = user_prompt
                # Execute Cognitive Tick
                result = await engine.run_cognitive_tick(external_input=user_prompt)

                if result.hold_card:
                    await websocket.send_json({
                        "type": "hold_card",
                        "card": result.hold_card
                    })
                else:
                    # In WebSocket streaming for the web dashboard, the client browser
                    # plays the synthesized speech via the streaming audio endpoint `/api/voice/audio`.
                    # Omitting backend voice_engine.speak() here prevents dual playback
                    # (host sounddevice + browser HTML5 audio colliding simultaneously).
                    await websocket.send_json({
                        "type": "cortex_response",
                        "response": result.user_response,
                        "speak": voice_engine.enabled,
                        "persona": voice_engine.active_persona,
                        "candidates": [
                            {"perspective": c.perspective, "thought_text": c.thought_text, "score": c.score}
                            for c in result.candidates
                        ],
                        "action_result": result.action_result,
                        "state": {
                            "tick_id": engine.state.tick_id,
                            "entropy": result.entropy,
                            "temperature": result.temperature,
                            "blocks": {k: {"value": b.value} for k, b in wm.blocks.items()}
                        }
                    })

            elif msg_type == "hold_decision":
                approved = data.get("approved", False)
                if approved and last_pending_prompt:
                    resumed = await engine.run_cognitive_tick(
                        external_input=last_pending_prompt, human_approval=True
                    )
                    await websocket.send_json({
                        "type": "cortex_response",
                        "response": resumed.user_response,
                        "speak": voice_engine.enabled,
                        "persona": voice_engine.active_persona,
                        "action_result": resumed.action_result,
                        "state": {
                            "tick_id": engine.state.tick_id,
                            "entropy": resumed.entropy,
                            "temperature": resumed.temperature,
                            "blocks": {k: {"value": b.value} for k, b in wm.blocks.items()}
                        }
                    })
                else:
                    await websocket.send_json({
                        "type": "cortex_response",
                        "response": "Action cancelled by human rejection. Workspace remains clean.",
                        "speak": False,
                        "state": {
                            "tick_id": engine.state.tick_id,
                            "blocks": {k: {"value": b.value} for k, b in wm.blocks.items()}
                        }
                    })

            elif msg_type == "toggle_ambient":
                ambient_daemon_active = data.get("active", False)

    except WebSocketDisconnect:
        if websocket in active_websockets:
            active_websockets.remove(websocket)
    except Exception as e:
        import traceback
        traceback.print_exc()
        if websocket in active_websockets:
            active_websockets.remove(websocket)

async def ambient_background_worker():
    """Background task running periodic ambient ticks when toggled on."""
    while True:
        await asyncio.sleep(15)
        if ambient_daemon_active and active_websockets:
            engine = stack["engine"]
            wm = stack["wm"]
            result = await engine.run_cognitive_tick(external_input=None)
            if result.transition == "[RESPONSE]":
                payload = {
                    "type": "ambient_tick",
                    "notice": result.user_response,
                    "state": {
                        "tick_id": engine.state.tick_id,
                        "entropy": result.entropy,
                        "temperature": result.temperature,
                        "blocks": {k: {"value": b.value} for k, b in wm.blocks.items()}
                    }
                }
                for ws in active_websockets:
                    try:
                        await ws.send_json(payload)
                    except Exception:
                        pass

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(ambient_background_worker())

def start_server(host: str = "127.0.0.1", port: int = 8000):
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    start_server()
