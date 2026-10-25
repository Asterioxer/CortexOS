"""
CortexOS Native Desktop Companion HUD.
Absorbed and modernized from Voice Lab.

Features:
1. Native Windows desktop GUI application running in pure Tkinter + Win32.
2. Procedural 3D Quantum Core Hologram Canvas (60 FPS particle sphere and rotating gimbals).
3. State-Reactive Chromatic Breathing (Standby, Listening, Reasoning, Speaking, Barge-in).
4. Direct integration with CortexVoiceAssistant and Somatosensory Engine.
5. Interactive persona switcher and quick command entry box.
"""

import os
import sys
import time
import math
import queue
import threading
import tkinter as tk
from tkinter import ttk
from typing import Optional

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from cortex.voice_assistant import CortexVoiceAssistant
from cortex.embodiment.voice import CortexVoiceEngine

# Palette & Visual Constants
BG_COLOR = "#040810"
PANEL_BG = "#08101e"
BORDER_COLOR = "#0c2842"
TEXT_MAIN = "#f8fafc"
TEXT_MUTED = "#64748b"
CYAN_ACCENT = "#00f0ff"
GOLD_ACCENT = "#fbbf24"
EMERALD_ACCENT = "#10b981"
PURPLE_ACCENT = "#c084fc"
AMBER_ACCENT = "#f59e0b"
RED_ACCENT = "#ef4444"
SKY_ACCENT = "#38bdf8"

STATE_CONFIGS = {
    "idle": {"label": "STANDBY", "primary": CYAN_ACCENT, "glow": "#012a42", "speed": 0.015},
    "listening": {"label": "LISTENING", "primary": EMERALD_ACCENT, "glow": "#064e3b", "speed": 0.04},
    "reasoning": {"label": "REASONING", "primary": PURPLE_ACCENT, "glow": "#3b0764", "speed": 0.06},
    "speaking": {"label": "SPEAKING", "primary": SKY_ACCENT, "glow": "#075985", "speed": 0.035},
    "barge_in": {"label": "HALT / BARGE-IN", "primary": RED_ACCENT, "glow": "#450a0a", "speed": 0.08}
}


