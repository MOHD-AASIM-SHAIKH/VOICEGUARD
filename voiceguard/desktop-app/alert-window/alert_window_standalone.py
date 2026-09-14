"""
VoiceGuard Desktop Alert Window — Redesigned
Design: white bg, black/gray only, single accent color (green=REAL, red=CLONE).
Flat, no gradients, Inter/system font, generous whitespace.
"""

import tkinter as tk
import tkinter.font as tkfont
import threading
import sys, os
import math
import time

# Patch import paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "core-detection"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "loopback-capture"))

from chunker import AudioChunker  # type: ignore
from smoother import ConfidenceSmoother, is_silence  # type: ignore
from detector import DetectorModel  # type: ignore
from capture import get_loopback_stream  # type: ignore

# ── Design tokens ──────────────────────────────────────────────
BG          = "#FFFFFF"
TEXT_PRIMARY = "#111111"
TEXT_GRAY   = "#888888"
TEXT_LIGHT  = "#BBBBBB"
BORDER      = "#DDDDDD"
GREEN       = "#2E7D4F"   # REAL — only accent color
RED         = "#C0392B"   # CLONE DETECTED — only accent color
WIN_W       = 420
WIN_H       = 360
PAD         = 32


class WaveformCanvas(tk.Canvas):
    """Animated thin-line waveform — gray bars, subtle pulse."""

    BARS   = 28
    BAR_W  = 3
    GAP    = 4
    BASE_H = 4
    MAX_H  = 28

    def __init__(self, parent, **kw):
        w = self.BARS * (self.BAR_W + self.GAP) - self.GAP
        super().__init__(parent, width=w, height=self.MAX_H + 2,
                         bg=BG, highlightthickness=0, **kw)
        self._running = True
        self._phase = 0.0
        self._animate()

    def _animate(self):
        if not self._running:
            return
        self.delete("all")
        self._phase += 0.12
        for i in range(self.BARS):
            h = self.BASE_H + (self.MAX_H - self.BASE_H) * (
                0.5 + 0.5 * math.sin(self._phase + i * 0.45)
            ) * (0.4 + 0.6 * math.sin(self._phase * 0.7 + i * 0.3))
            h = max(self.BASE_H, int(h))
            x = i * (self.BAR_W + self.GAP)
            cy = (self.MAX_H + 2) // 2
            self.create_rectangle(x, cy - h // 2, x + self.BAR_W, cy + h // 2,
                                  fill=TEXT_LIGHT, outline="")
        self.after(50, self._animate)

    def stop(self):
        self._running = False


class AlertWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("VoiceGuard")
        self.root.configure(bg=BG)
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)
        self.root.geometry(f"{WIN_W}x{WIN_H}")

        self.last_state      = "REAL"
        self.last_confidence = 0.0
        self._elapsed        = 0
        self._start_time     = time.time()

        self._build_ui()
        self._tick_elapsed()

    # ── UI construction ────────────────────────────────────────
    def _build_ui(self):
        root = self.root

        # ── Top bar ──────────────────────────────────────────
        topbar = tk.Frame(root, bg=BG)
        topbar.pack(fill="x", padx=PAD, pady=(20, 0))

        tk.Label(topbar, text="Voice Guard", font=("Segoe UI", 13, "bold"),
                 bg=BG, fg=TEXT_PRIMARY).pack(side="left")

        self.status_var = tk.StringVar(value="Loading model…")
        tk.Label(topbar, textvariable=self.status_var,
                 font=("Segoe UI", 10), bg=BG, fg=TEXT_GRAY).pack(side="right")

        # ── Thin divider ─────────────────────────────────────
        tk.Frame(root, height=1, bg=BORDER).pack(fill="x", padx=PAD, pady=(12, 0))

        # ── Main state label ─────────────────────────────────
        center = tk.Frame(root, bg=BG)
        center.pack(expand=True, fill="both", padx=PAD)

        self.state_label = tk.Label(
            center, text="REAL",
            font=("Segoe UI", 48, "bold"),
            bg=BG, fg=GREEN,
            anchor="center",
        )
        self.state_label.pack(pady=(24, 4))

        self.conf_label = tk.Label(
            center, text="Confidence: —",
            font=("Segoe UI", 11), bg=BG, fg=TEXT_GRAY,
        )
        self.conf_label.pack()

        # ── Waveform ─────────────────────────────────────────
        self.wave = WaveformCanvas(center)
        self.wave.pack(pady=(12, 0))

        self.elapsed_label = tk.Label(
            center, text="Monitoring active · 0:00",
            font=("Segoe UI", 9), bg=BG, fg=TEXT_LIGHT,
        )
        self.elapsed_label.pack(pady=(6, 0))

        # ── Thin divider ─────────────────────────────────────
        tk.Frame(root, height=1, bg=BORDER).pack(fill="x", padx=PAD, pady=(16, 0))

        # ── Buttons ───────────────────────────────────────────
        btn_row = tk.Frame(root, bg=BG)
        btn_row.pack(fill="x", padx=PAD, pady=(12, 20))

        # Primary: Hang Up (solid black — shown only during CLONED state)
        self.hangup_btn = tk.Button(
            btn_row, text="Hang Up",
            command=self._on_hangup,
            font=("Segoe UI", 11, "bold"),
            bg=TEXT_PRIMARY, fg=BG,
            relief="flat", bd=0,
            padx=16, pady=8,
            cursor="hand2",
        )
        # Secondary: Report (outlined)
        self.report_btn = tk.Button(
            btn_row, text="Report to Chakshu / TRAI",
            command=self._on_report,
            font=("Segoe UI", 11),
            bg=BG, fg=TEXT_PRIMARY,
            relief="solid", bd=1,
            padx=16, pady=8,
            cursor="hand2",
            highlightbackground=BORDER,
        )

        # Start in REAL state — only show Report
        self.report_btn.pack(side="right")
        self._hangup_visible = False

    # ── State transitions ──────────────────────────────────────
    def set_state(self, state, confidence=0.0):
        self.last_state      = state
        self.last_confidence = confidence

        if state == "CLONED":
            self.state_label.config(text="CLONE DETECTED", fg=RED)
            self.conf_label.config(text=f"Confidence: {confidence:.1%}")
            if not self._hangup_visible:
                self.hangup_btn.pack(side="left")
                self._hangup_visible = True
        else:
            self.state_label.config(text="REAL", fg=GREEN)
            self.conf_label.config(text=f"Confidence: {confidence:.1%}")
            if self._hangup_visible:
                self.hangup_btn.pack_forget()
                self._hangup_visible = False

    # ── Elapsed timer ──────────────────────────────────────────
    def _tick_elapsed(self):
        secs = int(time.time() - self._start_time)
        m, s = divmod(secs, 60)
        self.elapsed_label.config(text=f"Monitoring active · {m}:{s:02d}")
        self.root.after(1000, self._tick_elapsed)

    # ── Button actions ─────────────────────────────────────────
    def _on_hangup(self):
        """Signal the user to hang up (desktop: just log + flash status)."""
        self.status_var.set("Hang up now — clone voice detected")

    def _on_report(self):
        import urllib.parse, webbrowser, datetime
        ts   = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        conf = f"{self.last_confidence:.2f}"
        url  = ("https://sancharsaathi.gov.in/sfc/?"
                + urllib.parse.urlencode({
                    "reportedAt": ts,
                    "callType":   "voip",
                    "confidence": conf,
                }))
        webbrowser.open(url)
        self.status_var.set(f"Reported at {ts}")

    # ── Detection loop ─────────────────────────────────────────
    def run_detection_loop(self):
        self.root.after(0, self.status_var.set, "Loading AI model…")
        model   = DetectorModel()
        chunker = AudioChunker()
        smoother= ConfidenceSmoother()
        t = 0.0
        self.root.after(0, self.status_var.set, "Monitoring")
        try:
            for audio_block in get_loopback_stream():
                for chunk in chunker.push(audio_block):
                    if is_silence(chunk):
                        continue
                    pred       = model.predict(chunk)
                    result     = smoother.update(pred, t)
                    confidence = pred.get("confidence", 0.0)
                    self.root.after(0, self.set_state, result["state"], confidence)
                    t += chunker.chunk_len / chunker.sample_rate
        except Exception as e:
            self.root.after(0, self.status_var.set, f"Error: {e}")

    def start(self):
        threading.Thread(target=self.run_detection_loop, daemon=True).start()
        self.root.mainloop()


if __name__ == "__main__":
    AlertWindow().start()
