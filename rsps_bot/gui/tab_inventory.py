"""Inventory tab - user configures what to click and when."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QLabel,
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

        # Two rows instead of one cramped line
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 6, 8, 6)
        outer.setSpacing(4)

        # Row 1: Enable + Slot + Item name
        row1 = QHBoxLayout()
        self.chk_enabled = QCheckBox()
        self.chk_enabled.setChecked(True)
        row1.addWidget(self.chk_enabled)
        row1.addWidget(QLabel("Slot:"))
        self.slot_spin = QSpinBox()
        self.slot_spin.setRange(1, 28)
        self.slot_spin.setValue(index)
        self.slot_spin.setMaximumWidth(60)
        row1.addWidget(self.slot_spin)
        row1.addSpacing(10)
        row1.addWidget(QLabel("Item:"))
        self.item_edit = QLineEdit()
        self.item_edit.setPlaceholderText("e.g. Shark, Super str pot, Bones...")
        row1.addWidget(self.item_edit, 1)
        outer.addLayout(row1)

        # Row 2: Action + Trigger + Value
        row2 = QHBoxLayout()
        row2.addSpacing(26)
        row2.addWidget(QLabel("Action:"))
        self.action_combo = QComboBox()
        self.action_combo.addItems(ITEM_ACTIONS)
        self.action_combo.setMinimumWidth(180)
        row2.addWidget(self.action_combo)
        row2.addSpacing(10)
        row2.addWidget(QLabel("When:"))
        self.trigger_combo = QComboBox()
        self.trigger_combo.addItems(TRIGGERS)
        self.trigger_combo.setMinimumWidth(160)
        row2.addWidget(self.trigger_combo)
        row2.addSpacing(10)
        row2.addWidget(QLabel("Value:"))
        self.value_spin = QSpinBox()
        self.value_spin.setRange(1, 10000)
        self.value_spin.setValue(50)
        self.value_spin.setMaximumWidth(80)
        row2.addWidget(self.value_spin)
        row2.addStretch()
        outer.addLayout(row2)

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
        layout.setSpacing(8)

        info = QLabel(
            "Configure what items are in your inventory and when to click them.\n"
            "Example: Slot 25 = Shark, Action = Left-click (Eat), When = HP below 50%"
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #89b4fa; padding: 8px; font-size: 11px;")
        layout.addWidget(info)

        group = QGroupBox("Inventory Slot Actions")
        g_lay = QVBoxLayout(group)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.rows_layout = QVBoxLayout(scroll_widget)
        self.rows_layout.setSpacing(4)
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
