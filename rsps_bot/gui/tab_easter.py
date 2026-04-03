"""Easter Event tab - Easter Baby Mole boss automation.

Detection-based workflow:
  1. Checks if prayers are on -> turns them on if not
  2. Clicks spade to spawn mole -> mole auto-attacks player
  3. Waits for mole to die (player auto-retaliates)
  4. Repeats

Never attacks. No looting. No eating/potting.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox, QLabel,
    QSpinBox, QHBoxLayout, QPushButton,
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
            "Easter Baby Mole Event - fully automated boss farming.\n\n"
            "How it works:\n"
            "  1. Detects if prayers are off -> clicks quick prayers orb\n"
            "  2. Clicks spade in inventory -> mole spawns & auto-attacks you\n"
            "  3. Waits for your mole to die (you auto-retaliate)\n"
            "  4. Short delay, then clicks spade again\n\n"
            "The bot NEVER manually attacks - the mole attacks you.\n"
            "Other players' moles are ignored (only detects combat near your character).\n"
            "No looting needed (necklace auto-banks). No eating/potting (unlimited prayers)."
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

        self.cycle_delay_spin = QSpinBox()
        self.cycle_delay_spin.setRange(0, 10000)
        self.cycle_delay_spin.setValue(1000)
        self.cycle_delay_spin.setSuffix(" ms")
        self.cycle_delay_spin.setMaximumWidth(120)
        sf.addRow("Delay between kills:", self.cycle_delay_spin)

        self.spawn_timeout_spin = QSpinBox()
        self.spawn_timeout_spin.setRange(1000, 30000)
        self.spawn_timeout_spin.setValue(5000)
        self.spawn_timeout_spin.setSuffix(" ms")
        self.spawn_timeout_spin.setMaximumWidth(120)
        sf.addRow("Spawn timeout (retry spade):", self.spawn_timeout_spin)

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
            enabled=True,
            spade_slot=self.spade_slot_spin.value(),
            delay_between_kills_ms=self.cycle_delay_spin.value(),
            spawn_timeout_ms=self.spawn_timeout_spin.value(),
        )

    def load_profile(self, profile):
        s = profile.easter_event
        self.spade_slot_spin.setValue(s.spade_slot)
        self.cycle_delay_spin.setValue(s.delay_between_kills_ms)
        self.spawn_timeout_spin.setValue(s.spawn_timeout_ms)
