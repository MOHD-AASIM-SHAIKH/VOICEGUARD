"""Screen 4 — Trusted-Device Transaction Approval (Tier 2 Smart Contract Guard).
PySide6 Desktop Implementation strictly per Part 3 Screen 4 spec.
Displays TransactionAuthorizer.sol context and cryptographic multi-sig requirement.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import tokens
from components import VoiceGuardButton, VoiceGuardCard

class Screen4Approval(QWidget):
    approve_clicked = Signal()
    reject_clicked = Signal()

    def __init__(self, amount_str="₹50,00,000", to_str="ABC Industries Pvt Ltd", parent=None):
        super().__init__(parent)
        self.setObjectName("screen4")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"QWidget#screen4 {{ background-color: {tokens.COLOR_BG}; }}")
        
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
        
        # Blockchain Badge
        badge_label = QLabel("⛓️ TransactionAuthorizer.sol · Polygon")
        font_badge = QFont("Inter")
        font_badge.setPixelSize(12)
        font_badge.setWeight(QFont.Weight.Medium)
        badge_label.setFont(font_badge)
        badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge_label.setStyleSheet(
            "color: #4F46E5; background-color: #EEF2FF; border-radius: 12px; padding: 4px 12px; border: 1px solid #C7D2FE;"
        )
        badge_row = QHBoxLayout()
        badge_row.addStretch()
        badge_row.addWidget(badge_label)
        badge_row.addStretch()
        col_layout.addLayout(badge_row)
        col_layout.addSpacing(tokens.SPACE_3)
        
        # 1. Label: "Guarded Transaction Intercepted"
        self.lbl_requested = QLabel("Guarded Transaction Intercepted")
        font_label = QFont("Inter")
        font_label.setPixelSize(tokens.TEXT_LABEL["size"])
        font_label.setWeight(QFont.Weight.Medium)
        self.lbl_requested.setFont(font_label)
        self.lbl_requested.setStyleSheet("color: #DC2626; border: none;")
        col_layout.addWidget(self.lbl_requested)
        col_layout.addSpacing(tokens.SPACE_2)
        
        # 2. Amount: "₹50,00,000"
        self.lbl_amount = QLabel(amount_str)
        font_display = QFont("Inter")
        font_display.setPixelSize(tokens.TEXT_DISPLAY["size"])
        font_display.setWeight(QFont.Weight.Bold)
        self.lbl_amount.setFont(font_display)
        self.lbl_amount.setStyleSheet(f"color: {tokens.COLOR_TEXT_PRIMARY}; border: none;")
        col_layout.addWidget(self.lbl_amount)
        
        # To: "ABC Industries Pvt Ltd"
        self.lbl_to = QLabel(f"To: {to_str}")
        font_sub = QFont("Inter")
        font_sub.setPixelSize(tokens.TEXT_SUBTITLE["size"])
        font_sub.setWeight(QFont.Weight.DemiBold)
        self.lbl_to.setFont(font_sub)
        self.lbl_to.setStyleSheet(f"color: {tokens.COLOR_TEXT_PRIMARY}; border: none;")
        col_layout.addWidget(self.lbl_to)
        
        col_layout.addSpacing(tokens.SPACE_5)
        
        # 3. Card: risk context
        self.risk_card = VoiceGuardCard()
        lbl_risk_title = QLabel("On-Chain Interceptor Context")
        lbl_risk_title.setFont(font_sub)
        lbl_risk_title.setStyleSheet(f"color: {tokens.COLOR_TEXT_PRIMARY}; border: none;")
        
        lbl_risk_body = QLabel(
            "Status: PENDING_STEP_UP\n"
            "Reason: VoiceGuard AI detected clone activity on active WhatsApp call.\n"
            "Smart Contract: 0x89205A...c43e7\n"
            "Multi-sig consensus locked pending device biometric authorization."
        )
        font_body = QFont("Inter")
        font_body.setPixelSize(tokens.TEXT_BODY["size"])
        font_body.setWeight(QFont.Weight.Normal)
        lbl_risk_body.setFont(font_body)
        lbl_risk_body.setStyleSheet(f"color: {tokens.COLOR_TEXT_SECONDARY}; border: none;")
        
        self.risk_card.card_layout.addWidget(lbl_risk_title)
        self.risk_card.card_layout.addWidget(lbl_risk_body)
        col_layout.addWidget(self.risk_card)
        col_layout.addSpacing(tokens.SPACE_4)
        
        # 4. Biometric prompt
        self.bio_card = VoiceGuardCard()
        lbl_bio_title = QLabel("Biometric Step-Up Authorization")
        lbl_bio_title.setFont(font_label)
        lbl_bio_title.setStyleSheet(f"color: {tokens.COLOR_TEXT_PRIMARY}; border: none;")
        
        lbl_bio_desc = QLabel("Touch fingerprint sensor / security key to sign and unfreeze funds on Polygon ledger.")
        font_caption = QFont("Inter")
        font_caption.setPixelSize(tokens.TEXT_CAPTION["size"])
        lbl_bio_desc.setFont(font_caption)
        lbl_bio_desc.setStyleSheet(f"color: {tokens.COLOR_TEXT_SECONDARY}; border: none;")
        
        self.bio_card.card_layout.addWidget(lbl_bio_title)
        self.bio_card.card_layout.addWidget(lbl_bio_desc)
        col_layout.addWidget(self.bio_card)
        
        col_layout.addSpacerItem(QSpacerItem(20, 30, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # 5. Buttons
        self.btn_approve = VoiceGuardButton("Approve & Sign Transaction", variant="primary")
        self.btn_approve.clicked.connect(self.approve_clicked.emit)
        col_layout.addWidget(self.btn_approve)
        col_layout.addSpacing(tokens.SPACE_2)
        
        self.btn_reject = VoiceGuardButton("Reject & Maintain On-Chain Lock", variant="secondary")
        self.btn_reject.clicked.connect(self.reject_clicked.emit)
        col_layout.addWidget(self.btn_reject)
        
        root_layout.addWidget(self.column)
