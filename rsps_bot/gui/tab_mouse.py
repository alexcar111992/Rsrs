"""Mouse Mode tab - real mouse vs ghost mouse."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QComboBox, QCheckBox, QSlider,
)
from PyQt5.QtCore import Qt

from rsps_bot.core.config import MouseSettings


class MouseTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        info = QLabel(
            "REAL MOUSE: Moves your actual cursor. Only 1 client at a time.\n"
            "GHOST MOUSE: Sends clicks directly to the game window.\n"
            "   You keep your mouse free! Run multiple clients at once."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #89b4fa; padding: 6px;")
        layout.addWidget(info)

        group = QGroupBox("Mouse Settings")
        g = QVBoxLayout(group)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Mouse Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Ghost Mouse", "Real Mouse"])
        self.mode_combo.setMinimumWidth(200)
        row1.addWidget(self.mode_combo)
        row1.addStretch()
        g.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Speed:"))
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["Slow", "Normal", "Fast", "Instant"])
        self.speed_combo.setCurrentIndex(1)
        row2.addWidget(self.speed_combo)
        row2.addStretch()
        g.addLayout(row2)

        self.chk_humanize = QCheckBox("Humanize mouse movement (random curves, slight delays)")
        self.chk_humanize.setChecked(True)
        g.addWidget(self.chk_humanize)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Misclick chance:"))
        self.misclick_slider = QSlider(Qt.Horizontal)
        self.misclick_slider.setRange(0, 100)
        self.misclick_slider.setValue(2)
        self.misclick_label = QLabel("2%")
        self.misclick_slider.valueChanged.connect(
            lambda v: self.misclick_label.setText(f"{v}%")
        )
        row3.addWidget(self.misclick_slider)
        row3.addWidget(self.misclick_label)
        g.addLayout(row3)

        layout.addWidget(group)
        layout.addStretch()

    def get_settings(self) -> MouseSettings:
        return MouseSettings(
            mode=self.mode_combo.currentText(),
            speed=self.speed_combo.currentText(),
            humanize=self.chk_humanize.isChecked(),
            misclick_chance=self.misclick_slider.value() / 100.0,
        )

    def load_profile(self, profile):
        s = profile.mouse
        idx = self.mode_combo.findText(s.mode)
        if idx >= 0:
            self.mode_combo.setCurrentIndex(idx)
        idx = self.speed_combo.findText(s.speed)
        if idx >= 0:
            self.speed_combo.setCurrentIndex(idx)
        self.chk_humanize.setChecked(s.humanize)
        self.misclick_slider.setValue(int(s.misclick_chance * 100))
