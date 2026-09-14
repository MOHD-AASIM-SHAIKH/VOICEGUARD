import tkinter as tk
import threading
import sys, os

# Allow running as standalone or via module import
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "core-detection"))
from chunker import AudioChunker
from smoother import ConfidenceSmoother, is_silence
from detector import DetectorModel
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "loopback-capture"))
from capture import get_loopback_stream

class AlertWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("VoiceGuard")
        self.root.attributes("-topmost", True)
        self.label = tk.Label(
            self.root, text="REAL", bg="green", fg="white",
            font=("Arial", 32), width=20, height=5
        )
        self.label.pack()
        self.report_btn = tk.Button(self.root, text="Report", command=self.on_report)
        self.report_btn.pack()
        self.last_incident = None

    def set_state(self, state):
        if state == "CLONED":
            self.label.config(text="CLONE DETECTED", bg="red")
        else:
            self.label.config(text="REAL", bg="green")

    def on_report(self):
        # Wired to reporting module in Phase 8
        # on_report will build evidence hash + open Chakshu link
        print("Report button pressed — wiring to reporting module pending Phase 8.")
        pass

    def run_detection_loop(self):
        chunker = AudioChunker()
        smoother = ConfidenceSmoother()
        model = DetectorModel()
        t = 0.0
        for audio_block in get_loopback_stream():
            for chunk in chunker.push(audio_block):
                if is_silence(chunk):
                    continue
                pred = model.predict(chunk)
                result = smoother.update(pred, t)
                self.root.after(0, self.set_state, result["state"])
                t += chunker.chunk_len / chunker.sample_rate

    def start(self):
        threading.Thread(target=self.run_detection_loop, daemon=True).start()
        self.root.mainloop()

if __name__ == "__main__":
    AlertWindow().start()
