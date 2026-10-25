import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Ensure cortex root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cortex.main import build_cortex_stack

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

class MediaControlRequest(BaseModel):
    command: str = "toggle"


HTML_DASHBOARD = """
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
            --bg-card-hover: rgba(18, 28, 51, 0.82);
            --border-panel: rgba(56, 189, 248, 0.22);
            --border-glow: rgba(56, 189, 248, 0.45);
            --border-subtle: rgba(255, 255, 255, 0.08);
            --accent-cyan: #00e5ff;
            --accent-blue: #38bdf8;
            --accent-green: #10b981;
            --accent-yellow: #f59e0b;
            --accent-red: #ef4444;
            --accent-purple: #c084fc;
            --text-main: #f1f5f9;
            --text-dim: #94a3b8;
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
        }

        /* Persistent Ambient Three.js Canvas */
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
            background: rgba(10, 15, 29, 0.85);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border-bottom: 1px solid var(--border-panel);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 24px;
            z-index: 20;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.5);
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 14px;
            font-family: 'Orbitron', 'JetBrains Mono', monospace;
            font-weight: 700;
            font-size: 1.05rem;
            color: var(--accent-cyan);
            letter-spacing: 1px;
            text-shadow: 0 0 12px rgba(0, 229, 255, 0.4);
        }
        .pulse-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: var(--accent-green);
            box-shadow: 0 0 14px var(--accent-green);
            animation: pulse-glow 2s infinite;
        }
        @keyframes pulse-glow {
            0% { transform: scale(0.9); opacity: 0.6; box-shadow: 0 0 8px var(--accent-green); }
            50% { transform: scale(1.15); opacity: 1; box-shadow: 0 0 18px var(--accent-green); }
            100% { transform: scale(0.9); opacity: 0.6; box-shadow: 0 0 8px var(--accent-green); }
        }
        .ticker-bar {
            display: flex;
            align-items: center;
            gap: 12px;
            font-family: 'JetBrains Mono', monospace;
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
            font-family: 'JetBrains Mono', monospace;
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
            font-family: 'JetBrains Mono', monospace;
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
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.78rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-panic:hover { background: rgba(239, 68, 68, 0.35); box-shadow: 0 0 16px rgba(239, 68, 68, 0.4); }

        /* Main Grid Area */
        main {
            flex: 1;
            display: grid;
            grid-template-columns: 270px 1fr;
            overflow: hidden;
            position: relative;
            z-index: 10;
        }

        /* Sidebar Navigation */
        aside.nav-sidebar {
            background: rgba(10, 15, 29, 0.75);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border-right: 1px solid var(--border-panel);
            padding: 20px 16px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            z-index: 15;
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
            gap: 14px;
        }
        .nav-btn .icon { font-size: 1.15rem; transition: transform 0.2s ease; }
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

        /* Content Container */
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

        /* 3D Glass Card Physics Tilt */
        .tilt-card {
            transform-style: preserve-3d;
            perspective: 1000px;
            transition: transform 0.15s ease-out, box-shadow 0.2s ease, border-color 0.2s ease;
            will-change: transform;
        }
        .tilt-card:hover {
            border-color: var(--border-glow);
            box-shadow: 0 16px 36px -8px rgba(0, 229, 255, 0.18), 0 0 14px rgba(56, 189, 248, 0.15);
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
            background: rgba(8, 12, 24, 0.4);
            position: relative;
        }
        .chat-messages {
            flex: 1;
            padding: 28px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 20px;
        }
        .message-bubble {
            max-width: 82%;
            padding: 16px 22px;
            border-radius: 14px;
            line-height: 1.55;
            font-size: 0.96rem;
            animation: fadeIn 0.25s cubic-bezier(0.16, 1, 0.3, 1);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
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
            border: 1px solid rgba(255, 255, 255, 0.15);
            box-shadow: 0 8px 20px rgba(37, 99, 235, 0.3);
        }
        .msg-cortex {
            align-self: flex-start;
            background: rgba(18, 28, 51, 0.85);
            border: 1px solid var(--border-panel);
            color: var(--text-main);
            border-bottom-left-radius: 3px;
        }
        .thought-card {
            margin-top: 12px;
            background: rgba(10, 16, 30, 0.9);
            border-left: 3px solid var(--accent-cyan);
            border-radius: 6px;
            padding: 10px 14px;
            font-size: 0.84rem;
            font-family: 'JetBrains Mono', monospace;
            color: var(--text-dim);
            box-shadow: inset 0 0 12px rgba(0, 0, 0, 0.5);
        }
        .thought-card summary { cursor: pointer; color: var(--accent-cyan); font-weight: 600; outline: none; }
        .hold-card {
            margin-top: 14px;
            background: rgba(239, 68, 68, 0.18);
            border: 1px solid var(--accent-red);
            border-radius: 10px;
            padding: 16px;
            box-shadow: 0 0 20px rgba(239, 68, 68, 0.25);
        }
        .hold-card h4 { color: var(--accent-red); margin-bottom: 8px; font-size: 0.92rem; }
        .hold-actions { display: flex; gap: 12px; margin-top: 14px; }
        .btn-approve {
            background: var(--accent-green);
            color: #fff;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 0 12px rgba(16, 185, 129, 0.4);
        }
        .btn-reject {
            background: var(--accent-red);
            color: #fff;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 0 12px rgba(239, 68, 68, 0.4);
        }
        .chat-input-bar {
            padding: 18px 28px;
            background: rgba(10, 15, 29, 0.92);
            backdrop-filter: blur(16px);
            border-top: 1px solid var(--border-panel);
            display: flex;
            gap: 14px;
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
        }
        .chat-input:focus {
            border-color: var(--accent-cyan);
            box-shadow: 0 0 16px rgba(0, 229, 255, 0.25);
            background: rgba(22, 34, 60, 0.9);
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

        /* Cognitive Stage Sidebar / Inspector */
        aside.state-inspector {
            background: rgba(10, 15, 29, 0.7);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border-left: 1px solid var(--border-panel);
            padding: 22px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 18px;
            z-index: 5;
        }
        .block-card {
            background: var(--bg-card);
            border: 1px solid var(--border-panel);
            border-radius: 10px;
            padding: 14px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
        }
        .block-card h4 {
            font-family: 'JetBrains Mono', monospace;
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
            padding: 30px 40px;
            gap: 26px;
            z-index: 5;
        }
        .pane-scrollable.active { display: flex; }
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
            font-family: 'Orbitron', 'Inter', sans-serif;
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
            font-family: 'JetBrains Mono', monospace;
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
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.98rem;
            font-weight: 700;
            color: var(--accent-cyan);
        }
        .mem-char-badge {
            font-family: 'JetBrains Mono', monospace;
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
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.86rem;
            color: var(--text-main);
            outline: none;
            resize: vertical;
            line-height: 1.45;
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
            height: 420px;
            border-radius: 10px;
            overflow: hidden;
            border: 1px solid var(--border-panel);
            background: radial-gradient(circle at center, #0e172a 0%, #060911 100%);
            box-shadow: inset 0 0 40px rgba(0, 0, 0, 0.8);
        }
        #graph-3d-viewport {
            width: 100%;
            height: 100%;
        }
        #graph-3d-hud {
            position: absolute;
            top: 14px;
            left: 18px;
            pointer-events: none;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.78rem;
            color: var(--accent-cyan);
            background: rgba(10, 15, 29, 0.75);
            padding: 6px 12px;
            border-radius: 6px;
            border: 1px solid var(--border-panel);
        }
        #graph-node-details {
            position: absolute;
            bottom: 14px;
            right: 18px;
            background: rgba(10, 15, 29, 0.88);
            border: 1px solid var(--border-panel);
            padding: 10px 16px;
            border-radius: 8px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.78rem;
            color: #fff;
            display: none;
            backdrop-filter: blur(10px);
            max-width: 300px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
        }
        .filter-tags { display: flex; gap: 8px; }
        .filter-tag {
            background: rgba(18, 28, 51, 0.85);
            border: 1px solid var(--border-panel);
            color: var(--text-dim);
            padding: 5px 12px;
            border-radius: 6px;
            font-size: 0.8rem;
            cursor: pointer;
            font-family: 'JetBrains Mono', monospace;
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
            font-family: 'JetBrains Mono', monospace;
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
            font-family: 'JetBrains Mono', monospace;
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
            font-family: 'JetBrains Mono', monospace;
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
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--accent-cyan);
        }
        .skill-score {
            font-family: 'JetBrains Mono', monospace;
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
            font-family: 'JetBrains Mono', monospace;
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
            font-family: 'JetBrains Mono', monospace;
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
            font-family: 'JetBrains Mono', monospace;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .code-display {
            background: rgba(8, 12, 24, 0.85);
            border: 1px solid var(--border-panel);
            border-radius: 8px;
            padding: 16px;
            font-family: 'JetBrains Mono', monospace;
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
            font-family: 'JetBrains Mono', monospace;
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
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.76rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-restore:hover { background: rgba(239, 68, 68, 0.35); }
    </style>
</head>
<body>
    <!-- Persistent Ambient 3D Three.js Canvas -->
    <canvas id="webgl-bg-canvas"></canvas>

    <header>
        <div class="brand">
            <div class="pulse-dot"></div>
            <span>CORTEX-OS // COGNITIVE RUNTIME</span>
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
            <button class="btn-ambient" id="btn-ambient" onclick="toggleAmbient()">AMBIENT: OFF</button>
            <button class="btn-sleep" onclick="triggerSleep()">DIGITAL SLEEP</button>
            <button class="btn-panic" id="btn-panic" onclick="togglePanicKillswitch()">🚨 PANIC STOP</button>
        </div>
    </header>

    <main>
        <!-- Sidebar Navigation -->
        <aside class="nav-sidebar">
            <button class="nav-btn active" id="tab-stage" onclick="switchTab('stage')">
                <span class="icon">💬</span> Cognitive Stage
            </button>
            <button class="nav-btn" id="tab-memory" onclick="switchTab('memory')">
                <span class="icon">🧠</span> Working Memory
            </button>
            <button class="nav-btn" id="tab-graph" onclick="switchTab('graph')">
                <span class="icon">🕸️</span> Bi-Temporal Graph
            </button>
            <button class="nav-btn" id="tab-skills" onclick="switchTab('skills')">
                <span class="icon">⚡</span> Skill Crystallizer
            </button>
            <button class="nav-btn" id="tab-governance" onclick="switchTab('governance')">
                <span class="icon">🛡️</span> Cedar Governance
            </button>
        </aside>

        <!-- Main Content Area with 5 Interchangeable Views -->
        <div class="content-area">
            
            <!-- PANE 1: COGNITIVE STAGE (Active Interactive Chat + Real-Time Telemetry Inspector) -->
            <div id="pane-stage" class="pane-view active">
                <section class="chat-center">
                    <div class="chat-messages" id="chat-messages">
                        <div class="message-bubble msg-cortex">
                            I am CortexOS, your laptop-resident cognitive operating system. My 4-tier memory substrate, GWA cognitive tick, and autopoietic procedural skill engine are synchronized and ready. How can I assist you?
                        </div>
                    </div>
                    <div class="chat-input-bar">
                        <input type="text" class="chat-input" id="chat-input" placeholder="Give CortexOS a task, instruction, or prompt..." onkeydown="if(event.key==='Enter') sendMessage()">
                        <button class="btn-send" onclick="sendMessage()">Send</button>
                    </div>
                </section>
                <aside class="state-inspector">
                    <!-- 3D Global Workspace Satellite Core Visualizer -->
                    <div id="stage-3d-box" style="height: 150px; position:relative; border-radius:10px; overflow:hidden; background:rgba(6,9,17,0.7); border:1px solid var(--border-panel); box-shadow: inset 0 0 20px rgba(0,0,0,0.8);">
                        <canvas id="stage-3d-canvas" style="width:100%; height:100%;"></canvas>
                        <div style="position:absolute; bottom:6px; left:10px; font-size:0.68rem; color:var(--accent-cyan); font-family:'JetBrains Mono',monospace;">GWA Orbit: 3 Perspectives (Analytic, Pragmatic, Cautious)</div>
                    </div>

                    <h3 style="font-size:0.9rem; letter-spacing:0.5px; text-transform:uppercase; color:var(--accent-cyan); font-family:'JetBrains Mono', monospace;">Working Memory</h3>
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
                    <div style="position: absolute; top: 8px; left: 14px; font-size: 0.76rem; color: var(--accent-cyan); font-family: 'JetBrains Mono', monospace;">3D Holographic Memory Prisms (Character Capacity & Allocation)</div>
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
                    <h3 style="font-size:0.95rem; font-family:'JetBrains Mono', monospace; color:var(--accent-cyan);">➕ Assert New Fact / Relation</h3>
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
                        <h3 style="font-size:0.95rem; font-family:'JetBrains Mono', monospace; color:var(--accent-cyan);">🌐 Interactive 3D WebGL Multi-Graph Universe</h3>
                        <div style="display:flex; gap:10px;">
                            <button class="btn-ambient" onclick="reset3DGraphCamera()" style="font-size:0.75rem; padding:4px 10px;">Reset View</button>
                            <span style="font-size:0.75rem; color:var(--text-dim); font-family:'JetBrains Mono', monospace;">3D Orbit Controls + Photon Laser Beams</span>
                        </div>
                    </div>
                    <div id="graph-3d-container">
                        <div id="graph-3d-viewport"></div>
                        <div id="graph-3d-hud">🖱️ Drag: Rotate 3D | Wheel: Zoom | Right-Click: Pan | Hover/Click: Inspect</div>
                        <div id="graph-node-details"></div>
                    </div>
                    <!-- Hidden legacy 2D canvas preserved for tests and fallback -->
                    <canvas id="graph-canvas" width="800" height="220" style="display:none;"></canvas>
                </div>

                <div class="graph-layout" style="display:grid; grid-template-columns: 1.2fr 0.8fr; gap:24px;">
                    <!-- Graph Relations Table -->
                    <div class="graph-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <h3 style="font-size:0.95rem; font-family:'JetBrains Mono', monospace; color:var(--text-main);">Verified Multi-Graph Relations</h3>
                            <div class="filter-tags">
                                <span class="filter-tag active" onclick="filterGraph('all', this)">ALL</span>
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
                        <h3 style="font-size:0.95rem; font-family:'JetBrains Mono', monospace; color:var(--text-main);">Atomic Engrams (Digital Sleep)</h3>
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
                            <label style="font-size:0.8rem; color:var(--text-dim); font-family:'JetBrains Mono', monospace;">Action to Test:</label>
                            <select class="form-input" id="pdp-action">
                                <option value="file_read">file_read (Somatosensory / Inspect)</option>
                                <option value="git_status">git_status (Read-Only)</option>
                                <option value="get_hardware_telemetry">get_hardware_telemetry (Sensor)</option>
                                <option value="command_run">command_run (Subprocess Command)</option>
                                <option value="git_push_remote">git_push_remote (Irreversible Push)</option>
                                <option value="delete_directory_recursive">delete_directory_recursive (Destructive)</option>
                            </select>
                            <label style="font-size:0.8rem; color:var(--text-dim); font-family:'JetBrains Mono', monospace;">Target Resource Path:</label>
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

        </div>
    </main>

    <script>
        // ==================== WEBSOCKET & CORE ROUTING ====================
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/ws`;
        let socket = new WebSocket(wsUrl);

        socket.onopen = () => { console.log('Connected to CortexOS WebSocket'); };
        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'state_update') {
                updateTelemetry(data.state);
            } else if (data.type === 'cortex_response') {
                renderCortexResponse(data);
                updateTelemetry(data.state);
                trigger3DCognitivePulse(data.state ? data.state.entropy : 1.0);
            } else if (data.type === 'hold_card') {
                renderHoldCard(data);
            } else if (data.type === 'ambient_tick') {
                renderAmbientNotice(data);
                updateTelemetry(data.state);
                trigger3DCognitivePulse(data.state ? data.state.entropy : 1.0);
            }
        };

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
            const tabs = ['stage', 'memory', 'graph', 'skills', 'governance'];
            tabs.forEach(t => {
                const btn = document.getElementById(`tab-${t}`);
                const pane = document.getElementById(`pane-${t}`);
                if (btn) btn.classList.toggle('active', t === tabName);
                if (pane) pane.classList.toggle('active', t === tabName);
            });

            if (tabName === 'memory') loadMemoryPane();
            else if (tabName === 'graph') {
                loadGraphPane();
                setTimeout(onGraphResize, 100);
            }
            else if (tabName === 'skills') loadSkillsPane();
            else if (tabName === 'governance') loadGovernancePane();
        }

        // ==================== 1. THREE.JS PERSISTENT BACKGROUND ====================
        let bgScene, bgCamera, bgRenderer, bgParticles, bgCoreMesh, bgRingMesh, bgGrid;
        let mouseX = 0, mouseY = 0;
        let targetRotX = 0, targetRotY = 0;

        function initBackground3D() {
            const canvas = document.getElementById('webgl-bg-canvas');
            bgScene = new THREE.Scene();
            bgScene.fog = new THREE.FogExp2(0x060911, 0.002);

            bgCamera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 1, 2000);
            bgCamera.position.z = 450;
            bgCamera.position.y = 80;

            bgRenderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
            bgRenderer.setSize(window.innerWidth, window.innerHeight);
            bgRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

            // Perspective Floor Grid
            bgGrid = new THREE.GridHelper(1600, 40, 0x00e5ff, 0x1e293b);
            bgGrid.position.y = -180;
            bgGrid.material.opacity = 0.25;
            bgGrid.material.transparent = true;
            bgScene.add(bgGrid);

            // 600 Synapse Particles
            const particleCount = 600;
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
                size: 3.2,
                transparent: true,
                opacity: 0.65,
                blending: THREE.AdditiveBlending
            });
            bgParticles = new THREE.Points(geom, pMat);
            bgScene.add(bgParticles);

            // Floating Consciousness Core (Upper Right Perspective)
            const coreGroup = new THREE.Group();
            coreGroup.position.set(280, 100, -100);

            // Wireframe Icosahedron
            const icoGeom = new THREE.IcosahedronGeometry(70, 1);
            const icoMat = new THREE.MeshBasicMaterial({
                color: 0x38bdf8,
                wireframe: true,
                transparent: true,
                opacity: 0.35
            });
            bgCoreMesh = new THREE.Mesh(icoGeom, icoMat);
            coreGroup.add(bgCoreMesh);

            // Inner Glowing Sphere
            const innerGeom = new THREE.SphereGeometry(38, 24, 24);
            const innerMat = new THREE.MeshBasicMaterial({
                color: 0x00e5ff,
                wireframe: true,
                transparent: true,
                opacity: 0.55
            });
            const innerCore = new THREE.Mesh(innerGeom, innerMat);
            coreGroup.add(innerCore);

            // Orbiting Accretion Synapse Ring
            const ringGeom = new THREE.RingGeometry(85, 95, 32);
            const ringMat = new THREE.MeshBasicMaterial({
                color: 0xc084fc,
                side: THREE.DoubleSide,
                transparent: true,
                opacity: 0.35,
                wireframe: true
            });
            bgRingMesh = new THREE.Mesh(ringGeom, ringMat);
            bgRingMesh.rotation.x = Math.PI / 2.5;
            coreGroup.add(bgRingMesh);

            bgScene.add(coreGroup);

            window.addEventListener('resize', onWindowResize);
            document.addEventListener('mousemove', onMouseMove);

            animateBackground();
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
        }

        function trigger3DCognitivePulse(entropy) {
            if (!bgCoreMesh) return;
            const baseScale = 1.0;
            const targetScale = 1.35;
            new TWEEN.Tween(bgCoreMesh.scale)
                .to({ x: targetScale, y: targetScale, z: targetScale }, 150)
                .yoyo(true)
                .repeat(1)
                .easing(TWEEN.Easing.Quadratic.Out)
                .start();

            // Color pulse on high entropy
            if (entropy > 1.2 && bgCoreMesh.material) {
                bgCoreMesh.material.color.setHex(0xc084fc);
                setTimeout(() => { if (bgCoreMesh) bgCoreMesh.material.color.setHex(0x38bdf8); }, 800);
            }
        }

        function animateBackground(time) {
            requestAnimationFrame(animateBackground);
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

            // Smooth Parallax
            targetRotX += (mouseX - targetRotX) * 0.04;
            targetRotY += (mouseY - targetRotY) * 0.04;
            bgCamera.position.x = targetRotX * 0.5;
            bgCamera.position.y = 80 - targetRotY * 0.3;
            bgCamera.lookAt(0, 0, 0);

            bgRenderer.render(bgScene, bgCamera);
        }

        // ==================== 2. THREE.JS COGNITIVE STAGE SATELLITES ====================
        let stageScene, stageCamera, stageRenderer;
        let satGroup, satAnalytic, satPragmatic, satCautious;

        function initStage3D() {
            const canvas = document.getElementById('stage-3d-canvas');
            if (!canvas) return;
            const rect = canvas.getBoundingClientRect();
            stageScene = new THREE.Scene();

            stageCamera = new THREE.PerspectiveCamera(50, (rect.width || 340) / (rect.height || 150), 0.1, 1000);
            stageCamera.position.set(0, 20, 110);
            stageCamera.lookAt(0, 0, 0);

            stageRenderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
            stageRenderer.setSize(rect.width || 340, rect.height || 150);

            // Central Core
            const coreGeom = new THREE.SphereGeometry(12, 20, 20);
            const coreMat = new THREE.MeshBasicMaterial({ color: 0x00e5ff, wireframe: true });
            const core = new THREE.Mesh(coreGeom, coreMat);
            stageScene.add(core);

            satGroup = new THREE.Group();
            stageScene.add(satGroup);

            // 3 Satellites: Analytic (Blue), Pragmatic (Green), Cautious (Amber)
            const sGeom = new THREE.SphereGeometry(5, 16, 16);
            satAnalytic = new THREE.Mesh(sGeom, new THREE.MeshBasicMaterial({ color: 0x38bdf8 }));
            satPragmatic = new THREE.Mesh(sGeom, new THREE.MeshBasicMaterial({ color: 0x10b981 }));
            satCautious = new THREE.Mesh(sGeom, new THREE.MeshBasicMaterial({ color: 0xf59e0b }));

            satGroup.add(satAnalytic);
            satGroup.add(satPragmatic);
            satGroup.add(satCautious);

            animateStage3D();
        }

        let satAngle = 0;
        function animateStage3D() {
            requestAnimationFrame(animateStage3D);
            satAngle += 0.025;
            const radius = 42;

            if (satAnalytic) satAnalytic.position.set(radius * Math.cos(satAngle), 8 * Math.sin(satAngle * 2), radius * Math.sin(satAngle));
            if (satPragmatic) satPragmatic.position.set(radius * Math.cos(satAngle + 2.09), 8 * Math.sin((satAngle + 2.09) * 2), radius * Math.sin(satAngle + 2.09));
            if (satCautious) satCautious.position.set(radius * Math.cos(satAngle + 4.18), 8 * Math.sin((satAngle + 4.18) * 2), radius * Math.sin(satAngle + 4.18));

            if (satGroup) satGroup.rotation.y += 0.005;
            if (stageRenderer && stageScene && stageCamera) {
                stageRenderer.render(stageScene, stageCamera);
            }
        }

        // ==================== 3. THREE.JS 3D MULTI-GRAPH UNIVERSE ====================
        let graphScene, graphCamera, graphRenderer, graphControls;
        let graphNodesGroup, graphEdgesGroup;
        let graphRaycaster, graphMouse;
        let graphNodeMeshes = [];
        let currentGraphEdges = [];

        function initGraph3D() {
            const container = document.getElementById('graph-3d-viewport');
            if (!container) return;

            graphScene = new THREE.Scene();
            graphCamera = new THREE.PerspectiveCamera(50, container.clientWidth / container.clientHeight, 1, 3000);
            graphCamera.position.set(0, 120, 360);

            graphRenderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
            graphRenderer.setSize(container.clientWidth, container.clientHeight);
            graphRenderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            container.appendChild(graphRenderer.domElement);

            // OrbitControls
            graphControls = new THREE.OrbitControls(graphCamera, graphRenderer.domElement);
            graphControls.enableDamping = true;
            graphControls.dampingFactor = 0.06;
            graphControls.autoRotate = true;
            graphControls.autoRotateSpeed = 0.6;
            graphControls.maxDistance = 800;
            graphControls.minDistance = 60;

            // Ambient lights
            const ambLight = new THREE.AmbientLight(0xffffff, 0.9);
            graphScene.add(ambLight);

            graphNodesGroup = new THREE.Group();
            graphEdgesGroup = new THREE.Group();
            graphScene.add(graphNodesGroup);
            graphScene.add(graphEdgesGroup);

            // Raycaster
            graphRaycaster = new THREE.Raycaster();
            graphMouse = new THREE.Vector2();

            graphRenderer.domElement.addEventListener('mousemove', onGraphMouseMove);
            graphRenderer.domElement.addEventListener('click', onGraphClick);
            window.addEventListener('resize', onGraphResize);

            animateGraph3D();
        }

        function onGraphResize() {
            const container = document.getElementById('graph-3d-viewport');
            if (!container || !graphCamera || !graphRenderer) return;
            const w = container.clientWidth;
            const h = container.clientHeight;
            if (w === 0 || h === 0) return;
            graphCamera.aspect = w / h;
            graphCamera.updateProjectionMatrix();
            graphRenderer.setSize(w, h);
        }

        function reset3DGraphCamera() {
            if (!graphCamera || !graphControls) return;
            new TWEEN.Tween(graphCamera.position)
                .to({ x: 0, y: 120, z: 360 }, 800)
                .easing(TWEEN.Easing.Cubic.Out)
                .start();
            graphControls.target.set(0, 0, 0);
        }

        function onGraphMouseMove(event) {
            const rect = graphRenderer.domElement.getBoundingClientRect();
            graphMouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
            graphMouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

            graphRaycaster.setFromCamera(graphMouse, graphCamera);
            const intersects = graphRaycaster.intersectObjects(graphNodeMeshes);
            const hud = document.getElementById('graph-node-details');

            if (intersects.length > 0) {
                const nodeData = intersects[0].object.userData;
                hud.style.display = 'block';
                hud.innerHTML = `
                    <div style="font-weight:700; color:var(--accent-cyan); font-size:0.85rem; margin-bottom:2px;">Node: ${escapeHtml(nodeData.id)}</div>
                    <div><b>Layer:</b> <span class="layer-badge layer-${nodeData.layer.toLowerCase()}">${nodeData.layer}</span></div>
                    <div style="margin-top:4px; font-size:0.74rem; color:var(--text-dim);">Click node to focus & filter relations.</div>
                `;
            } else {
                hud.style.display = 'none';
            }
        }

        function onGraphClick(event) {
            const rect = graphRenderer.domElement.getBoundingClientRect();
            graphMouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
            graphMouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

            graphRaycaster.setFromCamera(graphMouse, graphCamera);
            const intersects = graphRaycaster.intersectObjects(graphNodeMeshes);
            if (intersects.length > 0) {
                const targetMesh = intersects[0].object;
                const pos = targetMesh.position;
                new TWEEN.Tween(graphCamera.position)
                    .to({ x: pos.x + 30, y: pos.y + 25, z: pos.z + 70 }, 700)
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
            ctx.fillStyle = 'rgba(10, 15, 29, 0.7)';
            ctx.roundRect ? ctx.roundRect(0, 0, 256, 64, 8) : ctx.fillRect(0, 0, 256, 64);
            ctx.fill();
            ctx.strokeStyle = colorHex || '#00e5ff';
            ctx.lineWidth = 3;
            ctx.stroke();

            ctx.font = 'bold 24px "JetBrains Mono", monospace';
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
            // Also draw to hidden canvas for backwards compatibility
            drawGraphCanvas(edges);

            if (!graphScene) return;

            // Clear old groups
            while (graphNodesGroup.children.length > 0) graphNodesGroup.remove(graphNodesGroup.children[0]);
            while (graphEdgesGroup.children.length > 0) graphEdgesGroup.remove(graphEdgesGroup.children[0]);
            graphNodeMeshes = [];

            if (!edges || edges.length === 0) return;

            // Aggregate unique nodes
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

                // Determine color
                let colHex = 0x00e5ff;
                let cssCol = '#00e5ff';
                if (n.layer === 'causal') { colHex = 0xf59e0b; cssCol = '#f59e0b'; }
                else if (n.layer === 'temporal') { colHex = 0xc084fc; cssCol = '#c084fc'; }
                else if (n.layer === 'entity') { colHex = 0x10b981; cssCol = '#10b981'; }

                // Sphere Node
                const sGeom = new THREE.SphereGeometry(6.5, 24, 24);
                const sMat = new THREE.MeshBasicMaterial({ color: colHex });
                const mesh = new THREE.Mesh(sGeom, sMat);
                mesh.position.set(n.x, n.y, n.z);
                mesh.userData = n;
                graphNodesGroup.add(mesh);
                graphNodeMeshes.push(mesh);

                // Halo ring
                const haloGeom = new THREE.RingGeometry(8, 9.5, 24);
                const haloMat = new THREE.MeshBasicMaterial({ color: colHex, side: THREE.DoubleSide, transparent: true, opacity: 0.6 });
                const halo = new THREE.Mesh(haloGeom, haloMat);
                halo.position.set(n.x, n.y, n.z);
                graphNodesGroup.add(halo);

                // Text Billboard Sprite
                const sprite = makeTextSprite(n.id, cssCol);
                sprite.position.set(n.x, n.y + 14, n.z);
                graphNodesGroup.add(sprite);
            });

            const posLookup = new Map(nodes.map(n => [n.id, n]));

            // Add 3D Edges
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
                if (e.layer === 'causal') colHex = 0xf59e0b;
                else if (e.layer === 'temporal') colHex = 0xc084fc;

                const lineMat = new THREE.LineBasicMaterial({ color: colHex, transparent: true, opacity: 0.5, linewidth: 2 });
                const line = new THREE.Line(lineGeom, lineMat);
                graphEdgesGroup.add(line);
            });
        }

        function animateGraph3D() {
            requestAnimationFrame(animateGraph3D);
            if (graphControls) graphControls.update();
            if (graphRenderer && graphScene && graphCamera) {
                graphRenderer.render(graphScene, graphCamera);
            }
        }

        // ==================== 4. THREE.JS WORKING MEMORY PRISMS ====================
        let memScene, memCamera, memRenderer;
        let memPrisms = [];

        function initMemory3D() {
            const canvas = document.getElementById('memory-3d-canvas');
            if (!canvas) return;
            const rect = canvas.getBoundingClientRect();

            memScene = new THREE.Scene();
            memCamera = new THREE.PerspectiveCamera(45, (rect.width || 600) / (rect.height || 130), 1, 1000);
            memCamera.position.set(0, 35, 120);
            memCamera.lookAt(0, 0, 0);

            memRenderer = new THREE.WebGLRenderer({ canvas: canvas, alpha: true, antialias: true });
            memRenderer.setSize(rect.width || 600, rect.height || 130);

            const grid = new THREE.GridHelper(300, 20, 0x00e5ff, 0x1e293b);
            grid.position.y = -15;
            memScene.add(grid);

            // 4 Floating Holographic Prisms
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

            animateMemory3D();
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

        function animateMemory3D() {
            requestAnimationFrame(animateMemory3D);
            memPrisms.forEach((p, idx) => {
                p.rotation.y += 0.015;
                p.position.y = Math.sin(Date.now() * 0.003 + idx) * 3;
            });
            if (memRenderer && memScene && memCamera) {
                memRenderer.render(memScene, memCamera);
            }
        }

        // ==================== 5. 3D CARD PHYSICS TILT ====================
        function initTiltPhysics() {
            document.querySelectorAll('.tilt-card').forEach(card => {
                card.addEventListener('mousemove', (e) => {
                    const rect = card.getBoundingClientRect();
                    const x = e.clientX - rect.left;
                    const y = e.clientY - rect.top;
                    const centerX = rect.width / 2;
                    const centerY = rect.height / 2;
                    const rotX = ((y - centerY) / centerY) * -8;
                    const rotY = ((x - centerX) / centerX) * 8;
                    card.style.transform = `perspective(1000px) rotateX(${rotX.toFixed(2)}deg) rotateY(${rotY.toFixed(2)}deg) scale3d(1.01, 1.01, 1.01)`;
                });
                card.addEventListener('mouseleave', () => {
                    card.style.transform = `perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)`;
                });
            });
        }

        // ==================== Working Memory Functions ====================
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

        // ==================== Bi-Temporal Graph Functions ====================
        async function loadGraphPane() {
            try {
                const res = await fetch('/api/graph');
                const data = await res.json();
                currentGraphEdges = data.edges || [];
                renderGraphEdges(currentGraphEdges);

                // Render Engrams
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
                const layerClass = `layer-${edge.layer.toLowerCase()}`;
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
                const filtered = currentGraphEdges.filter(e => e.layer.toLowerCase() === layer.toLowerCase());
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

        // ==================== Skill Crystallizer Functions ====================
        async function loadSkillsPane() {
            try {
                const res = await fetch('/api/skills');
                const data = await res.json();

                // Curriculum
                if (data.curriculum_challenge) {
                    document.getElementById('curr-level').innerText = (data.curriculum_challenge.level || 'BEGINNER').toUpperCase();
                    document.getElementById('curr-task').innerText = data.curriculum_challenge.task || '';
                }

                // Grid
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
                            <span style="font-size:0.75rem; color:var(--text-dim); font-family:'JetBrains Mono', monospace;">Sandbox Checkpointed</span>
                        </div>
                        <div class="skill-output-box" id="skill-out-${idx}"></div>
                    </div>
                `).join('');

                initTiltPhysics();
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
            appendMessage(`Activating Tool Generator & Sandbox Refiner loop (max 3 attempts). Creating shadow git checkpoint...`, 'msg-cortex');

            try {
                const res = await fetch('/api/skills/synthesize', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ description: desc })
                });
                const data = await res.json();
                appendMessage(`Skill Synthesis Result:\n${data.stdout || JSON.stringify(data)}`, 'msg-cortex');
            } catch (e) {
                appendMessage(`Synthesis Error: ${e}`, 'msg-cortex');
            }
        }

        // ==================== Cedar Governance Functions ====================
        async function loadGovernancePane() {
            try {
                const res = await fetch('/api/governance');
                const data = await res.json();

                document.getElementById('gov-cedar-path').innerText = data.cedar_path || 'config/policies.cedar';
                document.getElementById('gov-policy-code').innerText = data.policy_code || '# No custom policies configured';
                document.getElementById('gov-working-diff').innerText = data.working_tree_diff || 'Working tree clean.';

                // Checkpoints Table
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

        // ==================== Cognitive Chat Functions ====================
        function sendMessage() {
            const input = document.getElementById('chat-input');
            const text = input.value.trim();
            if (!text) return;
            
            appendMessage(text, 'msg-user');
            input.value = '';

            socket.send(JSON.stringify({ type: 'user_message', content: text }));
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

        function renderCortexResponse(data) {
            const container = document.getElementById('chat-messages');
            const div = document.createElement('div');
            div.className = 'message-bubble msg-cortex';
            div.innerHTML = `<div>${data.response}</div>`;
            
            if (data.candidates && data.candidates.length > 0) {
                const thoughtDetails = document.createElement('details');
                thoughtDetails.className = 'thought-card';
                thoughtDetails.innerHTML = `<summary>[Inner Monologue / 3 Perspectives]</summary>` +
                    data.candidates.map(c => `<div>* <b>${c.perspective}</b>: ${escapeHtml(c.thought_text)} (${c.score > 0 ? '+' : ''}${c.score})</div>`).join('');
                div.appendChild(thoughtDetails);
            }
            if (data.action_result && data.action_result.stdout && (data.action_result.action === 'command_run' || data.action_result.action === 'crystallize_skill')) {
                const outBox = document.createElement('div');
                outBox.style = 'margin-top:8px; font-family:"JetBrains Mono", monospace; font-size:0.8rem; background:rgba(0,0,0,0.4); padding:6px 10px; border-radius:4px; color:#10b981;';
                outBox.innerText = '$ ' + data.action_result.stdout;
                div.appendChild(outBox);
            }

            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
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

        // Initialize 3D Graphics and Tilt Physics on Window Load
        window.addEventListener('DOMContentLoaded', () => {
            initBackground3D();
            initStage3D();
            initGraph3D();
            initMemory3D();
            initTiltPhysics();
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
    return {
        "tick_id": engine.state.tick_id,
        "entropy": 1.0,
        "temperature": engine.state.current_temperature,
        "blocks": {k: {"label": b.label, "value": b.value, "limit": b.char_limit} for k, b in wm.blocks.items()},
        "policy": stack["policy"].cedar_path
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
                    await websocket.send_json({
                        "type": "cortex_response",
                        "response": result.user_response,
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
    except Exception:
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
