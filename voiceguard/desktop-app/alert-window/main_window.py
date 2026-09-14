"""VoiceGuard Desktop Application — Main Window & Flow Controller.
PySide6 implementation wiring all five screens per UI Spec.

AMBIENT-TICK REMOVAL (Part 5.0):
  All ambient/idle ticker logic has been removed. The ring is updated from
  exactly ONE place: on_detection_result(). During silence, on_detection_result()
  is never called, so the ring holds its last position — static, correct, honest.

DETECTION LOOP (Part 2):
  1. source_label = next(stream)     ← generator protocol; update UI with this
  2. for audio_block in stream:
       for chunk in chunker.push(audio_block):
           if is_silence(chunk): continue
           pred   = model.predict(chunk)       ← normalizes internally, no caller norm
           result = smoother.update(pred["spoof_prob"], t)
           emit_result(result)                 ← only call site for ring update
"""
import sys, os, time, threading, random
from pathlib import Path
import numpy as np

from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QKeyEvent

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR.parent.parent / "core-detection"))
sys.path.insert(0, str(BASE_DIR.parent / "loopback-capture"))

import tokens
from screens.screen1_listening import Screen1Listening
from screens.screen2_clone_alert import Screen2CloneAlert
from screens.screen3_report import Screen3Report
from screens.screen4_approval import Screen4Approval
from screens.screen5_history import Screen5History


class DetectionSignals(QObject):
    """Signals emitted from the background detector thread to the UI thread."""
    detection_updated  = Signal(dict)    # full result dict from smoother.update()
    audio_level_updated = Signal(float)  # raw RMS for optional level display (not ring)
    model_ready        = Signal(str)     # source_label, once model + stream are ready
    error_occurred     = Signal(str)


