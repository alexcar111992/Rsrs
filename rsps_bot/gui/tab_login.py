"""Login tab - auto-login configuration."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox, QLabel,
    QLineEdit, QSpinBox, QCheckBox,
)

from rsps_bot.core.config import LoginSettings


class LoginTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        info = QLabel(
            "If the bot detects you've been logged out or disconnected,\n"
            "it will automatically log back in using these credentials."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #89b4fa; padding: 8px; font-size: 11px;")
        layout.addWidget(info)

        group = QGroupBox("Auto-Login Settings")
        form = QFormLayout(group)
        form.setSpacing(12)
        form.setContentsMargins(12, 20, 12, 12)

        self.chk_enabled = QCheckBox("Enable auto-login")
        self.chk_enabled.setChecked(True)
        form.addRow(self.chk_enabled)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Your RSPS username")
        self.username_edit.setMaximumWidth(300)
        form.addRow("Username:", self.username_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("Your RSPS password")
        self.password_edit.setMaximumWidth(300)
        form.addRow("Password:", self.password_edit)

        self.world_spin = QSpinBox()
        self.world_spin.setRange(1, 200)
        self.world_spin.setValue(1)
        self.world_spin.setMaximumWidth(100)
        form.addRow("World:", self.world_spin)

        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(1, 300)
        self.delay_spin.setValue(10)
        self.delay_spin.setSuffix(" sec")
        self.delay_spin.setMaximumWidth(100)
        form.addRow("Retry delay:", self.delay_spin)

        self.retries_spin = QSpinBox()
        self.retries_spin.setRange(1, 100)
        self.retries_spin.setValue(10)
        self.retries_spin.setMaximumWidth(100)
        form.addRow("Max retries:", self.retries_spin)

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
