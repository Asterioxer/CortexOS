"""
J.A.R.V.I.S. Autonomous AI Desktop Launcher (Stark Industries Edition)
Features:
1. Launches the Hardware-Accelerated J.A.R.V.I.S. Arc Reactor HUD directly on your desktop screen.
2. Zero Browser Chrome: Standalone native app mode window (no address bar, no tabs, no lag).
3. 60 FPS GPU-accelerated CSS Arc Reactor + 48-channel Radial Laser Voice Equalizer.
4. Ultra-natural conversational neural voices: J.A.R.V.I.S. (Brian), FRIDAY (Ava), EDITH (Emma).
5. Real-time bidirectional WebSocket link to the autonomous voice & system controller backend.
"""
import os
import sys
import time
import subprocess
import threading
import win32gui
import win32con
import win32event
import win32api
import winerror

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from voice_assistant import AutonomousAssistant

EDGE_EXE_PATHS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe")
]

def find_edge_path():
    for p in EDGE_EXE_PATHS:
        if os.path.exists(p):
            return p
    return "msedge.exe"

class JarvisDesktopApp:
    def __init__(self):
        print("=" * 65)
        print("🤖 J.A.R.V.I.S. // STARK-OS AI ASSISTANT (MARK XLII)")
        print("=" * 65)

        # Single-instance lock to prevent duplicate assistant instances
        self._mutex = win32event.CreateMutex(None, False, "Global\\StarkJarvisAssistantMutex")
        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
            print("[!] J.A.R.V.I.S. is already active on this system.")
            print("[*] Focusing existing J.A.R.V.I.S. Arc Reactor HUD...")
            self.bring_to_front()
            time.sleep(0.5)
            sys.exit(0)
        
        # 1. Initialize Autonomous Voice & Agentic Assistant
        print("[*] Initializing Autonomous Assistant Engine & Layer 2 Voice Listener...")
        self.assistant = AutonomousAssistant(
            tool_model="qwen2.5:3b",
            chat_model="dolphinlabs/llama3.2-3b-uncensored:latest",
            reasoning_model="nandhank/qwen3.5-abliterated-truthful:9b",
            default_profile="voice",
            voice_input_enabled=True,
            voice_output_enabled=True
        )

        # Hook unlock event
        self.assistant.sentinel.on_unlock_callback = self._on_unlock_event

        # 2. Launch Native Hardware-Accelerated HUD Window
        self.hud_process = None
        self._launch_hud_window()

        # 3. Deliver initial startup greeting in J.A.R.V.I.S. voice
        def _startup_greet():
            time.sleep(1.2) # Allow HUD window to connect to WebSocket
            time_greet = self.assistant.sentinel.briefing.get_time_greeting()
            startup_msg = f"{time_greet} J.A.R.V.I.S. is online. All diagnostic checks are green. How may I assist you?"
            if hasattr(self.assistant, "ui_server") and self.assistant.ui_server:
                self.assistant.ui_server.broadcast("response", startup_msg)
                self.assistant.ui_server.broadcast("state", "speaking")
            self.assistant.speak(startup_msg)
            self.assistant.wait_until_done_speaking(timeout=10.0)
            if hasattr(self.assistant, "ui_server") and self.assistant.ui_server:
                self.assistant.ui_server.broadcast("state", "idle")

        threading.Thread(target=_startup_greet, daemon=True).start()

    def _launch_hud_window(self):
        edge_path = find_edge_path()
        url = "http://127.0.0.1:9090"
        edge_data_dir = os.path.join(os.path.dirname(__file__), "sandbox", "edge_hud_profile")
        os.makedirs(edge_data_dir, exist_ok=True)
        
        # App mode parameters: standalone window, fixed size, positioned on right side of screen
        cmd = [
            edge_path,
            f"--app={url}",
            f"--user-data-dir={edge_data_dir}",
            "--window-size=500,780",
            "--window-position=960,80",
            "--no-first-run",
            "--no-default-browser-check"
        ]
        print(f"[+] Launching Hardware-Accelerated J.A.R.V.I.S. Arc Reactor HUD via:\n    {edge_path}")
        try:
            self.hud_process = subprocess.Popen(cmd)
        except Exception as e:
            print(f"[!] Warning launching Edge App window: {e}")

    def _on_unlock_event(self, briefing_text: str):
        """Called by Windows Session Unlock Sentinel when laptop is opened/unlocked."""
        print(f"\n[Session Unlock Detected] Bringing J.A.R.V.I.S. to foreground...")
        self.bring_to_front()
        if hasattr(self.assistant, "ui_server") and self.assistant.ui_server:
            self.assistant.ui_server.broadcast("response", briefing_text)
            self.assistant.ui_server.broadcast("state", "speaking")
        self.assistant.speak(briefing_text)
        self.assistant.wait_until_done_speaking(timeout=15.0)
        if hasattr(self.assistant, "ui_server") and self.assistant.ui_server:
            self.assistant.ui_server.broadcast("state", "idle")

    def bring_to_front(self):
        """Finds J.A.R.V.I.S. window and brings it to top of all open apps."""
        try:
            def enum_windows_cb(hwnd, extra):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if "J.A.R.V.I.S." in title or "STARK-OS" in title:
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                        win32gui.SetForegroundWindow(hwnd)
                return True
            win32gui.EnumWindows(enum_windows_cb, None)
        except Exception:
            pass

    def run(self):
        """Starts assistant listener and maintains process loop."""
        if self.assistant.listener:
            self.assistant.listener.start()

        print("\n========================================================")
        print("  J.A.R.V.I.S. Interface is active on your screen!")
        print("  - Speak naturally anytime (No Win+H needed)")
        print("  - Say 'Stop' or speak over J.A.R.V.I.S. to interrupt")
        print("  - Close the HUD window or press Ctrl+C here to stop")
        print("========================================================\n")

        try:
            while True:
                time.sleep(0.5)
                # If HUD window was closed by the user, shutdown assistant
                if self.hud_process and self.hud_process.poll() is not None:
                    print("\n[HUD window closed by user. Shutting down assistant...]")
                    break
        except KeyboardInterrupt:
            print("\nShutting down J.A.R.V.I.S....")
        finally:
            if self.assistant:
                self.assistant.stop_speaking()
                if self.assistant.listener:
                    self.assistant.listener.stop()
                if hasattr(self.assistant, "sentinel") and self.assistant.sentinel:
                    self.assistant.sentinel.stop()
            if self.hud_process:
                try:
                    self.hud_process.terminate()
                except Exception:
                    pass
            print("J.A.R.V.I.S. offline. Goodbye.")

if __name__ == "__main__":
    app = JarvisDesktopApp()
    app.run()
