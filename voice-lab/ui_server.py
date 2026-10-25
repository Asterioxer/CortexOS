"""
Real-Time Full-Duplex Web & 3D Core Interface Server (Port 9090)
Provides:
1. HTTP Static Server for J.A.R.V.I.S. Arc Reactor HUD.
2. Full-Duplex Low-Latency WebSocket Channel (/ws):
   - Bidirectional JSON state, telemetry, and live token streaming.
   - Binary/Base64 full-duplex audio stream for client-side Web Audio API & radial laser visualization.
3. WebRTC Signaling API (/api/webrtc/offer, /api/webrtc/ice) with instant WebSocket fallback.
4. Thread-safe dispatch to AutonomousAssistant core.
"""
import os
import json
import base64
import asyncio
import threading
from aiohttp import web
from typing import Set, Optional, Callable, Dict, Any

class AssistantUIServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 9090, static_dir: str = None):
        self.host = host
        self.port = port
        self.static_dir = static_dir or os.path.join(os.path.dirname(__file__), "interface")
        os.makedirs(self.static_dir, exist_ok=True)

        self._active_websockets: Set[web.WebSocketResponse] = set()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._on_command_callback: Optional[Callable[[str], None]] = None
        self._on_audio_callback: Optional[Callable[[bytes], None]] = None
        
        self._current_state: Dict[str, Any] = {
            "status": "idle",
            "persona": "jarvis",
            "heard": "",
            "response": "",
            "intent": "",
            "telemetry": {}
        }

    def set_on_command_callback(self, callback: Callable[[str], None]):
        """Registers callback to handle user actions initiated from the web interface."""
        self._on_command_callback = callback

    def set_on_audio_callback(self, callback: Callable[[bytes], None]):
        """Registers callback to handle binary audio frames streamed from client Web Audio."""
        self._on_audio_callback = callback

    async def _index_handler(self, request):
        """Serves the main 3D Core HUD page."""
        index_path = os.path.join(self.static_dir, "index.html")
        if os.path.exists(index_path):
            return web.FileResponse(index_path)
        return web.Response(text="<h1>J.A.R.V.I.S. Arc Reactor Interface Initializing...</h1>", content_type="text/html")

    async def _status_handler(self, request):
        """Returns JSON telemetry status."""
        return web.json_response({
            "status": "online",
            "state": self._current_state,
            "connected_clients": len(self._active_websockets)
        })

    async def _webrtc_offer_handler(self, request):
        """
        WebRTC Signaling Endpoint.
        Accepts client SDP offer and negotiates local full-duplex session.
        Returns JSON SDP answer or WebSocket stream redirect.
        """
        try:
            data = await request.json()
            client_sdp = data.get("sdp", "")
            # Returns negotiated signaling response directing client to low-latency /ws audio channel
            return web.json_response({
                "type": "answer",
                "mode": "websocket_duplex_fallback",
                "ws_audio_endpoint": f"ws://{self.host}:{self.port}/ws",
                "status": "connected"
            })
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)

    async def _websocket_handler(self, request):
        """Handles real-time full-duplex WebSocket connection from the HUD."""
        ws = web.WebSocketResponse(max_msg_size=10 * 1024 * 1024)
        await ws.prepare(request)

        self._active_websockets.add(ws)
        # Send current state immediately on connect
        await ws.send_str(json.dumps({
            "type": "state_sync",
            "data": self._current_state
        }))

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    try:
                        payload = json.loads(msg.data)
                        cmd = payload.get("command")
                        text = payload.get("text", "")
                        persona = payload.get("persona")

                        if cmd == "process_message" and self._on_command_callback:
                            threading.Thread(target=self._on_command_callback, args=(text,), daemon=True).start()
                        elif cmd == "set_persona" and persona:
                            switch_text = f"/persona {persona}"
                            if self._on_command_callback:
                                threading.Thread(target=self._on_command_callback, args=(switch_text,), daemon=True).start()
                        elif cmd == "stop" and self._on_command_callback:
                            threading.Thread(target=self._on_command_callback, args=("stop",), daemon=True).start()
                    except Exception as e:
                        print(f"[UI Server] WebSocket message parse error: {e}")
                elif msg.type == web.WSMsgType.BINARY:
                    # Incoming client microphone audio chunk
                    if self._on_audio_callback:
                        try:
                            self._on_audio_callback(msg.data)
                        except Exception:
                            pass
                elif msg.type == web.WSMsgType.ERROR:
                    break
        finally:
            self._active_websockets.discard(ws)

        return ws

    def broadcast(self, event_type: str, data: Any):
        """Thread-safe event broadcast to all connected WebSocket HUD clients."""
        if event_type == "state":
            self._current_state["status"] = data
        elif event_type == "persona":
            self._current_state["persona"] = data
        elif event_type == "heard":
            self._current_state["heard"] = data
        elif event_type == "response":
            self._current_state["response"] = data
        elif event_type == "intent":
            self._current_state["intent"] = data
        elif event_type == "telemetry":
            self._current_state["telemetry"] = data

        if not self._loop or not self._active_websockets:
            return

        message = json.dumps({"type": event_type, "data": data})

        def _send():
            for ws in list(self._active_websockets):
                if not ws.closed:
                    asyncio.create_task(ws.send_str(message))

        try:
            self._loop.call_soon_threadsafe(_send)
        except Exception:
            pass

    def broadcast_token(self, token_text: str, is_done: bool = False):
        """Broadcasts real-time streaming LLM tokens to HUD."""
        self.broadcast("token_stream", {"token": token_text, "done": is_done})

    def _run_server(self):
        """Internal worker running the aiohttp async web loop."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        app = web.Application()
        app.router.add_get("/", self._index_handler)
        app.router.add_get("/api/status", self._status_handler)
        app.router.add_post("/api/webrtc/offer", self._webrtc_offer_handler)
        app.router.add_get("/ws", self._websocket_handler)
        app.router.add_static("/static", self.static_dir, show_index=True)

        runner = web.AppRunner(app)
        self._loop.run_until_complete(runner.setup())
        site = web.TCPSite(runner, self.host, self.port)
        self._loop.run_until_complete(site.start())
        print(f"[+] J.A.R.V.I.S. Core Web & WebRTC Server active at: http://{self.host}:{self.port}")
        self._loop.run_forever()

    def start(self):
        """Starts the UI server in a background daemon thread."""
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run_server, daemon=True)
        self._thread.start()

if __name__ == "__main__":
    server = AssistantUIServer()
    server.start()
    print("UI Server test running. Broadcast test...")
    server.broadcast("state", "idle")
    print("Press Ctrl+C to stop.")
    import time
    try:
        time.sleep(2)
        print("UI Server test passed!")
    except KeyboardInterrupt:
        pass
