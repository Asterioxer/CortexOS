import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
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

HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CortexOS | Autonomous Cognitive Operating System</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;600;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #0a0e17;
            --bg-panel: rgba(16, 23, 38, 0.75);
            --border-panel: rgba(56, 189, 248, 0.2);
            --accent-cyan: #38bdf8;
            --accent-blue: #3b82f6;
            --accent-green: #10b981;
            --accent-yellow: #f59e0b;
            --accent-red: #ef4444;
            --accent-purple: #a855f7;
            --text-main: #f1f5f9;
            --text-dim: #94a3b8;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background: radial-gradient(circle at 15% 15%, #0f172a, #0a0e17 80%);
            color: var(--text-main);
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        header {
            height: 60px;
            background: rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border-panel);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 24px;
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 700;
            font-size: 1.1rem;
            color: var(--accent-cyan);
            letter-spacing: -0.5px;
        }
        .pulse-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--accent-green);
            box-shadow: 0 0 10px var(--accent-green);
            animation: pulse 2s infinite;
        }
        @keyframes pulse { 0% { opacity: 0.5; } 50% { opacity: 1; } 100% { opacity: 0.5; } }
        .ticker-bar {
            display: flex;
            align-items: center;
            gap: 20px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
        }
        .ticker-item {
            display: flex;
            align-items: center;
            gap: 6px;
            background: rgba(30, 41, 59, 0.6);
            padding: 4px 10px;
            border-radius: 6px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
        .ticker-item span.val { color: var(--accent-cyan); font-weight: 600; }
        .btn-ambient {
            background: rgba(56, 189, 248, 0.15);
            border: 1px solid var(--accent-cyan);
            color: var(--accent-cyan);
            padding: 6px 14px;
            border-radius: 6px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-ambient.active {
            background: rgba(16, 185, 129, 0.2);
            border-color: var(--accent-green);
            color: var(--accent-green);
        }
        .btn-sleep {
            background: rgba(168, 85, 247, 0.15);
            border: 1px solid var(--accent-purple);
            color: var(--accent-purple);
            padding: 6px 14px;
            border-radius: 6px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        main {
            flex: 1;
            display: grid;
            grid-template-columns: 260px 1fr 340px;
            overflow: hidden;
        }
        /* Sidebar */
        aside.nav-sidebar {
            background: rgba(15, 23, 42, 0.4);
            border-right: 1px solid var(--border-panel);
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .nav-btn {
            background: transparent;
            border: 1px solid transparent;
            color: var(--text-dim);
            padding: 10px 14px;
            border-radius: 8px;
            text-align: left;
            font-size: 0.9rem;
            cursor: pointer;
            transition: all 0.15s;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .nav-btn:hover, .nav-btn.active {
            background: rgba(56, 189, 248, 0.1);
            color: var(--text-main);
            border-color: rgba(56, 189, 248, 0.2);
        }
        /* Chat Panel */
        section.chat-center {
            display: flex;
            flex-direction: column;
            height: 100%;
            overflow: hidden;
            background: rgba(10, 14, 23, 0.4);
        }
        .chat-messages {
            flex: 1;
            padding: 24px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 18px;
        }
        .message-bubble {
            max-width: 82%;
            padding: 14px 18px;
            border-radius: 12px;
            line-height: 1.5;
            font-size: 0.95rem;
            animation: fadeIn 0.2s ease-in;
        }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
        .msg-user {
            align-self: flex-end;
            background: linear-gradient(135deg, #1e3a8a, #2563eb);
            color: #fff;
            border-bottom-right-radius: 2px;
        }
        .msg-cortex {
            align-self: flex-start;
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid rgba(56, 189, 248, 0.2);
            color: var(--text-main);
            border-bottom-left-radius: 2px;
        }
        .thought-card {
            margin-top: 10px;
            background: rgba(15, 23, 42, 0.85);
            border-left: 3px solid var(--accent-cyan);
            border-radius: 4px;
            padding: 8px 12px;
            font-size: 0.82rem;
            font-family: 'JetBrains Mono', monospace;
            color: var(--text-dim);
        }
        .thought-card summary { cursor: pointer; color: var(--accent-cyan); font-weight: 600; outline: none; }
        .hold-card {
            margin-top: 12px;
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid var(--accent-red);
            border-radius: 8px;
            padding: 14px;
        }
        .hold-card h4 { color: var(--accent-red); margin-bottom: 6px; font-size: 0.9rem; }
        .hold-actions { display: flex; gap: 10px; margin-top: 12px; }
        .btn-approve {
            background: var(--accent-green);
            color: #fff;
            border: none;
            padding: 6px 14px;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
        }
        .btn-reject {
            background: var(--accent-red);
            color: #fff;
            border: none;
            padding: 6px 14px;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
        }
        .chat-input-bar {
            padding: 16px 24px;
            background: rgba(15, 23, 42, 0.9);
            border-top: 1px solid var(--border-panel);
            display: flex;
            gap: 12px;
        }
        .chat-input {
            flex: 1;
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: #fff;
            padding: 12px 18px;
            border-radius: 8px;
            font-size: 0.95rem;
            outline: none;
            transition: all 0.2s;
        }
        .chat-input:focus { border-color: var(--accent-cyan); box-shadow: 0 0 10px rgba(56, 189, 248, 0.2); }
        .btn-send {
            background: var(--accent-blue);
            color: #fff;
            border: none;
            padding: 0 24px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.15s;
        }
        .btn-send:hover { background: #1d4ed8; }
        /* Right Inspector Panel */
        aside.state-inspector {
            background: rgba(15, 23, 42, 0.5);
            border-left: 1px solid var(--border-panel);
            padding: 20px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 18px;
        }
        .block-card {
            background: rgba(30, 41, 59, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 12px;
        }
        .block-card h4 {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            color: var(--accent-purple);
            text-transform: uppercase;
            margin-bottom: 6px;
            display: flex;
            justify-content: space-between;
        }
        .block-card p {
            font-size: 0.82rem;
            color: var(--text-dim);
            line-height: 1.4;
            max-height: 120px;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <header>
        <div class="brand">
            <div class="pulse-dot"></div>
            <span>CORTEX-OS // RUNTIME</span>
        </div>
        <div class="ticker-bar">
            <div class="ticker-item">TICK <span class="val" id="tick-id">#0</span></div>
            <div class="ticker-item">H(W) <span class="val" id="entropy-val">1.00</span></div>
            <div class="ticker-item">TEMP <span class="val" id="temp-val">0.40</span></div>
            <div class="ticker-item">UQ <span class="val" id="uq-val" style="color:var(--accent-green)">PASS</span></div>
            <button class="btn-ambient" id="btn-ambient" onclick="toggleAmbient()">AMBIENT: OFF</button>
            <button class="btn-sleep" onclick="triggerSleep()">DIGITAL SLEEP</button>
        </div>
    </header>
    <main>
        <aside class="nav-sidebar">
            <button class="nav-btn active">Cognitive Stage</button>
            <button class="nav-btn" onclick="showMemoryModal()">Working Memory</button>
            <button class="nav-btn" onclick="showGraphModal()">Bi-Temporal Graph</button>
            <button class="nav-btn" onclick="showSkillsModal()">Skill Crystallizer</button>
            <button class="nav-btn" onclick="showGovernanceModal()">Cedar Governance</button>
        </aside>
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
            <h3 style="font-size:0.9rem; letter-spacing:0.5px; text-transform:uppercase; color:var(--accent-cyan); font-family:'JetBrains Mono', monospace;">Working Memory</h3>
            <div class="block-card">
                <h4>persona_self</h4>
                <p id="block-persona">Autonomous cognitive OS embodied on this laptop.</p>
            </div>
            <div class="block-card">
                <h4>workspace_state</h4>
                <p id="block-workspace">Active repository root monitored.</p>
            </div>
            <div class="block-card">
                <h4>scratchpad_stm</h4>
                <p id="block-scratchpad">Awaiting prompt.</p>
            </div>
        </aside>
    </main>

    <script>
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
            } else if (data.type === 'hold_card') {
                renderHoldCard(data);
            } else if (data.type === 'ambient_tick') {
                renderAmbientNotice(data);
                updateTelemetry(data.state);
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
        }

        function sendMessage() {
            const input = document.getElementById('chat-input');
            const text = input.value.trim();
            if (!text) return;
            
            // Append user bubble
            appendMessage(text, 'msg-user');
            input.value = '';

            // Send via WS
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
                    data.candidates.map(c => `<div>* <b>${c.perspective}</b>: ${c.thought_text} (${c.score > 0 ? '+' : ''}${c.score})</div>`).join('');
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
            div.style = 'font-size:0.8rem; color:#94a3b8; font-style:italic; padding:4px 12px; background:rgba(56,189,248,0.05); border-left:2px solid #38bdf8; border-radius:2px;';
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

        function showMemoryModal() { alert('Letta Working Memory: 4 character-bounded self-editing in-context blocks active and synchronized.'); }
        function showGraphModal() { alert('Bi-Temporal Knowledge Graph: 4 MAGMA layers (Semantic, Temporal, Causal, Entity) active.'); }
        function showSkillsModal() { alert('Autopoietic Skill Engine: FRIDAY/Voyager synthesis with sandbox and ATLAS pamphlets.'); }
        function showGovernanceModal() { alert('Cedar Policy Gate: Sub-millisecond decision point enforcing ALLOW, ESCALATE, DENY.'); }
    </script>
</body>
</html>
"""

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

@app.post("/api/sleep")
async def trigger_sleep():
    report = await stack["sleep"].run_consolidation_cycle()
    return {"status": "SUCCESS", "report": report.__dict__}

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
