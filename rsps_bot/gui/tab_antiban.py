"""Anti-Ban tab - settings to look more human."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QLabel,
    QSpinBox, QCheckBox, QSlider,
)
from PyQt5.QtCore import Qt

from rsps_bot.core.config import AntibanSettings


class AntibanTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        info = QLabel(
            "These settings make the bot behave more like a real player\n"
            "to reduce the chance of being detected and banned."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #89b4fa; padding: 8px; font-size: 11px;")
        layout.addWidget(info)

        group = QGroupBox("Anti-Ban Settings")
        form = QFormLayout(group)
        form.setSpacing(10)
        form.setContentsMargins(12, 20, 12, 12)

        self.chk_enabled = QCheckBox("Enable anti-ban features")
        self.chk_enabled.setChecked(True)
        form.addRow(self.chk_enabled)

        self.chk_camera = QCheckBox("Random camera rotations")
        self.chk_camera.setChecked(True)
        form.addRow(self.chk_camera)

        self.chk_drift = QCheckBox("Random mouse drifts")
        self.chk_drift.setChecked(True)
        form.addRow(self.chk_drift)

        self.chk_pauses = QCheckBox("Random short pauses")
        self.chk_pauses.setChecked(True)
        form.addRow(self.chk_pauses)

        # Pause duration row
        pause_row = QHBoxLayout()
        self.pause_min = QSpinBox()
        self.pause_min.setRange(1, 60)
        self.pause_min.setValue(3)
        self.pause_min.setSuffix(" sec")
        self.pause_min.setMaximumWidth(90)
        pause_row.addWidget(self.pause_min)
        pause_row.addWidget(QLabel("to"))
        self.pause_max = QSpinBox()
        self.pause_max.setRange(1, 120)
        self.pause_max.setValue(30)
        self.pause_max.setSuffix(" sec")
        self.pause_max.setMaximumWidth(90)
        pause_row.addWidget(self.pause_max)
        pause_row.addStretch()
        form.addRow("Pause duration:", pause_row)

        self.chk_afk = QCheckBox("Occasional AFK breaks (walk away from keyboard)")
        self.chk_afk.setChecked(True)
        form.addRow(self.chk_afk)

        # AFK duration row
        afk_row = QHBoxLayout()
        self.afk_min = QSpinBox()
        self.afk_min.setRange(10, 600)
        self.afk_min.setValue(30)
        self.afk_min.setSuffix(" sec")
        self.afk_min.setMaximumWidth(90)
        afk_row.addWidget(self.afk_min)
        afk_row.addWidget(QLabel("to"))
        self.afk_max = QSpinBox()
        self.afk_max.setRange(10, 600)
        self.afk_max.setValue(180)
        self.afk_max.setSuffix(" sec")
        self.afk_max.setMaximumWidth(90)
        afk_row.addWidget(self.afk_max)
        afk_row.addStretch()
        form.addRow("AFK duration:", afk_row)

        # AFK chance
        chance_row = QHBoxLayout()
        self.afk_chance = QSlider(Qt.Horizontal)
        self.afk_chance.setRange(1, 25)
        self.afk_chance.setValue(5)
        self.afk_chance.setMaximumWidth(200)
        self.afk_label = QLabel("5%")
        self.afk_label.setMinimumWidth(35)
        self.afk_chance.valueChanged.connect(lambda v: self.afk_label.setText(f"{v}%"))
        chance_row.addWidget(self.afk_chance)
        chance_row.addWidget(self.afk_label)
        chance_row.addStretch()
        form.addRow("AFK chance:", chance_row)

        layout.addWidget(group)
        layout.addStretch()

    def get_settings(self) -> AntibanSettings:
        return AntibanSettings(
            enabled=self.chk_enabled.isChecked(),
            random_camera=self.chk_camera.isChecked(),
            random_mouse_drift=self.chk_drift.isChecked(),
            random_pauses=self.chk_pauses.isChecked(),
            pause_min_seconds=self.pause_min.value(),
            pause_max_seconds=self.pause_max.value(),
            random_afk=self.chk_afk.isChecked(),
            afk_min_seconds=self.afk_min.value(),
            afk_max_seconds=self.afk_max.value(),
            afk_chance_percent=self.afk_chance.value(),
        )

    def load_profile(self, profile):
        s = profile.antiban
        self.chk_enabled.setChecked(s.enabled)
        self.chk_camera.setChecked(s.random_camera)
        self.chk_drift.setChecked(s.random_mouse_drift)
        self.chk_pauses.setChecked(s.random_pauses)
        self.pause_min.setValue(s.pause_min_seconds)
        self.pause_max.setValue(s.pause_max_seconds)
        self.chk_afk.setChecked(s.random_afk)
        self.afk_min.setValue(s.afk_min_seconds)
        self.afk_max.setValue(s.afk_max_seconds)
        self.afk_chance.setValue(s.afk_chance_percent)
