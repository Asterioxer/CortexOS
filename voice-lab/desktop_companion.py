"""
Autonomous Windows Voice & Agentic Assistant v3.5 - Native Desktop Companion HUD
Direct Native System Integration:
1. Pure native Windows desktop GUI application (zero web browser required).
2. Procedural 3D Quantum Core Hologram canvas (60 FPS, particle sphere & rotating gimbals).
3. Automatically opens on screen at laptop startup and brings itself to the front upon Windows unlock.
4. Greets user out loud ("Good morning Soham! All systems are online...") and starts conversational loop.
5. Interactive multi-persona switcher (Christopher, Jenny, Aria, Guy, Neerja).
6. Multi-modal input: speak naturally anytime or type commands into the quick entry box.
7. Instant sub-10ms hardware barge-in interruption.
"""
import os
import sys
import time
import math
import queue
import threading
import tkinter as tk
from tkinter import ttk
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

# -----------------------------------------------------------------------------
# Color Palette & Visual Themes (JARVIS Arc Reactor Holographic Palette)
# -----------------------------------------------------------------------------
BG_COLOR = "#040810"        # Stark Obsidian
PANEL_BG = "#08101e"        # Holographic deep slate
BORDER_COLOR = "#0c2842"    # High-tech cyan border
TEXT_MAIN = "#f8fafc"       # Crisp white
TEXT_MUTED = "#64748b"      # Sleek steel gray
CYAN_ACCENT = "#00f0ff"     # Iconic JARVIS cyan
GOLD_ACCENT = "#fbbf24"     # Stark Mark gold
EMERALD_ACCENT = "#10b981"  # Active mic emerald
PURPLE_ACCENT = "#c084fc"   # Reasoning purple
AMBER_ACCENT = "#f59e0b"    # Tactical amber
RED_ACCENT = "#ef4444"      # Lockdown red
SKY_ACCENT = "#38bdf8"      # Transmission sky blue

STATE_CONFIGS = {
    "idle": {
        "label": "STANDBY",
        "primary": CYAN_ACCENT,
        "glow": "#012a42",
        "speed": 0.015,
        "badge_bg": "#082f49",
        "badge_fg": CYAN_ACCENT
    },
    "listening": {
        "label": "🎙️ AUDIO CAPTURE",
        "primary": EMERALD_ACCENT,
        "glow": "#043c2c",
        "speed": 0.035,
        "badge_bg": "#022c22",
        "badge_fg": EMERALD_ACCENT
    },
    "thinking": {
        "label": "🧠 COGNITIVE MATRIX",
        "primary": PURPLE_ACCENT,
        "glow": "#451268",
        "speed": 0.065,
        "badge_bg": "#3b0764",
        "badge_fg": PURPLE_ACCENT
    },
    "speaking": {
        "label": "🗣️ AUDIO TRANSMISSION",
        "primary": SKY_ACCENT,
        "glow": "#083e60",
        "speed": 0.030,
        "badge_bg": "#082f49",
        "badge_fg": SKY_ACCENT
    },
    "barge_in": {
        "label": "🛑 LOCKDOWN CUTOFF",
        "primary": RED_ACCENT,
        "glow": "#5c0e0e",
        "speed": 0.005,
        "badge_bg": "#450a0a",
        "badge_fg": RED_ACCENT
    }
}

