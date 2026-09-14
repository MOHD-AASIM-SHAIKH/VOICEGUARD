"""VoiceGuard Reusable UI Components.
Desktop PySide6 implementation conforming to design tokens (tokens.py).

RING IDLE-MOVEMENT FIX (Part 5.0):
  The previous CircularConfidenceMeter used a 40ms QTimer that continuously animated
  the arc even with no audio playing (ambient/idle drift). This violated the spec:
  the ring must be completely static during silence.

  ConfidenceRing now has NO internal timer. set_value() is the ONLY entry point for
  value changes, and it must be called exclusively from on_detection_result(), which
  is itself only called when a non-silence-gated chunk has been inferred.

  During silence:
    - The detection loop skips predict() and smoother.update()
    - No result is emitted
    - on_detection_result() is never called
    - set_value() is never called
    - The ring holds its exact last rendered position — static, correct, honest.
"""
import math
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QPushButton, QVBoxLayout, QHBoxLayout
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Signal, QRectF, Property
from PySide6.QtGui import QFont, QCursor, QPainter, QPen, QColor, QBrush

import tokens


# ── Part 5.1: ConfidenceRing ─────────────────────────────────────────────────

COLOR_BORDER         = QColor("#E3E3E0")
COLOR_REAL           = QColor("#3F7D5C")   # Emerald green — real/bonafide
COLOR_CLONE          = QColor("#A8453F")   # Crimson red — spoof/cloned
COLOR_TEXT_PRIMARY   = QColor("#1A1A1A")
COLOR_TEXT_SECONDARY = QColor("#6B6B68")


class ConfidenceRing(QWidget):
    """Circular confidence arc — Part 5.1 robust spec.

    NO internal QTimer. Ring is static during silence. Only set_value() may
    change the displayed value, and set_value() is called exclusively from
    on_detection_result() in the main window when new predictions arrive.

    set_value() uses QPropertyAnimation for smooth visual transition (350ms
    ease-out) when a new prediction arrives, then holds that position until
    the next call.
    """

    def __init__(self, state: str = "REAL", confidence: float = 0.0,
                 caption: str = "", parent=None):
        super().__init__(parent)
        self.setFixedSize(240, 240)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")

        self._confidence  = max(0.0, min(1.0, float(confidence)))
        self._state       = state.upper()
        self._caption     = caption

        # Smooth transition animation — only fires on prediction update
        self._anim = QPropertyAnimation(self, b"confidenceProp")
        self._anim.setDuration(350)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Backwards-compatibility shims so existing screen code keeps working
        self.caption_label = _DummyPropertyLabel(
            lambda: self._caption,
            lambda t: self.set_caption(t)
        )
        self.state_label = _DummyPropertyLabel(
            lambda: self._state,
            lambda t: self.update_state(t)
        )

    # ── Qt property for animation ────────────────────────────────────────────

    def _get_confidence(self) -> float:
        return self._confidence

    def _set_confidence(self, value: float):
        self._confidence = max(0.0, min(1.0, float(value)))
        self.update()   # repaint with new interpolated value

    confidenceProp = Property(float, _get_confidence, _set_confidence)

    # ── Public API ───────────────────────────────────────────────────────────

    def set_value(self, confidence: float, state: str):
        """THE PRIMARY WAY this ring's value updates.
        Smoothly animates arc to the new confidence value.
        """
        self._state = state.upper()
        target = max(0.0, min(1.0, float(confidence)))
        self._anim.stop()
        self._anim.setStartValue(self._confidence)
        self._anim.setEndValue(target)
        self._anim.start()

    def set_caption(self, caption: str):
        """Update caption (e.g. elapsed time) without disrupting running animations."""
        if self._caption != caption:
            self._caption = caption
            self.update()

    def update_data(self, state: str = None, confidence: float = None, caption: str = None):
        """Backwards-compatible updater used by screen init code and loading indicator."""
        if state is not None:
            self._state = state.upper()
        if caption is not None:
            self._caption = caption
        if confidence is not None:
            target = max(0.0, min(1.0, float(confidence)))
            self._anim.stop()
            self._anim.setStartValue(self._confidence)
            self._anim.setEndValue(target)
            self._anim.start()
        else:
            self.update()

    def update_state(self, state: str, caption: str = None):
        self.update_data(state=state, caption=caption)

    def set_audio_level(self, level: float):
        """No-op: ring is static during silence."""
        pass

    def closeEvent(self, event):
        self._anim.stop()
        super().closeEvent(event)

    # ── Painting ─────────────────────────────────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self.width())
        h = float(self.height())
        stroke = 12.0
        diameter = 188.0
        rect = QRectF((w - diameter) / 2.0, (h - diameter) / 2.0, diameter, diameter)

        # 1. Background track
        track_pen = QPen(COLOR_BORDER, stroke)
        track_pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setPen(track_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(rect, 0, 360 * 16)

        # 2. Determine state colors & typography
        if self._state in ("CLONE", "CLONED"):
            arc_color = COLOR_CLONE
            line1     = "CLONE"
            line2     = "DETECTED"
            pct_text  = f"{int(round(self._confidence * 100))}% Spoof"
        elif self._state == "PAUSED":
            arc_color = QColor("#9CA3AF")
            line1     = "PAUSED"
            line2     = ""
            pct_text  = "Monitoring Off"
        else:  # REAL / loading
            arc_color = COLOR_REAL
            line1     = "REAL"
            line2     = ""
            if self._confidence < 0.01:
                pct_text = "Starting…"
            else:
                pct_text = f"{int(round(self._confidence * 100))}% Authentic"

        # 3. Progress arc — only draw if meaningful confidence and not paused
        if self._state != "PAUSED" and self._confidence > 0.01:
            if self._confidence >= 0.999:
                # Full 360 ring: draw seamless full circle (avoids round-cap collision)
                arc_pen = QPen(arc_color, stroke)
                arc_pen.setCapStyle(Qt.PenCapStyle.FlatCap)
                painter.setPen(arc_pen)
                painter.drawArc(rect, 0, 360 * 16)
            else:
                # Partial arc: start at 12 o'clock (90 deg), sweep clockwise (-span)
                arc_pen = QPen(arc_color, stroke)
                arc_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(arc_pen)
                span = int(self._confidence * 360.0 * 16.0)
                painter.drawArc(rect, 90 * 16, -span)

        # 4. Text layout — perfectly centered inside inner circle
        cx = w / 2.0
        cy = h / 2.0
        TW = 148.0
        TX = cx - TW / 2.0

        font_family = "Segoe UI"
        font_state = QFont(font_family)
        font_state.setPointSize(14)
        font_state.setWeight(QFont.Weight.Bold)
        painter.setFont(font_state)
        painter.setPen(arc_color)

        if line2:
            painter.drawText(
                QRectF(TX, cy - 34, TW, 24),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                line1
            )
            painter.drawText(
                QRectF(TX, cy - 10, TW, 24),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                line2
            )
            pct_y = cy + 18
            cap_y = cy + 40
        else:
            painter.drawText(
                QRectF(TX, cy - 22, TW, 26),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                line1
            )
            pct_y = cy + 8
            cap_y = cy + 30

        # Percentage text
        font_val = QFont(font_family)
        font_val.setPointSize(10)
        font_val.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font_val)
        painter.setPen(COLOR_TEXT_SECONDARY)
        painter.drawText(
            QRectF(TX, pct_y, TW, 18),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            pct_text
        )

        # Caption text
        if self._caption:
            font_cap = QFont(font_family)
            font_cap.setPointSize(8)
            font_cap.setWeight(QFont.Weight.Normal)
            painter.setFont(font_cap)
            painter.setPen(QColor("#8E8E93"))
            painter.drawText(
                QRectF(TX, cap_y, TW, 16),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                self._caption
            )

        painter.end()


