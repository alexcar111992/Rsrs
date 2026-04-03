"""Inventory tab - user configures what to click and when."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QLineEdit, QSpinBox, QComboBox, QCheckBox, QPushButton,
    QScrollArea, QFrame,
)

from rsps_bot.core.config import InventorySlotAction, ITEM_ACTIONS

TRIGGERS = [
    "When HP below %",
    "On cooldown (seconds)",
    "When inventory full",
    "When not in combat",
    "When in combat",
    "Always (every tick)",
]


class InvActionRow(QFrame):
    def __init__(self, index: int = 1):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)

        self.chk_enabled = QCheckBox()
        self.chk_enabled.setChecked(True)
        lay.addWidget(self.chk_enabled)

        lay.addWidget(QLabel("Slot:"))
        self.slot_spin = QSpinBox()
        self.slot_spin.setRange(1, 28)
        self.slot_spin.setValue(index)
        lay.addWidget(self.slot_spin)

        lay.addWidget(QLabel("Item:"))
        self.item_edit = QLineEdit()
        self.item_edit.setPlaceholderText("e.g. Shark, Super str pot...")
        self.item_edit.setMinimumWidth(120)
        lay.addWidget(self.item_edit, 1)

        lay.addWidget(QLabel("Action:"))
        self.action_combo = QComboBox()
        self.action_combo.addItems(ITEM_ACTIONS)
        lay.addWidget(self.action_combo)

        lay.addWidget(QLabel("When:"))
        self.trigger_combo = QComboBox()
        self.trigger_combo.addItems(TRIGGERS)
        lay.addWidget(self.trigger_combo)

        lay.addWidget(QLabel("Value:"))
        self.value_spin = QSpinBox()
        self.value_spin.setRange(1, 10000)
        self.value_spin.setValue(50)
        lay.addWidget(self.value_spin)

    def get_action(self) -> InventorySlotAction:
        return InventorySlotAction(
            slot_number=self.slot_spin.value(),
            item_description=self.item_edit.text(),
            action=self.action_combo.currentText(),
            trigger=self.trigger_combo.currentText(),
            trigger_value=self.value_spin.value(),
            enabled=self.chk_enabled.isChecked(),
        )

    def load_action(self, a: InventorySlotAction):
        self.slot_spin.setValue(a.slot_number)
        self.item_edit.setText(a.item_description)
        idx = self.action_combo.findText(a.action)
        if idx >= 0:
            self.action_combo.setCurrentIndex(idx)
        idx = self.trigger_combo.findText(a.trigger)
        if idx >= 0:
            self.trigger_combo.setCurrentIndex(idx)
        self.value_spin.setValue(a.trigger_value)
        self.chk_enabled.setChecked(a.enabled)


class InventoryTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        info = QLabel(
            "Configure what items are in your inventory and when to click them.\n"
            "Example: Slot 25 = Shark, Action = Left-click (Eat), When HP below 50%"
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #89b4fa; padding: 6px;")
        layout.addWidget(info)

        group = QGroupBox("Inventory Slot Actions")
        g_lay = QVBoxLayout(group)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.rows_layout = QVBoxLayout(scroll_widget)
        scroll.setWidget(scroll_widget)
        g_lay.addWidget(scroll)

        self.rows = []

        btn_row = QHBoxLayout()
        btn_add = QPushButton("+ Add Inventory Action")
        btn_add.clicked.connect(self._add_row)
        btn_remove = QPushButton("- Remove Last")
        btn_remove.clicked.connect(self._remove_row)
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_remove)
        btn_row.addStretch()
        g_lay.addLayout(btn_row)

        layout.addWidget(group, 1)

    def _add_row(self):
        row = InvActionRow(len(self.rows) + 1)
        self.rows.append(row)
        self.rows_layout.addWidget(row)

    def _remove_row(self):
        if self.rows:
            row = self.rows.pop()
            self.rows_layout.removeWidget(row)
            row.deleteLater()

    def get_actions(self):
        return [row.get_action() for row in self.rows]

    def load_profile(self, profile):
        while self.rows:
            self._remove_row()
        for a in profile.inventory_actions:
            self._add_row()
            self.rows[-1].load_action(a)
