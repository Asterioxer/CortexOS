"""
CortexOS Autonomous Laptop Startup & Session Unlock Greeting Sentinel.
Absorbed and modernized from Voice Lab.

Provides:
- Native Windows Session Unlock Listener via WTSRegisterSessionNotification (0% CPU message pump).
- Time-of-Day Aware Executive Greeting ("Good morning/afternoon/evening, Soham").
- Spoken Telemetry: Local 12-hour time, battery health & AC power posture, and top news headline.
- Anti-redundancy cooldown guard for rapid lock/unlock cycles.
"""

import time
import threading
import ctypes
import psutil
import urllib.request
import xml.etree.ElementTree as ET
from typing import Callable, Optional

# Windows WTS Notification Constants
NOTIFY_FOR_THIS_SESSION = 0
WM_WTSSESSION_CHANGE = 0x02B1
WTS_SESSION_LOCK = 0x7
WTS_SESSION_UNLOCK = 0x8


class ExecutiveBriefing:
    """Generates an executive briefing tailored for Soham's laptop."""
    def __init__(self, username: str = "Soham"):
        self.username = username

    def get_time_greeting(self) -> str:
        hour = time.localtime().tm_hour
        if 5 <= hour < 12:
            return f"Good morning, {self.username}."
        elif 12 <= hour < 17:
            return f"Good afternoon, {self.username}."
        elif 17 <= hour < 22:
            return f"Good evening, {self.username}."
        else:
            return f"Welcome back, {self.username}."

    def get_battery_status(self) -> str:
        try:
            bat = psutil.sensors_battery()
            if not bat:
                return ""
            plugged = "plugged into AC power" if bat.power_plugged else "running on battery"
            return f"Battery is at {int(bat.percent)} percent, {plugged}."
        except Exception:
            return ""

    def get_top_headline(self) -> str:
        """Fetches the #1 top news headline from RSS."""
        url = "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                root = ET.fromstring(resp.read())
                first_item = root.find(".//item/title")
                if first_item is not None and first_item.text:
                    clean = first_item.text.split(" - ")[0].strip()
                    return clean
        except Exception:
            pass
        return ""

    def generate(self) -> str:
        """Compiles the full spoken executive briefing text."""
        greeting = self.get_time_greeting()
        time_str = time.strftime("%I:%M %p").lstrip("0")
        bat_str = self.get_battery_status()
        headline = self.get_top_headline()

        parts = [greeting, f"The time is {time_str}."]
        if bat_str:
            parts.append(bat_str)
        if headline:
            parts.append(f"In top news: {headline}.")
        parts.append("All CortexOS neural substrates are online and standing by.")

        return " ".join(parts)


class SessionUnlockSentinel:
    """Native Windows message pump listening for desktop session unlocks with 0% CPU polling."""
    def __init__(
        self,
        on_unlock_callback: Optional[Callable[[str], None]] = None,
        username: str = "Soham",
        cooldown_seconds: float = 120.0
    ):
        self.on_unlock_callback = on_unlock_callback
        self.briefing = ExecutiveBriefing(username=username)
        self.cooldown_seconds = cooldown_seconds

        self.last_unlock_time = 0.0
        self.is_running = False
        self.hwnd = None
        self.thread: Optional[threading.Thread] = None

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == WM_WTSSESSION_CHANGE:
            if wparam == WTS_SESSION_UNLOCK:
                now = time.time()
                if now - self.last_unlock_time > self.cooldown_seconds:
                    self.last_unlock_time = now
                    briefing_text = self.briefing.generate()
                    if self.on_unlock_callback:
                        self.on_unlock_callback(briefing_text)
            elif wparam == WTS_SESSION_LOCK:
                pass

        try:
            import win32gui
            return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
        except Exception:
            return 0

    def _listen_loop(self):
        try:
            import win32gui
            import win32con
        except ImportError:
            return

        class_name = f"CortexSessionSentinel_{int(time.time())}_{threading.get_ident()}"
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self._wnd_proc
        wc.lpszClassName = class_name

        try:
            atom = win32gui.RegisterClass(wc)
        except Exception:
            return

        self.hwnd = win32gui.CreateWindow(
            atom,
            "CortexSessionSentinelWindow",
            0, 0, 0, 0, 0,
            win32con.HWND_MESSAGE,
            0, 0, None
        )

        try:
            registered = ctypes.windll.wtsapi32.WTSRegisterSessionNotification(self.hwnd, NOTIFY_FOR_THIS_SESSION)
        except Exception:
            registered = False

        while self.is_running:
            try:
                win32gui.PumpWaitingMessages()
            except Exception:
                pass
            time.sleep(0.1)

        try:
            ctypes.windll.wtsapi32.WTSUnRegisterSessionNotification(self.hwnd)
            win32gui.DestroyWindow(self.hwnd)
            win32gui.UnregisterClass(atom, None)
        except Exception:
            pass

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False
        if self.hwnd:
            try:
                ctypes.windll.user32.PostMessageW(self.hwnd, 0x0012, 0, 0)  # WM_QUIT
            except Exception:
                pass

    def trigger_briefing_now(self) -> str:
        text = self.briefing.generate()
        if self.on_unlock_callback:
            self.on_unlock_callback(text)
        return text