# Backwards-compatibility alias: existing screens reference CircularConfidenceMeter
CircularConfidenceMeter = ConfidenceRing


# ── _DummyPropertyLabel helper ────────────────────────────────────────────────

class _DummyPropertyLabel:
    def __init__(self, get_fn, set_fn):
        self._get_fn = get_fn
        self._set_fn = set_fn
    def text(self):
        return self._get_fn()
    def setText(self, text):
        self._set_fn(text)


# ── StatusIndicator (legacy fallback) ────────────────────────────────────────

class StatusIndicator(QFrame):
    """Legacy block indicator. Kept for backwards compatibility only."""
    def __init__(self, state="REAL", caption="Listening to call audio", parent=None):
        super().__init__(parent)
        self.state = state
        self.caption_text = caption

        layout = QVBoxLayout(self)
        layout.setContentsMargins(tokens.SPACE_5, tokens.SPACE_6, tokens.SPACE_5, tokens.SPACE_6)
        layout.setSpacing(tokens.SPACE_2)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.state_label = QLabel()
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_state = QFont("Inter")
        font_state.setPixelSize(tokens.TEXT_DISPLAY["size"])
        font_state.setWeight(QFont.Weight.Bold)
        self.state_label.setFont(font_state)

        self.caption_label = QLabel()
        self.caption_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_cap = QFont("Inter")
        font_cap.setPixelSize(tokens.TEXT_CAPTION["size"])
        self.caption_label.setFont(font_cap)
        self.caption_label.setStyleSheet(f"color: {tokens.COLOR_TEXT_SECONDARY};")

        layout.addWidget(self.state_label)
        layout.addWidget(self.caption_label)
        self.update_state(state, caption)

    def update_state(self, state: str, caption: str = None):
        self.state = state.upper()
        if caption is not None:
            self.caption_text = caption
            self.caption_label.setText(self.caption_text)
        if self.state == "REAL":
            self.setStyleSheet(
                f"background-color: {tokens.COLOR_STATE_REAL_BG}; "
                f"border-radius: {tokens.RADIUS}px;"
            )
            self.state_label.setStyleSheet(f"color: {tokens.COLOR_STATE_REAL};")
            self.state_label.setText("REAL")
        else:
            self.setStyleSheet(
                f"background-color: {tokens.COLOR_STATE_CLONE_BG}; "
                f"border-radius: {tokens.RADIUS}px;"
            )
            self.state_label.setStyleSheet(f"color: {tokens.COLOR_STATE_CLONE};")
            self.state_label.setText("CLONE DETECTED")


