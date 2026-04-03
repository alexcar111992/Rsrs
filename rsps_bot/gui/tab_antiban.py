"""Anti-Ban tab - settings to look more human."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QSpinBox, QCheckBox, QSlider,
)
from PyQt5.QtCore import Qt

from rsps_bot.core.config import AntibanSettings


class AntibanTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        info = QLabel(
            "These settings make the bot behave more like a real player\n"
            "to reduce the chance of being detected and banned."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #89b4fa; padding: 6px;")
        layout.addWidget(info)

        group = QGroupBox("Anti-Ban Settings")
        g = QVBoxLayout(group)

        self.chk_enabled = QCheckBox("Enable anti-ban features")
        self.chk_enabled.setChecked(True)
        g.addWidget(self.chk_enabled)

        self.chk_camera = QCheckBox("Random camera rotations")
        self.chk_camera.setChecked(True)
        g.addWidget(self.chk_camera)

        self.chk_drift = QCheckBox("Random mouse drifts")
        self.chk_drift.setChecked(True)
        g.addWidget(self.chk_drift)

        self.chk_pauses = QCheckBox("Random short pauses")
        self.chk_pauses.setChecked(True)
        g.addWidget(self.chk_pauses)

        pause_row = QHBoxLayout()
        pause_row.addWidget(QLabel("Pause duration (sec):"))
        self.pause_min = QSpinBox()
        self.pause_min.setRange(1, 60)
        self.pause_min.setValue(3)
        pause_row.addWidget(self.pause_min)
        pause_row.addWidget(QLabel("to"))
        self.pause_max = QSpinBox()
        self.pause_max.setRange(1, 120)
        self.pause_max.setValue(30)
        pause_row.addWidget(self.pause_max)
        pause_row.addStretch()
        g.addLayout(pause_row)

        self.chk_afk = QCheckBox("Occasional AFK breaks (walk away from keyboard)")
        self.chk_afk.setChecked(True)
        g.addWidget(self.chk_afk)

        afk_row = QHBoxLayout()
        afk_row.addWidget(QLabel("AFK duration (sec):"))
        self.afk_min = QSpinBox()
        self.afk_min.setRange(10, 600)
        self.afk_min.setValue(30)
        afk_row.addWidget(self.afk_min)
        afk_row.addWidget(QLabel("to"))
        self.afk_max = QSpinBox()
        self.afk_max.setRange(10, 600)
        self.afk_max.setValue(180)
        afk_row.addWidget(self.afk_max)
        afk_row.addStretch()
        g.addLayout(afk_row)

        chance_row = QHBoxLayout()
        chance_row.addWidget(QLabel("AFK chance:"))
        self.afk_chance = QSlider(Qt.Horizontal)
        self.afk_chance.setRange(1, 25)
        self.afk_chance.setValue(5)
        self.afk_label = QLabel("5%")
        self.afk_chance.valueChanged.connect(lambda v: self.afk_label.setText(f"{v}%"))
        chance_row.addWidget(self.afk_chance)
        chance_row.addWidget(self.afk_label)
        g.addLayout(chance_row)

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
