"""Screen 1 — Idle / Listening.
PySide6 Desktop Implementation strictly per Part 3 Screen 1 spec.
Includes Circular Radial Confidence Meter and novelty feature tray matching mobile app.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpacerItem, QSizePolicy, QPushButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import tokens
from components import CircularConfidenceMeter, VoiceGuardButton, VoiceGuardCard

class Screen1Listening(QWidget):
    stop_protection_clicked = Signal()
    simulate_clone_clicked = Signal()
    guarded_tx_clicked = Signal()
    blockchain_ledger_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("screen1")
        self.setStyleSheet(f"background-color: {tokens.COLOR_BG};")
        
        # Root layout with center-aligned column (max-width 480px)
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Center column container
        self.column = QWidget()
        self.column.setMaximumWidth(480)
        self.column.setObjectName("centerColumn")
        
        col_layout = QVBoxLayout(self.column)
        col_layout.setContentsMargins(tokens.SPACE_5, tokens.SPACE_6, tokens.SPACE_5, tokens.SPACE_6)
        col_layout.setSpacing(0)
        
        # Top Blockchain Trust Badge
        self.badge_label = QLabel("⛓️ Polygon Amoy Notary Active")
        font_badge = QFont("Inter")
        font_badge.setPixelSize(12)
        font_badge.setWeight(QFont.Weight.Medium)
        self.badge_label.setFont(font_badge)
        self.badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge_label.setStyleSheet(
            "color: #4F46E5; background-color: #EEF2FF; border-radius: 12px; padding: 4px 12px; border: 1px solid #C7D2FE;"
        )
        badge_row = QHBoxLayout()
        badge_row.addStretch()
        badge_row.addWidget(self.badge_label)
        badge_row.addStretch()
        col_layout.addLayout(badge_row)
        col_layout.addSpacing(tokens.SPACE_4)
        
        # 1. Circular Confidence Meter (matching mobile app)
        self.circular_meter = CircularConfidenceMeter("REAL", 0.95, "Active · 00:00")
        self.status_indicator = self.circular_meter # Backwards-compatibility alias for test assertions
        
        meter_row = QHBoxLayout()
        meter_row.addStretch()
        meter_row.addWidget(self.circular_meter)
        meter_row.addStretch()
        col_layout.addLayout(meter_row)
        
        col_layout.addSpacing(tokens.SPACE_5)
        
        # 2. Card: Call Context
        self.context_card = VoiceGuardCard()
        
        title = QLabel("Call Context")
        font_sub = QFont("Inter")
        font_sub.setPixelSize(tokens.TEXT_SUBTITLE["size"])
        font_sub.setWeight(QFont.Weight.DemiBold)
        title.setFont(font_sub)
        title.setStyleSheet(f"color: {tokens.COLOR_TEXT_PRIMARY}; border: none;")
        
        self.context_body = QLabel("Active · Ready to protect calls (Cellular / WhatsApp / VoIP) · 00:00\nProtected by VoiceGuard on-device model + On-Chain Interceptor")
        font_body = QFont("Inter")
        font_body.setPixelSize(tokens.TEXT_BODY["size"])
        font_body.setWeight(QFont.Weight.Normal)
        self.context_body.setFont(font_body)
        self.context_body.setStyleSheet(f"color: {tokens.COLOR_TEXT_SECONDARY}; border: none;")
        
        self.context_card.card_layout.addWidget(title)
        self.context_card.card_layout.addWidget(self.context_body)
        col_layout.addWidget(self.context_card)
        
        # Flex-grow spacer
        col_layout.addSpacerItem(QSpacerItem(20, 30, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Novelty tray label
        lbl_novelty = QLabel("Novelty Features & Simulation")
        lbl_novelty.setFont(font_badge)
        lbl_novelty.setStyleSheet(f"color: {tokens.COLOR_TEXT_SECONDARY}; border: none;")
        col_layout.addWidget(lbl_novelty)
        col_layout.addSpacing(tokens.SPACE_2)
        
        # Novelty buttons row
        novelty_row = QHBoxLayout()
        novelty_row.setSpacing(8)
        
        btn_sim = QPushButton("Simulate Clone")
        btn_sim.setStyleSheet("background: transparent; color: #DC2626; border: none; font-weight: 500; font-size: 13px; text-align: left; padding: 4px;")
        btn_sim.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_sim.clicked.connect(self.simulate_clone_clicked.emit)
        novelty_row.addWidget(btn_sim)
        
        btn_guard = QPushButton("Guarded Tx")
        btn_guard.setStyleSheet(f"background: transparent; color: {tokens.COLOR_TEXT_PRIMARY}; border: none; font-weight: 500; font-size: 13px; padding: 4px;")
        btn_guard.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_guard.clicked.connect(self.guarded_tx_clicked.emit)
        novelty_row.addWidget(btn_guard)
        
        btn_ledger = QPushButton("Blockchain Ledger")
        btn_ledger.setStyleSheet(f"background: transparent; color: {tokens.COLOR_TEXT_PRIMARY}; border: none; font-weight: 500; font-size: 13px; padding: 4px;")
        btn_ledger.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ledger.clicked.connect(self.blockchain_ledger_clicked.emit)
        novelty_row.addWidget(btn_ledger)
        
        col_layout.addLayout(novelty_row)
        col_layout.addSpacing(tokens.SPACE_3)
        
        # 3. Button: Stop Protection (secondary/outlined, bottom)
        self.btn_stop = VoiceGuardButton("Stop Protection", variant="secondary")
        self.btn_stop.clicked.connect(self.stop_protection_clicked.emit)
        col_layout.addWidget(self.btn_stop)
        
        root_layout.addWidget(self.column)