# ── VoiceGuardButton ──────────────────────────────────────────────────────────

class VoiceGuardButton(QPushButton):
    """Primary: dark bg, white text. Secondary: transparent bg, bordered."""
    def __init__(self, text: str, variant: str = "primary", parent=None):
        super().__init__(text, parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        font = QFont("Inter")
        font.setPixelSize(tokens.TEXT_LABEL["size"])
        font.setWeight(QFont.Weight.Medium)
        self.setFont(font)
        self.set_variant(variant)

    def set_variant(self, variant: str):
        if variant == "primary":
            self.setObjectName("primaryButton")
            self.setStyleSheet(
                f"QPushButton {{"
                f"  background-color: {tokens.COLOR_TEXT_PRIMARY};"
                f"  color: #FFFFFF;"
                f"  border-radius: {tokens.RADIUS}px;"
                f"  padding: {tokens.SPACE_3}px {tokens.SPACE_5}px;"
                f"  border: {tokens.BORDER_WIDTH}px solid {tokens.COLOR_TEXT_PRIMARY};"
                f"}}"
                f"QPushButton:hover {{ background-color: #2E2E2E; }}"
                f"QPushButton:pressed {{ background-color: #000000; }}"
                f"QPushButton:focus {{ border: {tokens.BORDER_WIDTH}px solid {tokens.COLOR_TEXT_PRIMARY}; }}"
            )
        else:
            self.setObjectName("secondaryButton")
            self.setStyleSheet(
                f"QPushButton {{"
                f"  background-color: transparent;"
                f"  color: {tokens.COLOR_TEXT_PRIMARY};"
                f"  border-radius: {tokens.RADIUS}px;"
                f"  padding: {tokens.SPACE_3}px {tokens.SPACE_5}px;"
                f"  border: {tokens.BORDER_WIDTH}px solid {tokens.COLOR_BORDER};"
                f"}}"
                f"QPushButton:hover {{ background-color: {tokens.COLOR_SURFACE}; }}"
                f"QPushButton:pressed {{ background-color: #EAEAE6; }}"
                f"QPushButton:focus {{ border: {tokens.BORDER_WIDTH}px solid {tokens.COLOR_TEXT_PRIMARY}; }}"
            )


# ── VoiceGuardCard ────────────────────────────────────────────────────────────

class VoiceGuardCard(QFrame):
    """Surface card: light background, 1px border, radius, padding."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("cardWidget")
        self.setStyleSheet(
            f"QFrame#cardWidget {{"
            f"  background-color: {tokens.COLOR_SURFACE};"
            f"  border: {tokens.BORDER_WIDTH}px solid {tokens.COLOR_BORDER};"
            f"  border-radius: {tokens.RADIUS}px;"
            f"}}"
        )
        self.card_layout = QVBoxLayout(self)
        self.card_layout.setContentsMargins(tokens.SPACE_5, tokens.SPACE_5, tokens.SPACE_5, tokens.SPACE_5)
        self.card_layout.setSpacing(tokens.SPACE_3)


# ── ListRow ───────────────────────────────────────────────────────────────────

class ListRow(QFrame):
    """Left: body text. Right: caption text. Bottom border unless last."""
    clicked = Signal()

    def __init__(self, primary_text: str, secondary_text: str,
                 is_last: bool = False, parent=None):
        super().__init__(parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        border_style = (
            "border: none;" if is_last
            else f"border-bottom: {tokens.BORDER_WIDTH}px solid {tokens.COLOR_BORDER};"
        )
        self.setStyleSheet(f"QFrame {{ background-color: transparent; {border_style} }}")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(tokens.SPACE_5, tokens.SPACE_4, tokens.SPACE_5, tokens.SPACE_4)

        self.left_label = QLabel(primary_text)
        font_body = QFont("Inter")
        font_body.setPixelSize(tokens.TEXT_BODY["size"])
        font_body.setWeight(QFont.Weight.Normal)
        self.left_label.setFont(font_body)
        self.left_label.setStyleSheet(f"color: {tokens.COLOR_TEXT_PRIMARY}; border: none;")

        self.right_label = QLabel(secondary_text)
        font_cap = QFont("Inter")
        font_cap.setPixelSize(tokens.TEXT_CAPTION["size"])
        self.right_label.setFont(font_cap)
        self.right_label.setStyleSheet(f"color: {tokens.COLOR_TEXT_SECONDARY}; border: none;")

        layout.addWidget(self.left_label)
        layout.addStretch()
        layout.addWidget(self.right_label)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)
