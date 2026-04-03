"""Loot tab - user configures what items to pick up."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QLineEdit, QSpinBox, QCheckBox, QPushButton, QScrollArea, QFrame,
)

from rsps_bot.core.config import LootRule


class LootRuleRow(QFrame):
    def __init__(self, index: int = 1):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)

        self.chk_pickup = QCheckBox("Pick up")
        self.chk_pickup.setChecked(True)
        lay.addWidget(self.chk_pickup)

        lay.addWidget(QLabel("Item name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Dragon bones, Rune scimitar...")
        self.name_edit.setMinimumWidth(200)
        lay.addWidget(self.name_edit, 1)

        lay.addWidget(QLabel("Priority:"))
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(1, 10)
        self.priority_spin.setValue(index)
        lay.addWidget(self.priority_spin)

    def get_rule(self) -> LootRule:
        return LootRule(
            item_name=self.name_edit.text(),
            pickup=self.chk_pickup.isChecked(),
            priority=self.priority_spin.value(),
        )

    def load_rule(self, r: LootRule):
        self.name_edit.setText(r.item_name)
        self.chk_pickup.setChecked(r.pickup)
        self.priority_spin.setValue(r.priority)


class LootTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        info = QLabel(
            "Add items you want to pick up after killing NPCs.\n"
            "Leave empty and check 'Pick up all' to grab everything."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #89b4fa; padding: 6px;")
        layout.addWidget(info)

        self.chk_pickup_all = QCheckBox("Pick up ALL ground items (ignore list below)")
        layout.addWidget(self.chk_pickup_all)

        group = QGroupBox("Loot List (items to pick up)")
        g_lay = QVBoxLayout(group)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.rows_layout = QVBoxLayout(scroll_widget)
        scroll.setWidget(scroll_widget)
        g_lay.addWidget(scroll)

        self.rows = []

        btn_row = QHBoxLayout()
        btn_add = QPushButton("+ Add Loot Item")
        btn_add.clicked.connect(self._add_row)
        btn_remove = QPushButton("- Remove Last")
        btn_remove.clicked.connect(self._remove_row)
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_remove)
        btn_row.addStretch()
        g_lay.addLayout(btn_row)

        layout.addWidget(group, 1)

    def _add_row(self):
        row = LootRuleRow(len(self.rows) + 1)
        self.rows.append(row)
        self.rows_layout.addWidget(row)

    def _remove_row(self):
        if self.rows:
            row = self.rows.pop()
            self.rows_layout.removeWidget(row)
            row.deleteLater()

    def get_rules(self):
        return [row.get_rule() for row in self.rows if row.name_edit.text().strip()]

    def load_profile(self, profile):
        self.chk_pickup_all.setChecked(not bool(profile.loot_rules))
        while self.rows:
            self._remove_row()
        for r in profile.loot_rules:
            self._add_row()
            self.rows[-1].load_rule(r)
