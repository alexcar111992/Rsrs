"""Skilling tab - user configures stationary skilling activities."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox, QLabel,
    QLineEdit, QSpinBox, QComboBox, QCheckBox, QScrollArea,
)

from rsps_bot.core.config import SkillingSettings, SKILLING_TYPES, INVENTORY_FULL_ACTIONS


class SkillingTab(QWidget):
    def __init__(self):
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Wrap everything in a scroll area so nothing gets squeezed
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setSpacing(10)
        layout.setContentsMargins(8, 8, 8, 8)

        # Info
        info = QLabel(
            "Configure stationary skilling - the bot clicks the same object repeatedly.\n"
            "Works for: Mining rocks, Chopping trees, Fishing spots, Thieving stalls,\n"
            "Cooking, Smithing, Crafting, and anything where you stand still and click."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #89b4fa; padding: 8px; font-size: 11px;")
        layout.addWidget(info)

        # ── What to skill ─────────────────────────────────────────────
        skill_group = QGroupBox("What To Skill")
        sf = QFormLayout(skill_group)
        sf.setSpacing(12)
        sf.setContentsMargins(12, 24, 12, 12)

        self.chk_enabled = QCheckBox("Enable skilling mode (overrides combat)")
        self.chk_enabled.setStyleSheet("color: #a6e3a1; font-weight: bold; font-size: 12px;")
        sf.addRow(self.chk_enabled)

        self.skill_type_combo = QComboBox()
        self.skill_type_combo.addItems(SKILLING_TYPES)
        self.skill_type_combo.setMaximumWidth(300)
        sf.addRow("Skill type:", self.skill_type_combo)

        self.object_name_edit = QLineEdit()
        self.object_name_edit.setPlaceholderText("e.g. Iron rock, Yew tree, Fishing spot, Gem stall...")
        self.object_name_edit.setMinimumHeight(28)
        sf.addRow("Object name:", self.object_name_edit)

        self.action_combo = QComboBox()
        self.action_combo.addItems(["Left-click", "Right-click > select option"])
        self.action_combo.setMaximumWidth(300)
        sf.addRow("Click action:", self.action_combo)

        self.right_click_option = QLineEdit()
        self.right_click_option.setPlaceholderText("e.g. Mine, Chop down, Net, Steal from...")
        self.right_click_option.setMinimumHeight(28)
        sf.addRow("Right-click option:", self.right_click_option)

        layout.addWidget(skill_group)

        # ── Timing ────────────────────────────────────────────────────
        timing_group = QGroupBox("Timing")
        tf = QFormLayout(timing_group)
        tf.setSpacing(12)
        tf.setContentsMargins(12, 24, 12, 12)

        self.chk_same_spot = QCheckBox("Click the same spot every time")
        self.chk_same_spot.setChecked(True)
        tf.addRow(self.chk_same_spot)

        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(200, 30000)
        self.delay_spin.setValue(1000)
        self.delay_spin.setSuffix(" ms")
        self.delay_spin.setSingleStep(100)
        self.delay_spin.setMaximumWidth(140)
        tf.addRow("Re-click delay:", self.delay_spin)

        self.chk_wait_anim = QCheckBox("Wait for idle animation before re-clicking")
        self.chk_wait_anim.setChecked(True)
        tf.addRow(self.chk_wait_anim)

        layout.addWidget(timing_group)

        # ── When inventory is full ────────────────────────────────────
        full_group = QGroupBox("When Inventory Is Full")
        ff = QFormLayout(full_group)
        ff.setSpacing(12)
        ff.setContentsMargins(12, 24, 12, 12)

        self.full_action_combo = QComboBox()
        self.full_action_combo.addItems(INVENTORY_FULL_ACTIONS)
        self.full_action_combo.setMaximumWidth(300)
        ff.addRow("Action:", self.full_action_combo)

        self.custom_cmd_edit = QLineEdit()
        self.custom_cmd_edit.setPlaceholderText("e.g. ::empty, ::bank, ::home...")
        self.custom_cmd_edit.setMinimumHeight(28)
        ff.addRow("Custom command:", self.custom_cmd_edit)

        self.drop_items_edit = QLineEdit()
        self.drop_items_edit.setPlaceholderText("Item names to drop, comma separated")
        self.drop_items_edit.setMinimumHeight(28)
        ff.addRow("Drop items:", self.drop_items_edit)

        layout.addWidget(full_group)

        # ── Use item on object ────────────────────────────────────────
        use_group = QGroupBox("Use Item On Object (optional)")
        uf = QFormLayout(use_group)
        uf.setSpacing(12)
        uf.setContentsMargins(12, 24, 12, 12)

        self.chk_use_item = QCheckBox("Use inventory item on object (e.g. Knife on Logs)")
        uf.addRow(self.chk_use_item)

        self.use_item_slot_spin = QSpinBox()
        self.use_item_slot_spin.setRange(1, 28)
        self.use_item_slot_spin.setValue(1)
        self.use_item_slot_spin.setMaximumWidth(80)
        uf.addRow("Item slot #:", self.use_item_slot_spin)

        layout.addWidget(use_group)
        layout.addStretch()

        scroll.setWidget(inner)
        outer.addWidget(scroll)

    def get_settings(self) -> SkillingSettings:
        drop_names = [
            n.strip() for n in self.drop_items_edit.text().split(",") if n.strip()
        ]
        return SkillingSettings(
            enabled=self.chk_enabled.isChecked(),
            skill_type=self.skill_type_combo.currentText(),
            object_name=self.object_name_edit.text(),
            object_action=self.action_combo.currentText(),
            right_click_option=self.right_click_option.text(),
            click_same_spot=self.chk_same_spot.isChecked(),
            re_click_delay_ms=self.delay_spin.value(),
            wait_for_animation=self.chk_wait_anim.isChecked(),
            inventory_full_action=self.full_action_combo.currentText(),
            drop_item_names=drop_names,
            custom_command=self.custom_cmd_edit.text(),
            use_item_on_object=self.chk_use_item.isChecked(),
            use_item_slot=self.use_item_slot_spin.value(),
        )

    def load_profile(self, profile):
        s = profile.skilling
        self.chk_enabled.setChecked(s.enabled)
        idx = self.skill_type_combo.findText(s.skill_type)
        if idx >= 0:
            self.skill_type_combo.setCurrentIndex(idx)
        self.object_name_edit.setText(s.object_name)
        idx = self.action_combo.findText(s.object_action)
        if idx >= 0:
            self.action_combo.setCurrentIndex(idx)
        self.right_click_option.setText(s.right_click_option)
        self.chk_same_spot.setChecked(s.click_same_spot)
        self.delay_spin.setValue(s.re_click_delay_ms)
        self.chk_wait_anim.setChecked(s.wait_for_animation)
        idx = self.full_action_combo.findText(s.inventory_full_action)
        if idx >= 0:
            self.full_action_combo.setCurrentIndex(idx)
        self.custom_cmd_edit.setText(s.custom_command)
        self.drop_items_edit.setText(", ".join(s.drop_item_names))
        self.chk_use_item.setChecked(s.use_item_on_object)
        self.use_item_slot_spin.setValue(s.use_item_slot)
