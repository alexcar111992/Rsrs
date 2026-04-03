"""Easter Event tab - Easter Baby Mole boss automation.

Detection-based workflow:
  1. Detects if prayers are on -> turns them on if not
  2. Detects if mole is spawned -> clicks spade if not
  3. Detects mole -> attacks it
  4. Detects kill -> repeats

No looting (necklace auto-banks), no eating/potting (unlimited prayers).
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox, QLabel,
    QLineEdit, QSpinBox, QCheckBox, QHBoxLayout, QPushButton,
)
from PyQt5.QtCore import pyqtSignal

from rsps_bot.core.config import EasterEventSettings


class EasterEventTab(QWidget):
    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(8, 8, 8, 8)

        # Info
        info = QLabel(
            "Easter Baby Mole Event - detection-based boss farming.\n\n"
            "The bot DETECTS everything:\n"
            "  - Prayers off? -> Clicks quick prayers orb\n"
            "  - No mole?     -> Clicks spade to spawn one\n"
            "  - Mole visible? -> Right-click attacks it\n"
            "  - Mole dead?   -> Starts next cycle\n\n"
            "No looting needed (necklace auto-banks).\n"
            "No eating/potting needed (prayers are unlimited)."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #f9e2af; padding: 8px; font-size: 11px;")
        layout.addWidget(info)

        # ── Settings ──────────────────────────────────────────────────
        settings_group = QGroupBox("Settings")
        sf = QFormLayout(settings_group)
        sf.setSpacing(12)
        sf.setContentsMargins(12, 24, 12, 12)

        self.spade_slot_spin = QSpinBox()
        self.spade_slot_spin.setRange(1, 28)
        self.spade_slot_spin.setValue(5)
        self.spade_slot_spin.setMaximumWidth(80)
        sf.addRow("Spade inventory slot:", self.spade_slot_spin)

        self.npc_name_edit = QLineEdit("Easter baby mole")
        self.npc_name_edit.setMinimumHeight(28)
        sf.addRow("NPC name:", self.npc_name_edit)

        self.cycle_delay_spin = QSpinBox()
        self.cycle_delay_spin.setRange(0, 10000)
        self.cycle_delay_spin.setValue(1000)
        self.cycle_delay_spin.setSuffix(" ms")
        self.cycle_delay_spin.setMaximumWidth(120)
        sf.addRow("Delay between kills:", self.cycle_delay_spin)

        layout.addWidget(settings_group)

        # ── Start / Stop ──────────────────────────────────────────────
        btn_row = QHBoxLayout()
        self.btn_start = QPushButton("  START Easter Event  ")
        self.btn_start.setStyleSheet("background:#2a7a2a; color:white; font-size:13px; font-weight:bold; padding:8px 20px;")
        self.btn_start.clicked.connect(self.start_requested.emit)
        self.btn_stop = QPushButton("  STOP Easter Event  ")
        self.btn_stop.setStyleSheet("background:#a02020; color:white; font-size:13px; font-weight:bold; padding:8px 20px;")
        self.btn_stop.clicked.connect(self.stop_requested.emit)
        btn_row.addWidget(self.btn_start)
        btn_row.addWidget(self.btn_stop)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        layout.addStretch()

    def get_settings(self) -> EasterEventSettings:
        return EasterEventSettings(
            enabled=True,  # Always enabled when this tab starts it
            spade_slot=self.spade_slot_spin.value(),
            npc_name=self.npc_name_edit.text(),
            delay_between_kills_ms=self.cycle_delay_spin.value(),
        )

    def load_profile(self, profile):
        s = profile.easter_event
        self.spade_slot_spin.setValue(s.spade_slot)
        self.npc_name_edit.setText(s.npc_name)
        self.cycle_delay_spin.setValue(s.delay_between_kills_ms)
