"""
Autonomous Laptop Startup & Session Unlock Greeting Sentinel (Phase 3)
Features:
- Native Windows Session Unlock Listener via WTSRegisterSessionNotification (0% CPU polling).
- Time-of-Day Aware Greeting ("Good morning/afternoon/evening, Soham").
- Executive Briefing Engine:
  - Exact 12-hour local time.
  - Live battery health & AC power telemetry.
  - Top prioritized headline from live news.
  - Intelligent cooldown protection (prevents redundant greetings on rapid lock/unlock).
- Direct trigger support for startup and voice command "/briefing".
"""
import time
import threading
import ctypes
import psutil
import urllib.request
import xml.etree.ElementTree as ET
import win32gui
import win32con
from typing import Callable, Optional

# Windows WTS Notification Constants
NOTIFY_FOR_THIS_SESSION = 0
WM_WTSSESSION_CHANGE = 0x02B1
WTS_SESSION_LOCK = 0x7
WTS_SESSION_UNLOCK = 0x8

class ExecutiveBriefing:
    def __init__(self, username: str = "Soham"):
        self.username = username

    def get_time_greeting(self) -> str:
        """Determines time-of-day greeting."""
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
        """Retrieves spoken battery telemetry."""
        try:
            bat = psutil.sensors_battery()
            if not bat:
                return ""
            plugged = "plugged into AC power" if bat.power_plugged else "running on battery"
            return f"Battery is at {bat.percent} percent, {plugged}."
        except Exception:
            return ""

    def get_top_headline(self) -> str:
        """Fetches the #1 top news headline for the briefing."""
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
        """Compiles the full executive briefing text."""
        greeting = self.get_time_greeting()
        time_str = time.strftime("%I:%M %p").lstrip("0")
        bat_str = self.get_battery_status()
        headline = self.get_top_headline()

        parts = [greeting, f"The time is {time_str}."]
        if bat_str:
            parts.append(bat_str)
        if headline:
            parts.append(f"In top news: {headline}.")
        parts.append("All systems are online and standing by.")

        return " ".join(parts)

class SessionUnlockSentinel:
    def __init__(
        self,
        on_unlock_callback: Callable[[str], None],
        username: str = "Soham",
        cooldown_seconds: float = 180.0
    ):
        self.on_unlock_callback = on_unlock_callback
        self.briefing = ExecutiveBriefing(username=username)
        self.cooldown_seconds = cooldown_seconds
        
        self.last_unlock_time = 0.0
        self.is_running = False
        self.hwnd = None
        self.thread: Optional[threading.Thread] = None

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        """Processes Windows messages for session unlock events."""
        if msg == WM_WTSSESSION_CHANGE:
            if wparam == WTS_SESSION_UNLOCK:
                now = time.time()
                if now - self.last_unlock_time > self.cooldown_seconds:
                    self.last_unlock_time = now
                    print("\n[⚡ Session Sentinel] Windows Unlock detected! Delivering Executive Briefing...")
                    text = self.briefing.generate()
                    if self.on_unlock_callback:
                        self.on_unlock_callback(text)
                else:
                    print("\n[Session Sentinel] Unlock detected (cooldown active, skipping repeat greeting).")
            elif wparam == WTS_SESSION_LOCK:
                print("\n[Session Sentinel] Windows Session Locked.")

        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def _listen_loop(self):
        """Runs the native Windows message pump in a background thread."""
        class_name = f"SessionSentinelClass_{int(time.time())}_{threading.get_ident()}"

        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self._wnd_proc
        wc.lpszClassName = class_name
        
        try:
            atom = win32gui.RegisterClass(wc)
        except Exception as e:
            print(f"[!] Sentinel class registration error: {e}")
            return

        self.hwnd = win32gui.CreateWindow(
            atom,
            "SessionSentinelWindow",
            0, 0, 0, 0, 0,
            win32con.HWND_MESSAGE, # Message-only window
            0, 0, None
        )

        # Register for Windows Session Notifications
        registered = ctypes.windll.wtsapi32.WTSRegisterSessionNotification(self.hwnd, NOTIFY_FOR_THIS_SESSION)
        if registered:
            print("[+] Session Sentinel registered for Windows Unlock events (0% CPU polling).")
        else:
            print("[!] Warning: Could not register WTSRegisterSessionNotification.")

        # Windows Message Pump
        while self.is_running:
            win32gui.PumpWaitingMessages()
            time.sleep(0.1)

        # Cleanup
        try:
            ctypes.windll.wtsapi32.WTSUnRegisterSessionNotification(self.hwnd)
            win32gui.DestroyWindow(self.hwnd)
            win32gui.UnregisterClass(atom, None)
        except Exception:
            pass

    def start(self):
        """Starts the sentinel background listener."""
        self.is_running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()

    def stop(self):
        """Stops the sentinel listener."""
        self.is_running = False
        if self.hwnd:
            ctypes.windll.user32.PostMessageW(self.hwnd, 0x0012, 0, 0) # WM_QUIT

    def trigger_briefing_now(self) -> str:
        """Generates and delivers the executive briefing immediately."""
        text = self.briefing.generate()
        if self.on_unlock_callback:
            self.on_unlock_callback(text)
        return text

if __name__ == "__main__":
    print("Testing Executive Briefing Generation:")
    b = ExecutiveBriefing("Soham")
    print(b.generate())
