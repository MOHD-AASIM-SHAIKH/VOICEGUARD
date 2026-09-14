"""Screen 2 — Clone Detected (Alert).
PySide6 Desktop Implementation strictly per Part 3 Screen 2 spec.
Features Circular Confidence Meter, Smart Contract Interceptor card, and animated background tint.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QVariantAnimation
from PySide6.QtGui import QColor, QFont

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import tokens
from components import CircularConfidenceMeter, VoiceGuardButton, VoiceGuardCard

class Screen2CloneAlert(QWidget):
    hang_up_clicked = Signal()
    report_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("screen2")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.current_bg = QColor(tokens.COLOR_STATE_CLONE_BG)
        self.setStyleSheet(f"QWidget#screen2 {{ background-color: {tokens.COLOR_STATE_CLONE_BG}; }}")

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.column = QWidget()
        self.column.setMaximumWidth(480)
        self.column.setObjectName("centerColumn")
        self.column.setStyleSheet("background: transparent;")
        
        col_layout = QVBoxLayout(self.column)
        col_layout.setContentsMargins(tokens.SPACE_5, tokens.SPACE_6, tokens.SPACE_5, tokens.SPACE_6)
        col_layout.setSpacing(0)
        
        # 1. Circular Confidence Meter (CLONE state)
        self.circular_meter = CircularConfidenceMeter("CLONE", 0.96, "High-Risk AI Audio")
        self.status_indicator = self.circular_meter # Backwards compatibility alias
        
        meter_row = QHBoxLayout()
        meter_row.addStretch()
        meter_row.addWidget(self.circular_meter)
        meter_row.addStretch()
        col_layout.addLayout(meter_row)
        
        col_layout.addSpacing(tokens.SPACE_5)
        
        # 2. Smart Contract Interceptor Card (matching mobile app)
        self.interceptor_card = VoiceGuardCard()
        
        title = QLabel("Smart Contract Interceptor")
        font_sub = QFont("Inter")
        font_sub.setPixelSize(tokens.TEXT_SUBTITLE["size"])
        font_sub.setWeight(QFont.Weight.DemiBold)
        title.setFont(font_sub)
        title.setStyleSheet("color: #991B1B; border: none;")
        
        body = QLabel("TransactionAuthorizer.sol activated: Pending banking transfers and high-value approvals automatically locked on-chain.")
        font_body = QFont("Inter")
        font_body.setPixelSize(tokens.TEXT_BODY["size"])
        font_body.setWeight(QFont.Weight.Normal)
        body.setFont(font_body)
        body.setWordWrap(True)
        body.setStyleSheet(f"color: {tokens.COLOR_TEXT_PRIMARY}; border: none;")
        
        self.interceptor_card.card_layout.addWidget(title)
        self.interceptor_card.card_layout.addWidget(body)
        col_layout.addWidget(self.interceptor_card)
        
        # Spacer
        col_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        col_layout.addSpacing(tokens.SPACE_4)
        
        # 3. Button: Hang Up Immediately (primary, full-width)
        self.btn_hangup = VoiceGuardButton("Hang Up Immediately", variant="primary")
        self.btn_hangup.clicked.connect(self.hang_up_clicked.emit)
        col_layout.addWidget(self.btn_hangup)
        
        col_layout.addSpacing(tokens.SPACE_3)
        
        # 4. Button: Report & Notarize on Blockchain (secondary/outlined, full-width)
        self.btn_report = VoiceGuardButton("Report & Notarize on Blockchain", variant="secondary")
        self.btn_report.clicked.connect(self.report_clicked.emit)
        col_layout.addWidget(self.btn_report)
        
        root_layout.addWidget(self.column)

    def trigger_alert_transition(self, on_finished=None):
        """Cross-fades background color from COLOR_BG to COLOR_STATE_CLONE_BG over 180ms ease-out."""
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(tokens.TRANSITION_DURATION_MS)
        self.anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.anim.setStartValue(QColor(tokens.COLOR_BG))
        self.anim.setEndValue(QColor(tokens.COLOR_STATE_CLONE_BG))
        
        def update_color(value: QColor):
            self.setStyleSheet(f"QWidget#screen2 {{ background-color: {value.name()}; }}")
            
        self.anim.valueChanged.connect(update_color)
        if on_finished:
            self.anim.finished.connect(on_finished)
        self.anim.start()