class CortexCompanionHUD:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("CortexOS // Neural Quantum Core HUD")
        self.root.configure(bg=BG_COLOR)
        self.root.geometry("460x640")
        self.root.minsize(420, 580)

        # Assistant Backend
        self.assistant = CortexVoiceAssistant(voice_enabled=True)
        self.active_state = "idle"
        self.rotation_y = 0.0
        self.rotation_x = 0.3
        self.sphere_points = self._generate_fibonacci_sphere(220)

        self._build_ui()
        self._start_animation_loop()

        # Start assistant in background
        threading.Thread(target=self.assistant.start, daemon=True).start()

    def _generate_fibonacci_sphere(self, n_points: int):
        points = []
        phi = math.pi * (3.0 - math.sqrt(5.0))
        for i in range(n_points):
            y = 1.0 - (i / float(n_points - 1)) * 2.0
            radius = math.sqrt(1.0 - y * y)
            theta = phi * i
            x = math.cos(theta) * radius
            z = math.sin(theta) * radius
            points.append((x, y, z))
        return points

    def _build_ui(self):
        # Header Bar
        header = tk.Frame(self.root, bg=PANEL_BG, pady=10, padx=16, highlightthickness=1, highlightbackground=BORDER_COLOR)
        header.pack(fill=tk.X, side=tk.TOP)

        title_lbl = tk.Label(header, text="CORTEX-OS // COGNITIVE EMBODIMENT", font=("Segoe UI", 10, "bold"), fg=CYAN_ACCENT, bg=PANEL_BG)
        title_lbl.pack(side=tk.LEFT)

        self.state_badge = tk.Label(header, text="STANDBY", font=("Segoe UI", 8, "bold"), fg=CYAN_ACCENT, bg="#082f49", padx=8, pady=2)
        self.state_badge.pack(side=tk.RIGHT)

        # 3D Canvas
        self.canvas = tk.Canvas(self.root, bg=BG_COLOR, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Bottom Control Panel
        control_panel = tk.Frame(self.root, bg=PANEL_BG, pady=12, padx=16, highlightthickness=1, highlightbackground=BORDER_COLOR)
        control_panel.pack(fill=tk.X, side=tk.BOTTOM)

        # Persona Selector
        persona_row = tk.Frame(control_panel, bg=PANEL_BG)
        persona_row.pack(fill=tk.X, pady=(0, 8))

        lbl_p = tk.Label(persona_row, text="Persona:", font=("Segoe UI", 9), fg=TEXT_MUTED, bg=PANEL_BG)
        lbl_p.pack(side=tk.LEFT, padx=(0, 6))

        self.persona_var = tk.StringVar(value="Friday")
        personas = ["Friday", "Jarvis", "Edith", "Christopher", "Neerja", "Jenny", "Guy"]
        self.combo_persona = ttk.Combobox(persona_row, textvariable=self.persona_var, values=personas, state="readonly", width=12)
        self.combo_persona.pack(side=tk.LEFT)
        self.combo_persona.bind("<<ComboboxSelected>>", self._on_persona_change)

        btn_halt = tk.Button(persona_row, text="HALT (Barge-In)", font=("Segoe UI", 8, "bold"), bg="#450a0a", fg="#fca5a5", activebackground="#7f1d1d", relief=tk.FLAT, padx=8, pady=2, command=self._on_halt)
        btn_halt.pack(side=tk.RIGHT)

        # Quick Command Entry
        input_row = tk.Frame(control_panel, bg=PANEL_BG)
        input_row.pack(fill=tk.X)

        self.entry_cmd = tk.Entry(input_row, font=("Segoe UI", 10), bg="#040810", fg=TEXT_MAIN, insertbackground=CYAN_ACCENT, highlightthickness=1, highlightbackground=BORDER_COLOR, relief=tk.FLAT)
        self.entry_cmd.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=4)
        self.entry_cmd.bind("<Return>", lambda e: self._on_submit_command())

        btn_send = tk.Button(input_row, text="SEND", font=("Segoe UI", 9, "bold"), bg="#0284c7", fg=TEXT_MAIN, activebackground="#0369a1", relief=tk.FLAT, padx=12, pady=4, command=self._on_submit_command)
        btn_send.pack(side=tk.RIGHT)

    def _on_persona_change(self, event=None):
        p = self.persona_var.get().lower()
        self.assistant.active_persona = p
        self.assistant.voice.set_persona(p)

    def _on_halt(self):
        self.assistant.voice.stop()
        self.set_state("barge_in")
        self.root.after(800, lambda: self.set_state("idle"))

    def _on_submit_command(self):
        cmd = self.entry_cmd.get().strip()
        if not cmd:
            return
        self.entry_cmd.delete(0, tk.END)
        self.set_state("reasoning")
        threading.Thread(target=self._run_command_async, args=(cmd,), daemon=True).start()

    def _run_command_async(self, cmd: str):
        try:
            self.assistant.handle_input(cmd)
        finally:
            self.root.after(100, lambda: self.set_state("idle"))

    def set_state(self, state: str):
        if state not in STATE_CONFIGS:
            state = "idle"
        self.active_state = state
        cfg = STATE_CONFIGS[state]
        self.state_badge.config(text=cfg["label"], fg=cfg["primary"])

    def _start_animation_loop(self):
        self._render_frame()

    def _render_frame(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width() or 400
        h = self.canvas.winfo_height() or 420
        cx, cy = w / 2.0, h / 2.0
        radius = min(w, h) * 0.35

        cfg = STATE_CONFIGS.get(self.active_state, STATE_CONFIGS["idle"])
        self.rotation_y += cfg["speed"]

        # Project 3D points
        cos_y = math.cos(self.rotation_y)
        sin_y = math.sin(self.rotation_y)
        cos_x = math.cos(self.rotation_x)
        sin_x = math.sin(self.rotation_x)

        projected = []
        for x, y, z in self.sphere_points:
            # Rotate Y
            rx = x * cos_y + z * sin_y
            rz = -x * sin_y + z * cos_y
            # Rotate X
            ry = y * cos_x - rz * sin_x
            rz = y * sin_x + rz * cos_x

            # Perspective projection
            fov = 300.0
            scale = fov / (fov + rz * radius + 150.0)
            px = cx + rx * radius * scale
            py = cy + ry * radius * scale
            projected.append((rz, px, py, scale))

        # Sort by depth (back to front)
        projected.sort(key=lambda p: p[0])

        color = cfg["primary"]
        for rz, px, py, scale in projected:
            size = max(1.0, 2.8 * scale)
            self.canvas.create_oval(px - size, py - size, px + size, py + size, fill=color, outline="")

        # Draw Gimbal ring
        self.canvas.create_oval(cx - radius * 1.15, cy - radius * 0.4, cx + radius * 1.15, cy + radius * 0.4, outline=cfg["glow"], width=1.5)

        self.root.after(16, self._render_frame)


def main():
    root = tk.Tk()
    app = CortexCompanionHUD(root)
    root.mainloop()


if __name__ == "__main__":
    main()