class DesktopCompanionHUD:
    def __init__(self, start_assistant_core: bool = True):
        # Single-instance enforcement
        self._mutex = win32event.CreateMutex(None, False, "Global\\StarkJarvisCompanionMutex")
        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
            print("[!] J.A.R.V.I.S. Desktop Companion is already running.")
            sys.exit(0)

        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S. - Autonomous AI Desktop Companion")
        self.root.configure(bg=BG_COLOR)

        # Remove default OS titlebar for bespoke sci-fi HUD appearance
        self.root.overrideredirect(True)

        # Window Geometry: 490px width x 750px height
        self.win_width = 490
        self.win_height = 750
        
        # Position neatly on the right side of the screen
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        pos_x = max(20, screen_w - self.win_width - 35)
        pos_y = max(20, (screen_h - self.win_height) // 2)
        self.root.geometry(f"{self.win_width}x{self.win_height}+{pos_x}+{pos_y}")

        # Window State
        self.is_pinned = True
        self.root.wm_attributes("-topmost", self.is_pinned)
        self.drag_start_x = 0
        self.drag_start_y = 0

        # Event Queue for Thread-Safe UI Updates
        self.event_queue = queue.Queue()

        # Visual Core State
        self.current_state = "idle"
        self.active_persona = "jarvis"
        self.anim_time = 0.0
        self.wave_phase = 0.0

        # Initialize 3D Fibonacci Particle Sphere
        self.num_particles = 42
        self.particles = []
        phi = math.pi * (3 - math.sqrt(5))
        for i in range(self.num_particles):
            y = 1 - (i / (self.num_particles - 1)) * 2
            r_at_y = math.sqrt(max(0.0, 1 - y * y))
            theta = phi * i
            self.particles.append({
                "orig_x": math.cos(theta) * r_at_y,
                "orig_y": y,
                "orig_z": math.sin(theta) * r_at_y,
                "pulse": i * 0.15
            })

        # Build UI Elements
        self._build_header_bar()
        self._build_canvas_core()
        self._build_conversation_cards()
        self._build_persona_bar()
        self._build_action_shortcuts()
        self._build_command_bar()

        # Keyboard shortcuts
        self.root.bind("<Escape>", lambda e: self.minimize_window())
        self.root.bind("<Return>", lambda e: self._on_text_submit())

        # Start UI event polling loop and 3D canvas animation loop
        self.root.after(25, self._poll_event_queue)
        self.root.after(25, self._render_canvas_frame)

        # Assistant Background Core
        self.assistant = None
        if start_assistant_core:
            self._init_assistant_core()

    # -------------------------------------------------------------------------
    # Window Chrome & Drag Handlers
    # -------------------------------------------------------------------------
    def _start_drag(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def _on_drag(self, event):
        x = self.root.winfo_x() + (event.x - self.drag_start_x)
        y = self.root.winfo_y() + (event.y - self.drag_start_y)
        self.root.geometry(f"+{x}+{y}")

    def toggle_pin(self):
        self.is_pinned = not self.is_pinned
        self.root.wm_attributes("-topmost", self.is_pinned)
        self.pin_btn.config(text="📌" if self.is_pinned else "📍")

    def minimize_window(self):
        self.root.overrideredirect(False)
        self.root.iconify()
        # Restore borderless when deiconified
        self.root.bind("<Map>", self._on_window_mapped)

    def _on_window_mapped(self, event):
        self.root.overrideredirect(True)
        self.root.unbind("<Map>")

    def bring_to_front(self):
        """Brings the native companion window to foreground upon laptop unlock."""
        try:
            self.root.overrideredirect(True)
            self.root.deiconify()
            self.root.lift()
            self.root.attributes("-topmost", True)
            hwnd = self.root.winfo_id()
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            if not self.is_pinned:
                self.root.after(3000, lambda: self.root.attributes("-topmost", False))
        except Exception:
            pass

    def close_app(self):
        """Clean shutdown of assistant processes and desktop window."""
        if self.assistant:
            try:
                self.assistant.stop_speaking()
                if self.assistant.listener:
                    self.assistant.listener.stop()
                if hasattr(self.assistant, "sentinel") and self.assistant.sentinel:
                    self.assistant.sentinel.stop()
            except Exception:
                pass
        self.root.destroy()
        os._exit(0)

    # -------------------------------------------------------------------------
    # UI Component Builders
    # -------------------------------------------------------------------------
    def _build_header_bar(self):
        header = tk.Frame(self.root, bg="#0a0f1d", height=42, bd=0)
        header.pack(fill="x", side="top")
        header.bind("<Button-1>", self._start_drag)
        header.bind("<B1-Motion>", self._on_drag)

        # Status badge
        badge_frame = tk.Frame(header, bg="#0a0f1d")
        badge_frame.pack(side="left", padx=12, pady=8)
        badge_frame.bind("<Button-1>", self._start_drag)
        badge_frame.bind("<B1-Motion>", self._on_drag)

        self.status_dot = tk.Label(badge_frame, text="●", fg=CYAN_ACCENT, bg="#0a0f1d", font=("Segoe UI", 11, "bold"))
        self.status_dot.pack(side="left")
        self.status_dot.bind("<Button-1>", self._start_drag)
        self.status_dot.bind("<B1-Motion>", self._on_drag)

        title_lbl = tk.Label(badge_frame, text="J.A.R.V.I.S. // STARK-OS", fg=CYAN_ACCENT, bg="#0a0f1d", font=("Segoe UI", 10, "bold"))
        title_lbl.pack(side="left", padx=6)
        title_lbl.bind("<Button-1>", self._start_drag)
        title_lbl.bind("<B1-Motion>", self._on_drag)

        ver_lbl = tk.Label(badge_frame, text="MARK XLII", fg=GOLD_ACCENT, bg="#0a0f1d", font=("Segoe UI", 8, "bold"))
        ver_lbl.pack(side="left")
        ver_lbl.bind("<Button-1>", self._start_drag)
        ver_lbl.bind("<B1-Motion>", self._on_drag)

        # Right control buttons
        btn_box = tk.Frame(header, bg="#0a0f1d")
        btn_box.pack(side="right", padx=8)

        self.pin_btn = tk.Button(btn_box, text="📌", bg="#0a0f1d", fg=TEXT_MUTED, bd=0, activebackground="#1e293b", activeforeground=CYAN_ACCENT, font=("Segoe UI", 10), command=self.toggle_pin, cursor="hand2")
        self.pin_btn.pack(side="left", padx=2)

        min_btn = tk.Button(btn_box, text="—", bg="#0a0f1d", fg=TEXT_MUTED, bd=0, activebackground="#1e293b", activeforeground=TEXT_MAIN, font=("Segoe UI", 10, "bold"), command=self.minimize_window, cursor="hand2")
        min_btn.pack(side="left", padx=4)

        close_btn = tk.Button(btn_box, text="✕", bg="#0a0f1d", fg=TEXT_MUTED, bd=0, activebackground="#ef4444", activeforeground="#ffffff", font=("Segoe UI", 10, "bold"), command=self.close_app, cursor="hand2")
        close_btn.pack(side="left", padx=2)

    def _build_canvas_core(self):
        canvas_frame = tk.Frame(self.root, bg=BG_COLOR)
        canvas_frame.pack(fill="x", padx=16, pady=(6, 2))

        self.canvas_w = 448
        self.canvas_h = 220
        self.canvas = tk.Canvas(
            canvas_frame,
            width=self.canvas_w,
            height=self.canvas_h,
            bg="#050811",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR
        )
        self.canvas.pack(fill="both", expand=True)

    def _build_conversation_cards(self):
        cards_frame = tk.Frame(self.root, bg=BG_COLOR)
        cards_frame.pack(fill="x", padx=16, pady=4)

        # 1. User Voice Heard Card
        user_card = tk.Frame(cards_frame, bg=PANEL_BG, bd=1, relief="solid", highlightthickness=1, highlightbackground=BORDER_COLOR)
        user_card.pack(fill="x", pady=3)

        u_hdr = tk.Frame(user_card, bg=PANEL_BG)
        u_hdr.pack(fill="x", padx=10, pady=(6, 2))
        tk.Label(u_hdr, text="🗣️ YOUR VOICE", fg=TEXT_MUTED, bg=PANEL_BG, font=("Segoe UI", 8, "bold")).pack(side="left")

        self.user_text_lbl = tk.Label(
            user_card,
            text="\"Listening for your voice anytime...\"",
            fg=TEXT_MAIN,
            bg=PANEL_BG,
            font=("Segoe UI", 10),
            wraplength=420,
            justify="left",
            anchor="w"
        )
        self.user_text_lbl.pack(fill="x", padx=10, pady=(2, 8))

        # 2. Assistant Response Card
        asst_card = tk.Frame(cards_frame, bg=PANEL_BG, bd=1, relief="solid", highlightthickness=1, highlightbackground=BORDER_COLOR)
        asst_card.pack(fill="x", pady=3)

        a_hdr = tk.Frame(asst_card, bg=PANEL_BG)
        a_hdr.pack(fill="x", padx=10, pady=(6, 2))
        tk.Label(a_hdr, text="🤖 ASSISTANT RESPONSE", fg=CYAN_ACCENT, bg=PANEL_BG, font=("Segoe UI", 8, "bold")).pack(side="left")
        
        self.persona_indicator = tk.Label(a_hdr, text="Christopher", fg=TEXT_MUTED, bg=PANEL_BG, font=("Segoe UI", 8))
        self.persona_indicator.pack(side="right")

        self.asst_text_lbl = tk.Label(
            asst_card,
            text="Autonomous Assistant ready. Speak or type your request.",
            fg=TEXT_MAIN,
            bg=PANEL_BG,
            font=("Segoe UI", 10),
            wraplength=420,
            justify="left",
            anchor="w"
        )
        self.asst_text_lbl.pack(fill="x", padx=10, pady=(2, 8))

    def _build_persona_bar(self):
        p_frame = tk.Frame(self.root, bg=BG_COLOR)
        p_frame.pack(fill="x", padx=16, pady=4)

        tk.Label(p_frame, text="PERSONA:", fg=TEXT_MUTED, bg=BG_COLOR, font=("Segoe UI", 8, "bold")).pack(side="left", padx=(0, 6))

        self.persona_btns = {}
        personas = [
            ("jarvis", "🤖 JARVIS"),
            ("friday", "🌸 FRIDAY"),
            ("edith", "⚡ EDITH"),
            ("christopher", "👤 Christopher"),
            ("neerja", "🇮🇳 Neerja")
        ]

        for p_id, p_label in personas:
            btn = tk.Button(
                p_frame,
                text=p_label,
                bg="#081426",
                fg=TEXT_MUTED,
                activebackground="#0c2842",
                activeforeground=CYAN_ACCENT,
                bd=1,
                relief="solid",
                font=("Segoe UI", 8, "bold"),
                cursor="hand2",
                command=lambda p=p_id: self.switch_persona(p)
            )
            btn.pack(side="left", padx=2)
            self.persona_btns[p_id] = btn

        self._update_persona_ui("jarvis")

    def _build_action_shortcuts(self):
        actions_frame = tk.Frame(self.root, bg=BG_COLOR)
        actions_frame.pack(fill="x", padx=16, pady=4)

        shortcuts = [
            ("📊 Briefing", "Give me my executive briefing."),
            ("🌐 Live News", "What is today's latest news?"),
            ("🚀 Antigravity", "Open the application called Anti-Gravity"),
            ("💼 LinkedIn", "Open LinkedIn and go to my profile"),
            ("🛑 Stop", "stop")
        ]

        for label, cmd in shortcuts:
            is_danger = "Stop" in label
            bg = "#3b0707" if is_danger else "#0f172a"
            fg = "#fca5a5" if is_danger else "#cbd5e1"
            border = "#ef4444" if is_danger else "#334155"
            
            btn = tk.Button(
                actions_frame,
                text=label,
                bg=bg,
                fg=fg,
                activebackground="#1e293b",
                activeforeground="#ffffff",
                bd=1,
                relief="solid",
                font=("Segoe UI", 8, "bold"),
                cursor="hand2",
                command=lambda c=cmd: self.execute_command(c)
            )
            btn.pack(side="left", fill="x", expand=True, padx=2)

    def _build_command_bar(self):
        cmd_frame = tk.Frame(self.root, bg=BG_COLOR)
        cmd_frame.pack(fill="x", padx=16, pady=(6, 12), side="bottom")

        self.cmd_entry = tk.Entry(
            cmd_frame,
            bg=PANEL_BG,
            fg=TEXT_MAIN,
            insertbackground=CYAN_ACCENT,
            bd=1,
            relief="solid",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            highlightcolor=CYAN_ACCENT,
            font=("Segoe UI", 10)
        )
        self.cmd_entry.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 6))

        send_btn = tk.Button(
            cmd_frame,
            text="SEND ➔",
            bg="#0284c7",
            fg="#ffffff",
            activebackground="#0369a1",
            activeforeground="#ffffff",
            bd=0,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
            command=self._on_text_submit
        )
        send_btn.pack(side="right", ipady=2, ipadx=8)

    # -------------------------------------------------------------------------
    # Assistant Lifecycle & Callbacks
    # -------------------------------------------------------------------------
    def _init_assistant_core(self):
        """Initializes AutonomousAssistant in background thread."""
        def _boot():
            self.assistant = AutonomousAssistant(
                tool_model="qwen2.5:3b",
                chat_model="dolphinlabs/llama3.2-3b-uncensored:latest",
                reasoning_model="nandhank/qwen3.5-abliterated-truthful:9b",
                default_profile="voice",
                voice_input_enabled=True,
                voice_output_enabled=True
            )

            # Hook into listener speech callbacks
            if self.assistant.listener:
                orig_on_detected = self.assistant.listener.on_speech_detected
                self.assistant.listener.on_speech_started = lambda: self.event_queue.put(("state", "listening"))
                
                def _wrap_detected(text):
                    self.event_queue.put(("heard", text))
                    self.event_queue.put(("state", "thinking"))
                    orig_on_detected(text)
                self.assistant.listener.on_speech_detected = _wrap_detected

            # Hook into speak for UI animation
            orig_speak = self.assistant.speak
            def _wrap_speak(text, wait=False):
                self.event_queue.put(("response", text))
                self.event_queue.put(("state", "speaking"))
                orig_speak(text, wait=wait)
            self.assistant.speak = _wrap_speak

            # Hook into unlock sentinel
            self.assistant.sentinel.on_unlock_callback = self._on_unlock_event

            # Start listener
            if self.assistant.listener:
                self.assistant.listener.start()

            # Monitor when speech finishes to return HUD smoothly to idle
            def _monitor_speech():
                last_speaking = False
                while True:
                    time.sleep(0.08)
                    if self.assistant:
                        now_speaking = self.assistant.is_speaking()
                        if not now_speaking and last_speaking:
                            self.event_queue.put(("state", "idle"))
                        last_speaking = now_speaking
            threading.Thread(target=_monitor_speech, daemon=True).start()

            # Initial Startup Greeting (Time-of-day personalized)
            time.sleep(0.5)
            time_greet = self.assistant.sentinel.briefing.get_time_greeting()
            startup_msg = f"{time_greet} J.A.R.V.I.S. is online. All diagnostic checks are green. How may I assist you?"
            self.event_queue.put(("response", startup_msg))
            self.event_queue.put(("state", "speaking"))
            self.assistant.speak(startup_msg)

        threading.Thread(target=_boot, daemon=True).start()

    def _on_unlock_event(self, briefing_text: str):
        """Called by Windows Session Unlock Sentinel when laptop is opened/unlocked."""
        self.event_queue.put(("unlock", briefing_text))
        self.event_queue.put(("state", "speaking"))
        if self.assistant:
            self.assistant.speak(briefing_text)

    def execute_command(self, cmd_text: str):
        """Executes a command through the assistant's cognitive pipeline."""
        cleaned = cmd_text.strip()
        if not cleaned:
            return

        # Instant Barge-In Stop Shortcut
        if cleaned.lower() in ["stop", "pause", "quiet", "silence"]:
            if self.assistant:
                self.assistant.stop_speaking()
            self.event_queue.put(("state", "barge_in"))
            self.event_queue.put(("response", "Understood. Paused and standing by."))
            self.root.after(1200, lambda: self.event_queue.put(("state", "idle")))
            return
        
        self.event_queue.put(("heard", cleaned))
        self.event_queue.put(("state", "thinking"))

        if not self.assistant:
            self.event_queue.put(("response", f"Executing: {cleaned}"))
            return

        def _worker():
            res = self.assistant.process_message(cleaned)
            self.event_queue.put(("response", res))
            self.event_queue.put(("state", "idle"))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_text_submit(self):
        text = self.cmd_entry.get().strip()
        if text:
            self.cmd_entry.delete(0, tk.END)
            self.execute_command(text)

    def switch_persona(self, persona_name: str):
        """Switches the active neural voice persona."""
        self._update_persona_ui(persona_name)
        if self.assistant:
            ack = self.assistant.voice_engine.set_persona(persona_name)
            self.event_queue.put(("response", ack))
            self.assistant.speak(ack)

    def _update_persona_ui(self, persona_name: str):
        self.active_persona = persona_name
        self.persona_indicator.config(text=persona_name.capitalize())
        for p_id, btn in self.persona_btns.items():
            if p_id == persona_name:
                btn.config(bg="#0369a1", fg="#ffffff", relief="solid", bd=1)
            else:
                btn.config(bg="#0e172a", fg=TEXT_MUTED, relief="flat", bd=0)

    # -------------------------------------------------------------------------
    # Thread-Safe Event Queue Consumer
    # -------------------------------------------------------------------------
    def _poll_event_queue(self):
        while not self.event_queue.empty():
            try:
                event_type, data = self.event_queue.get_nowait()
                if event_type == "state":
                    self.current_state = data
                elif event_type == "heard":
                    self.user_text_lbl.config(text=f"\"{data}\"")
                elif event_type == "response":
                    self.asst_text_lbl.config(text=data)
                elif event_type == "persona":
                    self._update_persona_ui(data)
                elif event_type == "unlock":
                    self.bring_to_front()
                    self.asst_text_lbl.config(text=data)
            except queue.Empty:
                break
        self.root.after(25, self._poll_event_queue)

    # -------------------------------------------------------------------------
    # Procedural J.A.R.V.I.S. Arc Reactor Hologram Canvas (60 FPS)
    # -------------------------------------------------------------------------
    def _render_canvas_frame(self):
        self.canvas.delete("all")
        cfg = STATE_CONFIGS.get(self.current_state, STATE_CONFIGS["idle"])
        
        self.anim_time += cfg["speed"]
        self.wave_phase += 0.10
        t = self.anim_time

        cx = self.canvas_w / 2
        cy = self.canvas_h / 2

        # 1. Outer Compass Reticle & Cardinal Degree Markers
        r_outer = 104
        self.canvas.create_oval(cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer, outline="#082b3e", width=1)
        
        # Outer Corner Target Brackets
        b_len = 16
        for bx, by in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            ox = cx + bx * (r_outer + 12)
            oy = cy + by * (r_outer + 12)
            self.canvas.create_line(ox, oy, ox - bx * b_len, oy, fill="#005577", width=1)
            self.canvas.create_line(ox, oy, ox, oy - by * b_len, fill="#005577", width=1)

        # Degree Labels: 000, 090, 180, 270
        deg_offset = r_outer + 8
        self.canvas.create_text(cx, cy - deg_offset, text="000°", fill="#007799", font=("Segoe UI", 6, "bold"))
        self.canvas.create_text(cx + deg_offset, cy, text="090°", fill="#007799", font=("Segoe UI", 6, "bold"))
        self.canvas.create_text(cx, cy + deg_offset, text="180°", fill="#007799", font=("Segoe UI", 6, "bold"))
        self.canvas.create_text(cx - deg_offset, cy, text="270°", fill="#007799", font=("Segoe UI", 6, "bold"))

        # Outer Reticle Tick Marks (every 15 deg)
        for i in range(24):
            ang = (i / 24) * math.pi * 2
            t_len = 6 if i % 6 == 0 else 3
            p1x = cx + math.cos(ang) * (r_outer - t_len)
            p1y = cy + math.sin(ang) * (r_outer - t_len)
            p2x = cx + math.cos(ang) * r_outer
            p2y = cy + math.sin(ang) * r_outer
            self.canvas.create_line(p1x, p1y, p2x, p2y, fill="#0088aa" if i % 6 == 0 else "#003b55", width=1)

        # 2. Outer Rotating Segmented Armor Shield Ring (Clockwise)
        r_seg = 92
        num_shields = 6
        for s in range(num_shields):
            start_angle = (s * (360 / num_shields) + t * 45) % 360
            self.canvas.create_arc(
                cx - r_seg, cy - r_seg, cx + r_seg, cy + r_seg,
                start=start_angle, extent=38,
                outline=cfg["primary"], width=2, style="arc"
            )

        # 3. Inner Counter-Rotating Tachymeter Ring (Counter-Clockwise)
        r_inner = 76
        num_teeth = 8
        for tooth in range(num_teeth):
            start_angle = (tooth * (360 / num_teeth) - t * 65) % 360
            self.canvas.create_arc(
                cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner,
                start=start_angle, extent=24,
                outline=cfg["primary"], width=3, style="arc"
            )

        # 4. Radial Audio Frequency Equalizer Bars (J.A.R.V.I.S. Voice Spikes)
        num_bars = 36
        r_eq_base = 62
        for b in range(num_bars):
            ang = (b / num_bars) * math.pi * 2
            
            # Dynamic amplitude based on active speech / listening state
            if self.current_state == "speaking":
                amp = 4 + abs(math.sin(self.wave_phase * 1.8 + b * 0.6)) * 14 + math.cos(self.wave_phase * 0.9 + b) * 4
            elif self.current_state == "listening":
                amp = 3 + abs(math.sin(self.wave_phase + b * 0.4)) * 6
            elif self.current_state == "thinking":
                amp = 4 + abs(math.sin(t * 8 + b * 1.2)) * 10
            elif self.current_state == "barge_in":
                amp = 8
            else:
                amp = 2 + math.sin(t * 2 + b * 0.3) * 1.5

            r_eq_tip = r_eq_base + amp
            p1x = cx + math.cos(ang) * r_eq_base
            p1y = cy + math.sin(ang) * r_eq_base
            p2x = cx + math.cos(ang) * r_eq_tip
            p2y = cy + math.sin(ang) * r_eq_tip

            bar_color = cfg["primary"] if b % 2 == 0 else "#38bdf8"
            self.canvas.create_line(p1x, p1y, p2x, p2y, fill=bar_color, width=2)

        # 5. Central Luminous Plasma Core & Radial Energy Pulse
        pulse = math.sin(t * 3.5) * 4
        r_core = 36 + pulse
        
        # Translucent energy glow layers
        self.canvas.create_oval(
            cx - r_core - 14, cy - r_core - 14,
            cx + r_core + 14, cy + r_core + 14,
            fill=cfg["glow"], outline=""
        )
        self.canvas.create_oval(
            cx - r_core, cy - r_core,
            cx + r_core, cy + r_core,
            fill="#030d1a", outline=cfg["primary"], width=2
        )
        
        # Center Core Text: J.A.R.V.I.S.
        self.canvas.create_text(
            cx, cy - 8,
            text="J.A.R.V.I.S.",
            fill="#ffffff",
            font=("Segoe UI", 9, "bold")
        )
        self.canvas.create_text(
            cx, cy + 6,
            text=cfg["label"],
            fill=cfg["primary"],
            font=("Segoe UI", 7, "bold")
        )
        self.canvas.create_text(
            cx, cy + 18,
            text=f"PROTO // {self.active_persona.upper()}",
            fill=TEXT_MUTED,
            font=("Segoe UI", 6)
        )

        self.root.after(25, self._render_canvas_frame)

    def run(self):
        """Starts the native desktop companion GUI event loop."""
        self.root.mainloop()

if __name__ == "__main__":
    app = DesktopCompanionHUD(start_assistant_core=True)
    app.run()
