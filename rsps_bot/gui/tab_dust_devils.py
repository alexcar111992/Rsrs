"""Dust Devils tab - dedicated farming bot for Dust Devils.

Right-click attacks Dust Devils by name, waits for kill,
instantly attacks the next one. Never attacks desert lizards
or other NPCs.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox, QLabel,
    QLineEdit, QHBoxLayout, QPushButton,
)
from PyQt5.QtCore import pyqtSignal

from rsps_bot.core.config import DustDevilsSettings


class DustDevilsTab(QWidget):
    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(8, 8, 8, 8)

        # Info
        info = QLabel(
            "Dust Devils (Level 93, 105 HP) - instant re-attack farming.\n\n"
            "How it works:\n"
            "  1. Finds Dust Devils by their orange color in the viewport\n"
            "  2. Right-clicks and selects 'Attack Dust devil' from menu\n"
            "  3. Waits for it to die\n"
            "  4. INSTANTLY attacks the next one (zero delay)\n\n"
            "Only attacks NPCs matching the name below - ignores Desert Lizards\n"
            "and all other NPCs. No prayers/eating/potting needed."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #fab387; padding: 8px; font-size: 11px;")
        layout.addWidget(info)

        # ── Settings ──────────────────────────────────────────────────
        settings_group = QGroupBox("Settings")
        sf = QFormLayout(settings_group)
        sf.setSpacing(12)
        sf.setContentsMargins(12, 24, 12, 12)

        self.npc_name_edit = QLineEdit("Dust devil")
        self.npc_name_edit.setMinimumHeight(28)
        sf.addRow("NPC name (must match right-click menu):", self.npc_name_edit)

        layout.addWidget(settings_group)

        # ── Start / Stop ──────────────────────────────────────────────
        btn_row = QHBoxLayout()
        self.btn_start = QPushButton("  START Dust Devils  ")
        self.btn_start.setStyleSheet("background:#2a7a2a; color:white; font-size:13px; font-weight:bold; padding:8px 20px;")
        self.btn_start.clicked.connect(self.start_requested.emit)
        self.btn_stop = QPushButton("  STOP Dust Devils  ")
        self.btn_stop.setStyleSheet("background:#a02020; color:white; font-size:13px; font-weight:bold; padding:8px 20px;")
        self.btn_stop.clicked.connect(self.stop_requested.emit)
        btn_row.addWidget(self.btn_start)
        btn_row.addWidget(self.btn_stop)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        layout.addStretch()

    def get_settings(self) -> DustDevilsSettings:
        return DustDevilsSettings(
            enabled=True,
            npc_name=self.npc_name_edit.text(),
        )

    def load_profile(self, profile):
        s = profile.dust_devils
        self.npc_name_edit.setText(s.npc_name)
