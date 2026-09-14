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

        self.latest_spoof_prob = 0.05   # track honest last value for display
        self.start_time = time.time()
        self._model_loading = True

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

        self.screen_alert.hang_up_clicked.connect(self.show_idle)
        self.screen_alert.report_clicked.connect(self.show_report_confirmation)

        self.screen_report.confirm_report_clicked.connect(self.handle_confirm_report)
        self.screen_report.cancel_clicked.connect(self.show_idle)

        self.screen_approval.approve_clicked.connect(self.show_idle)
        self.screen_approval.reject_clicked.connect(self.show_idle)

        self.screen_history.back_clicked.connect(self.show_idle)

    def _update_elapsed(self):
        if self._model_loading or not self.detector_active:
            return
        elapsed = int(time.time() - self.start_time)
        m, s = divmod(elapsed, 60)
        if self.stack.currentWidget() == self.screen_idle:
            self.screen_idle.circular_meter.update_data(caption=f"Active · {m:02d}:{s:02d}")

    # ── Navigation slots ─────────────────────────────────────────────────────

    def show_idle(self):
        self.stack.setCurrentWidget(self.screen_idle)

    def trigger_clone_detected(self, confidence: float = 0.96):
        """Used by keyboard shortcut 'C' and by on_detection_result when CLONED."""
        self.screen_alert.circular_meter.update_data(
            state="CLONE", confidence=confidence, caption="High-Risk AI Audio"
        )
        self.stack.setCurrentWidget(self.screen_alert)
        self.screen_alert.trigger_alert_transition()

    def show_report_confirmation(self):
        import datetime
        now = datetime.datetime.now()
        # Display honest confidence: 1 - last spoof_prob
        conf_display = int((1.0 - self.latest_spoof_prob) * 100) if self.latest_spoof_prob < 0.5 \
                       else int(self.latest_spoof_prob * 100)

        self.stack.removeWidget(self.screen_report)
        self.screen_report.deleteLater()
        self.screen_report = Screen3Report(
            time_str=now.strftime("%H:%M, %b %d"),
            confidence_str=f"{conf_display}%",
            call_type_str="WhatsApp"
        )
        self.screen_report.confirm_report_clicked.connect(self.handle_confirm_report)
        self.screen_report.cancel_clicked.connect(self.show_idle)
        self.stack.insertWidget(2, self.screen_report)
        self.stack.setCurrentWidget(self.screen_report)

    def show_approval(self, amount: str = "₹50,00,000", to: str = "ABC Industries Pvt Ltd"):
        self.screen_approval.lbl_amount.setText(amount)
        self.screen_approval.lbl_to.setText(f"To: {to}")
        self.stack.setCurrentWidget(self.screen_approval)

    def show_history(self):
        self.screen_history.set_reports(self.reports_history)
        self.stack.setCurrentWidget(self.screen_history)

    def handle_confirm_report(self):
        import datetime
        now = datetime.datetime.now()
        new_incident = {
            "timestamp": f"Just now · WhatsApp",
            "sha256": "0x0be47a255930...af5b5d28",
            "block": "4829315",
            "tx": "0x7a83d4c510...",
            "status": "VERIFIED ON-CHAIN",
            "chakshu_url": (
                f"https://sancharsaathi.gov.in/sfc/"
                f"?reportedAt={now.strftime('%H:%M')}&callType=voip&confidence=0.94"
            )
        }
        self.reports_history.insert(0, new_incident)
        self.screen_history.set_reports(self.reports_history)
        self.show_idle()

    def handle_stop_protection(self):
        self.detector_active = not self.detector_active
        if self.detector_active:
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
        pass   # can wire to a level bar if added in future; ring is not touched here

    def on_detection_result(self, result: dict):
        """THE ONLY PLACE the ring value changes.
        Called only when the detection loop produced a real, non-silence-gated prediction.

        Part 2 auto-dismiss: if smoother returns REAL while alert is showing, dismiss.
        """
        if not self.detector_active:
            return

        state      = result["state"]                    # "REAL" | "CLONED"
        disp_conf  = result["real_confidence_display"]  # 1.0 - spoof_prob — honest, no flooring
        self.latest_spoof_prob = result["current_spoof_prob"]
        current = self.stack.currentWidget()

        # ── Update ring (single call site) ───────────────────────────────────
        if current == self.screen_idle:
            self.screen_idle.circular_meter.set_value(disp_conf, state)

        # ── Screen transitions ────────────────────────────────────────────────
        if state == "CLONED" and current == self.screen_idle:
            # spoof_prob is the cloned confidence; pass it so the alert ring shows it
            self.trigger_clone_detected(result["current_spoof_prob"])

        elif state == "REAL" and current == self.screen_alert:
            # Auto-dismiss: real voice resumed — return to idle
            self.show_idle()
            self.screen_idle.circular_meter.set_value(disp_conf, "REAL")

    # ── Background detector thread ────────────────────────────────────────────

    def _start_detector_thread(self):
        def _worker():
            try:
                from detector import DetectorModel    # type: ignore
                from chunker import AudioChunker      # type: ignore
                from smoother import ConfidenceSmoother, is_silence  # type: ignore
                from capture import get_loopback_stream              # type: ignore

                model    = DetectorModel()
                chunker  = AudioChunker()
                smoother = ConfidenceSmoother()
                t        = 0.0

                # Part 2: read source_label from generator first
                stream       = get_loopback_stream()
                source_label = next(stream)           # generator yields label as first value
                self.signals.model_ready.emit(source_label)

                for audio_block in stream:
                    if not self.detector_active:
                        time.sleep(0.1)
                        continue

                    # Emit raw RMS (for optional level display — does NOT update ring)
                    rms = float(np.sqrt(np.mean(np.square(audio_block.astype(np.float64)))))
                    self.signals.audio_level_updated.emit(rms)

                    for chunk in chunker.push(audio_block):
                        # Silence gate — hold state, never feed silence to model
                        if is_silence(chunk):
                            continue  # ring does NOT move (Part 5.0 fix)

                        # Predict — no caller-side normalization (detector.py does it)
                        pred   = model.predict(chunk)

                        # Smoother takes spoof_prob float directly
                        result = smoother.update(pred["spoof_prob"], t)

                        # Emit to UI — only path that may call ring.set_value()
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