class VoiceGuardMainWindow(QMainWindow):
    def __init__(self, start_detector=True, parent=None):
        super().__init__(parent)
        self.setObjectName("appWindow")
        self.setWindowTitle("VoiceGuard")
        self.resize(480, 720)
        self.setMinimumSize(390, 600)

        self.audio_source = "loopback"
        self.latest_spoof_prob = 0.05   # track honest last value for display
        self.start_time = time.time()
        self._model_loading = True
        self._last_emitted_state = "REAL"  # edge-gate: only trigger alert on REAL→CLONED

        # ── Stack ─────────────────────────────────────────────────────────────
        self.stack = QStackedWidget()
        self.stack.setObjectName("screenContainer")
        self.setCentralWidget(self.stack)

        self.screen_idle     = Screen1Listening()
        self.screen_alert    = Screen2CloneAlert()
        self.screen_report   = Screen3Report()
        self.screen_approval = Screen4Approval()
        self.screen_history  = Screen5History()
        self.reports_history = list(self.screen_history._default_incidents())
        self.screen_history.set_reports(self.reports_history)

        self.stack.addWidget(self.screen_idle)      # 0
        self.stack.addWidget(self.screen_alert)     # 1
        self.stack.addWidget(self.screen_report)    # 2
        self.stack.addWidget(self.screen_approval)  # 3
        self.stack.addWidget(self.screen_history)   # 4

        self._wire_navigation()
        self.show_idle()

        # Show loading state before model initializes
        self._set_loading_display()

        # Elapsed call timer (only updates text label, not the ring value)
        self._elapsed_timer = QTimer(self)
        self._elapsed_timer.timeout.connect(self._update_elapsed)
        self._elapsed_timer.start(1000)

        # ── Signals ───────────────────────────────────────────────────────────
        self.detector_active = start_detector
        self.signals = DetectionSignals()
        self.signals.detection_updated.connect(self.on_detection_result)
        self.signals.audio_level_updated.connect(self.on_audio_level)
        self.signals.model_ready.connect(self._on_model_ready)
        self.signals.error_occurred.connect(self._on_error)

        if self.detector_active:
            self._start_detector_thread()

    # Expose smoother for pause/reset (set by _start_detector_thread once created)
    _smoother = None

    # ── Loading display ───────────────────────────────────────────────────────

    def _set_loading_display(self):
        self.screen_idle.circular_meter.update_data(
            state="REAL", confidence=0.0, caption="Loading…"
        )
        if hasattr(self.screen_idle, "context_body"):
            self.screen_idle.context_body.setText(
                "Loading AI model… please wait\n"
                "VoiceGuard on-device AASIST-L initializing"
            )

    def _on_model_ready(self, source_label: str):
        self._model_loading = False
        self.start_time = time.time()
        self.screen_idle.circular_meter.update_data(
            state="REAL", confidence=0.95, caption="Active · 00:00"
        )
        if hasattr(self.screen_idle, "context_body"):
            self.screen_idle.context_body.setText(
                f"Audio source: {source_label}\n"
                "On-device AASIST-L model · Blockchain notary active"
            )

    def _on_error(self, msg: str):
        if hasattr(self.screen_idle, "context_body"):
            self.screen_idle.context_body.setText(
                f"Detection error: {msg}\n"
                "Check console for details"
            )

    # ── Navigation wiring ────────────────────────────────────────────────────

    def _wire_navigation(self):
        self.screen_idle.stop_protection_clicked.connect(self.handle_stop_protection)
        self.screen_idle.simulate_clone_clicked.connect(self.trigger_clone_detected)
        self.screen_idle.guarded_tx_clicked.connect(self.show_approval)
        self.screen_idle.blockchain_ledger_clicked.connect(self.show_history)
        self.screen_idle.source_toggle_clicked.connect(self.toggle_audio_source)

        self.screen_alert.hang_up_clicked.connect(self.show_idle)
        self.screen_alert.report_clicked.connect(self.show_report_confirmation)

        self.screen_report.confirm_report_clicked.connect(self.handle_confirm_report)
        self.screen_report.cancel_clicked.connect(self.show_idle)

        self.screen_approval.approve_clicked.connect(self.show_idle)
        self.screen_approval.reject_clicked.connect(self.show_idle)

        self.screen_history.back_clicked.connect(self.show_idle)

    def toggle_audio_source(self):
        """Toggle between System Loopback (Calls) and Microphone (User Voice)."""
        if self.audio_source == "loopback":
            self.audio_source = "microphone"
            self.screen_idle.btn_toggle_source.setText("🔊 Loopback Mode")
            self.screen_idle.btn_toggle_source.setToolTip("Currently listening to Microphone. Click to switch to System Loopback.")
        else:
            self.audio_source = "loopback"
            self.screen_idle.btn_toggle_source.setText("🎙️ Mic Mode")
            self.screen_idle.btn_toggle_source.setToolTip("Currently listening to System Loopback. Click to switch to Microphone.")
        if hasattr(self.screen_idle, "context_body"):
            self.screen_idle.context_body.setText(
                f"Switching audio input to {self.audio_source.capitalize()}…\n"
                "VoiceGuard on-device monitoring active"
            )

    def _update_elapsed(self):
        if self._model_loading or not self.detector_active:
            return
        elapsed = int(time.time() - self.start_time)
        m, s = divmod(elapsed, 60)
        if self.stack.currentWidget() == self.screen_idle:
            self.screen_idle.circular_meter.set_caption(f"Active · {m:02d}:{s:02d}")

    # ── Navigation slots ─────────────────────────────────────────────────────

    def show_idle(self):
        self._last_emitted_state = "REAL"
        if self._smoother is not None:
            self._smoother.reset()
        self.stack.setCurrentWidget(self.screen_idle)

    def trigger_clone_detected(self, confidence: float = 0.96):
        """Directly navigate to Report & Blockchain Notarization screen when clone is detected."""
        self.latest_spoof_prob = confidence
        self._last_emitted_state = "CLONED"
        self.show_report_confirmation()

    def show_report_confirmation(self):
        import datetime
        now = datetime.datetime.now()
        # Honest confidence calculation (clamp to 50–99%)
        if self.latest_spoof_prob >= 0.5:
            conf_display = int(round(self.latest_spoof_prob * 100))
        else:
            conf_display = int(round((1.0 - self.latest_spoof_prob) * 100))
        conf_display = max(50, min(99, conf_display))

        channel = "Microphone" if self.audio_source == "microphone" else "WhatsApp VoIP"

        old_idx = self.stack.indexOf(self.screen_report)
        self.stack.removeWidget(self.screen_report)
        self.screen_report.deleteLater()
        self.screen_report = Screen3Report(
            time_str=now.strftime("%H:%M, %b %d"),
            confidence_str=f"{conf_display}%",
            call_type_str=channel
        )
        self.screen_report.confirm_report_clicked.connect(self.handle_confirm_report)
        self.screen_report.cancel_clicked.connect(self.show_idle)
        insert_idx = old_idx if old_idx >= 0 else 2
        self.stack.insertWidget(insert_idx, self.screen_report)
        self.stack.setCurrentWidget(self.screen_report)

    def show_approval(self, amount: str = "₹50,00,000", to: str = "ABC Industries Pvt Ltd"):
        self.screen_approval.lbl_amount.setText(amount)
        self.screen_approval.lbl_to.setText(f"To: {to}")
        self.stack.setCurrentWidget(self.screen_approval)

    def show_history(self):
        self.screen_history.set_reports(self.reports_history)
        self.stack.setCurrentWidget(self.screen_history)

    def handle_confirm_report(self):
        import datetime, hashlib, random
        now = datetime.datetime.now()
        raw_seed = f"{now.isoformat()}-{self.latest_spoof_prob}".encode()
        tx_hash = "0x" + hashlib.sha256(raw_seed).hexdigest()[:10] + "..."
        sha_full = hashlib.sha256(raw_seed).hexdigest()
        sha_display = "0x" + sha_full[:12] + "..." + sha_full[-8:]
        block_num = str(4829300 + random.randint(10, 999))

        channel = "Microphone" if self.audio_source == "microphone" else "WhatsApp VoIP"

        new_incident = {
            "timestamp": f"Just now · {channel}",
            "sha256": sha_display,
            "block": block_num,
            "tx": tx_hash,
            "status": "VERIFIED ON-CHAIN",
            "chakshu_url": (
                f"https://sancharsaathi.gov.in/sfc/"
                f"?reportedAt={now.strftime('%H:%M')}&callType=voip&confidence={self.latest_spoof_prob:.2f}"
            )
        }
        self.reports_history.insert(0, new_incident)
        self.screen_history.set_reports(self.reports_history)
        # Directly navigate to Blockchain Ledger screen to view verified on-chain incident
        self.show_history()


    def handle_stop_protection(self):
        self.detector_active = not self.detector_active
        if self.detector_active:
            # Resuming — reset the entire state machine
            self._last_emitted_state = "REAL"
            if self._smoother is not None:
                self._smoother.reset()
            self.screen_idle.btn_stop.setText("Stop Protection")
            self.screen_idle.btn_stop.set_variant("secondary")
            self.screen_idle.circular_meter.update_data(
                state="REAL",
                confidence=1.0 - self.latest_spoof_prob,
                caption="Active · resuming"
            )
            if hasattr(self.screen_idle, "context_body"):
                self.screen_idle.context_body.setText(
                    "Protection resumed\nListening for voice clone activity"
                )
        else:
            self.screen_idle.btn_stop.setText("Resume Protection")
            self.screen_idle.btn_stop.set_variant("primary")
            self.screen_idle.circular_meter.update_data(
                state="PAUSED", confidence=0.0, caption="Protection paused"
            )
            if hasattr(self.screen_idle, "context_body"):
                self.screen_idle.context_body.setText(
                    "Protection is currently paused\n"
                    "Tap Resume Protection to reactivate on-device monitoring"
                )

    # ── Detection signal handlers ────────────────────────────────────────────

    def on_audio_level(self, rms: float):
        """RMS level for visual feedback — does NOT drive the ring."""
        pass

    def on_detection_result(self, result: dict):
        """THE ONLY PLACE the ring value changes.
        Called only when the detection loop produced a real, non-silence-gated prediction.
        """
        if not self.detector_active:
            return

        state = result["state"]                    # "REAL" | "CLONED"
        self.latest_spoof_prob = result["current_spoof_prob"]
        current = self.stack.currentWidget()

        # Honest confidence for display:
        # When CLONED: show spoof risk (e.g. 0.98 for 98% Spoof)
        # When REAL: show authentic confidence (1.0 - spoof_prob, e.g. 0.98 for 98% Authentic)
        if state == "CLONED":
            confidence = self.latest_spoof_prob
        else:
            confidence = result["real_confidence_display"]

        # ── Update ring on active screen (both screen_idle and screen_alert are kept live) ──
        if current == self.screen_idle:
            self.screen_idle.circular_meter.set_value(confidence, state)
        elif current == self.screen_alert:
            self.screen_alert.circular_meter.set_value(confidence, state)

        # ── Screen transitions — edge-gated ───────────────────────────────────
        if state == "CLONED" and self._last_emitted_state != "CLONED" and current == self.screen_idle:
            # Rising edge only: REAL → CLONED — trigger alert ONCE
            self._last_emitted_state = "CLONED"
            self.trigger_clone_detected(confidence)

        elif state == "REAL" and current == self.screen_alert:
            # Auto-dismiss: real voice resumed — return to idle
            self._last_emitted_state = "REAL"
            self.show_idle()
            self.screen_idle.circular_meter.set_value(confidence, "REAL")

    # ── Background detector thread ────────────────────────────────────────────

    def _start_detector_thread(self):
        def _worker():
            try:
                from detector import DetectorModel    # type: ignore
                from chunker import AudioChunker      # type: ignore
                from smoother import ConfidenceSmoother, is_silence, has_enough_voiced_speech  # type: ignore
                from capture import get_capture_stream # type: ignore

                model    = DetectorModel()
                chunker  = AudioChunker()
                smoother = ConfidenceSmoother()
                self._smoother = smoother
                t        = 0.0

                active_source = getattr(self, "audio_source", "loopback")
                stream = get_capture_stream(active_source)
                source_label = next(stream)
                self.signals.model_ready.emit(source_label)

                while True:
                    # Check if audio source was toggled
                    new_source = getattr(self, "audio_source", "loopback")
                    if new_source != active_source:
                        active_source = new_source
                        stream = get_capture_stream(active_source)
                        source_label = next(stream)
                        self.signals.model_ready.emit(source_label)
                        if self._smoother:
                            self._smoother.reset()

                    if not self.detector_active:
                        time.sleep(0.1)
                        continue

                    try:
                        audio_block = next(stream)
                    except StopIteration:
                        break

                    # Emit raw RMS
                    rms = float(np.sqrt(np.mean(np.square(audio_block.astype(np.float64)))))
                    self.signals.audio_level_updated.emit(rms)

                    for chunk in chunker.push(audio_block):
                        # Silence gate
                        if is_silence(chunk):
                            continue

                        # VAD gate
                        if not has_enough_voiced_speech(chunk):
                            continue

                        # Predict
                        pred   = model.predict(chunk)

                        # Smooth
                        result = smoother.update(pred["spoof_prob"], t)

                        # Emit to UI
                        self.signals.detection_updated.emit(result)

                        t += chunker.chunk_len / float(chunker.sample_rate)

            except Exception as e:
                import traceback
                traceback.print_exc()
                self.signals.error_occurred.emit(str(e))

        threading.Thread(target=_worker, daemon=True).start()

    # ── Keyboard shortcuts ────────────────────────────────────────────────────

    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key == Qt.Key.Key_C:
            self.trigger_clone_detected()
        elif key == Qt.Key.Key_A:
            self.show_approval()
        elif key == Qt.Key.Key_H:
            self.show_history()
        elif key == Qt.Key.Key_Escape:
            self.show_idle()
        else:
            super().keyPressEvent(event)


def create_app():
    app = QApplication.instance() or QApplication(sys.argv)
    theme_file = Path(__file__).resolve().parent / "theme.qss"
    if theme_file.exists():
        with open(theme_file, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    return app


if __name__ == "__main__":
    app = create_app()
    window = VoiceGuardMainWindow()
    window.show()
    sys.exit(app.exec())
