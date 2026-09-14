"""Screen 3 — Report & Blockchain Notarization.
PySide6 Desktop Implementation strictly per Part 3 Screen 3 spec.
Includes canonical SHA-256 evidence hashing and Chakshu DoT fraud portal launching.
"""
import webbrowser
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpacerItem, QSizePolicy, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent / "reporting" / "evidence-hash"))
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent / "reporting" / "chakshu-link-builder"))

try:
    from hash import compute_evidence_hash
except ImportError:
    import hashlib, json
    def compute_evidence_hash(incident: dict) -> str:
        canonical = json.dumps(incident, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

try:
    from link import build_chakshu_link
except ImportError:
    from urllib.parse import urlencode
    def build_chakshu_link(incident: dict) -> str:
        return f"https://sancharsaathi.gov.in/sfc/?{urlencode({'reportedAt': incident.get('detectedAt', ''), 'callType': incident.get('callType', ''), 'confidence': incident.get('confidenceAtAlert', '')})}"

import tokens
from components import VoiceGuardButton, VoiceGuardCard

class Screen3Report(QWidget):
    confirm_report_clicked = Signal()
    cancel_clicked = Signal()

    def __init__(self, time_str="13:42, Sept 14", confidence_str="94%", call_type_str="WhatsApp", parent=None):
        super().__init__(parent)
        self.setObjectName("screen3")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(f"QWidget#screen3 {{ background-color: {tokens.COLOR_BG}; }}")
        
        # Canonical hash computation matching blueprint
        incident_data = {
            "incidentId": "VG-DESKTOP-LIVE",
            "detectedAt": time_str,
            "callType": "voip",
            "app": call_type_str,
            "confidenceAtAlert": 0.94
        }
        raw_hash = compute_evidence_hash(incident_data)
        self.evidence_hash = "0x" + raw_hash[:12] + "..." + raw_hash[-8:]
        self.chakshu_url = build_chakshu_link(incident_data)

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
        badge_label = QLabel("EvidenceLog.sol · Polygon Amoy")
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
        col_layout.addSpacing(tokens.SPACE_4)
        
        # 1. Title: "Report & Notarize Incident"
        self.title_label = QLabel("Report & Notarize Incident")
        font_title = QFont("Inter")
        font_title.setPixelSize(tokens.TEXT_TITLE["size"])
        font_title.setWeight(QFont.Weight.DemiBold)
        self.title_label.setFont(font_title)
        self.title_label.setStyleSheet(f"color: {tokens.COLOR_TEXT_PRIMARY}; border: none;")
        col_layout.addWidget(self.title_label)
        
        col_layout.addSpacing(tokens.SPACE_5)
        
        # 2. Card: label / value pairs with SHA-256 and Gov Portal
        self.detail_card = VoiceGuardCard()
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(tokens.SPACE_4)
        grid.setVerticalSpacing(tokens.SPACE_3)
        
        pairs = [
            ("Call Timestamp:", time_str),
            ("AI Confidence:", confidence_str),
            ("Channel:", call_type_str),
            ("Evidence Hash:", self.evidence_hash),
            ("Ledger:", "Polygon Amoy Testnet"),
            ("Gov Portal:", "Chakshu (Sanchar Saathi)"),
        ]
        
        font_body = QFont("Inter")
        font_body.setPixelSize(tokens.TEXT_BODY["size"])
        font_body.setWeight(QFont.Weight.Normal)
        
        for row_idx, (label_t, val_t) in enumerate(pairs):
            lbl = QLabel(label_t)
            lbl.setFont(font_body)
            lbl.setStyleSheet(f"color: {tokens.COLOR_TEXT_SECONDARY}; border: none;")
            
            val = QLabel(val_t)
            val.setFont(font_body)
            val.setStyleSheet(f"color: {tokens.COLOR_TEXT_PRIMARY}; font-weight: 500; border: none;")
            
            grid.addWidget(lbl, row_idx, 0)
            grid.addWidget(val, row_idx, 1)
            
        self.detail_card.card_layout.addLayout(grid)
        col_layout.addWidget(self.detail_card)
        
        # Spacer
        col_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # 3. Button: Confirm & Notarize on Blockchain
        self.btn_confirm = VoiceGuardButton("Confirm & Notarize on Blockchain", variant="primary")
        self.btn_confirm.clicked.connect(self.confirm_report_clicked.emit)
        col_layout.addWidget(self.btn_confirm)
        col_layout.addSpacing(tokens.SPACE_2)
        
        # 4. Button: Report on Chakshu (DoT Portal)
        self.btn_chakshu = VoiceGuardButton("Report on Chakshu (DoT Portal)", variant="secondary")
        self.btn_chakshu.clicked.connect(self._open_chakshu)
        col_layout.addWidget(self.btn_chakshu)
        col_layout.addSpacing(tokens.SPACE_2)
        
        # 5. Button: Cancel
        self.btn_cancel = VoiceGuardButton("Cancel", variant="secondary")
        self.btn_cancel.clicked.connect(self.cancel_clicked.emit)
        col_layout.addWidget(self.btn_cancel)
        
        root_layout.addWidget(self.column)

    def _open_chakshu(self):
        try:
            webbrowser.open(self.chakshu_url)
        except Exception as e:
            print(f"Error launching browser for Chakshu: {e}")
