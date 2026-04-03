"""Login tab - auto-login configuration."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QLineEdit, QSpinBox, QCheckBox,
)

from rsps_bot.core.config import LoginSettings


class LoginTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        info = QLabel(
            "If the bot detects you've been logged out or disconnected,\n"
            "it will automatically log back in using these credentials."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #89b4fa; padding: 6px;")
        layout.addWidget(info)

        group = QGroupBox("Auto-Login Settings")
        g = QVBoxLayout(group)

        self.chk_enabled = QCheckBox("Enable auto-login")
        self.chk_enabled.setChecked(True)
        g.addWidget(self.chk_enabled)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Username:"))
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Your RSPS username")
        row1.addWidget(self.username_edit, 1)
        g.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Password:"))
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("Your RSPS password")
        row2.addWidget(self.password_edit, 1)
        g.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("World:"))
        self.world_spin = QSpinBox()
        self.world_spin.setRange(1, 200)
        self.world_spin.setValue(1)
        row3.addWidget(self.world_spin)
        row3.addStretch()
        row3.addWidget(QLabel("Retry delay (sec):"))
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(1, 300)
        self.delay_spin.setValue(10)
        row3.addWidget(self.delay_spin)
        row3.addStretch()
        row3.addWidget(QLabel("Max retries:"))
        self.retries_spin = QSpinBox()
        self.retries_spin.setRange(1, 100)
        self.retries_spin.setValue(10)
        row3.addWidget(self.retries_spin)
        g.addLayout(row3)

        layout.addWidget(group)
        layout.addStretch()

    def get_settings(self) -> LoginSettings:
        return LoginSettings(
            enabled=self.chk_enabled.isChecked(),
            username=self.username_edit.text(),
            password=self.password_edit.text(),
            world=self.world_spin.value(),
            retry_delay_seconds=self.delay_spin.value(),
            max_retries=self.retries_spin.value(),
        )

    def load_profile(self, profile):
        s = profile.login
        self.chk_enabled.setChecked(s.enabled)
        self.username_edit.setText(s.username)
        self.password_edit.setText(s.password)
        self.world_spin.setValue(s.world)
        self.delay_spin.setValue(s.retry_delay_seconds)
        self.retries_spin.setValue(s.max_retries)
