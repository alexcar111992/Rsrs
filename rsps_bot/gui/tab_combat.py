"""Combat / NPC tab - user configures who to fight and how."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QLabel,
    QLineEdit, QSpinBox, QComboBox, QCheckBox, QPushButton,
    QSlider, QScrollArea, QFrame,
)
from PyQt5.QtCore import Qt, pyqtSignal

from rsps_bot.core.config import NpcTarget, CombatSettings, NPC_ACTIONS


class NpcTargetRow(QFrame):
    """One row for configuring a single NPC target."""

    def __init__(self, index: int = 1):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("QFrame { margin: 2px; padding: 4px; }")

        # Use a 2-row layout instead of cramming everything on one line
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 6, 8, 6)
        outer.setSpacing(6)

        # Row 1: Name + HP
        row1 = QHBoxLayout()
        row1.addWidget(QLabel(f"<b>#{index}</b>"))
        row1.addSpacing(8)
        row1.addWidget(QLabel("NPC Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Rock Crab, Guard, Cow...")
        row1.addWidget(self.name_edit, 1)
        row1.addSpacing(12)
        row1.addWidget(QLabel("Max HP:"))
        self.hp_spin = QSpinBox()
        self.hp_spin.setRange(1, 100000)
        self.hp_spin.setValue(100)
        self.hp_spin.setMinimumWidth(80)
        row1.addWidget(self.hp_spin)
        outer.addLayout(row1)

        # Row 2: Action + Priority + Checkbox
        row2 = QHBoxLayout()
        row2.addSpacing(30)
        row2.addWidget(QLabel("Action:"))
        self.action_combo = QComboBox()
        self.action_combo.addItems(NPC_ACTIONS)
        self.action_combo.setMinimumWidth(120)
        row2.addWidget(self.action_combo)
        row2.addSpacing(12)
        row2.addWidget(QLabel("Priority:"))
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["1 (Highest)", "2", "3", "4", "5 (Lowest)"])
        row2.addWidget(self.priority_combo)
        row2.addSpacing(12)
        self.spawn_check = QCheckBox("Re-attack on spawn")
        self.spawn_check.setChecked(True)
        row2.addWidget(self.spawn_check)
        row2.addStretch()
        outer.addLayout(row2)

    def get_target(self) -> NpcTarget:
        return NpcTarget(
            name=self.name_edit.text(),
            max_health=self.hp_spin.value(),
            action=self.action_combo.currentText(),
            attack_on_spawn=self.spawn_check.isChecked(),
            priority=self.priority_combo.currentIndex() + 1,
        )

    def load_target(self, t: NpcTarget):
        self.name_edit.setText(t.name)
        self.hp_spin.setValue(t.max_health)
        idx = self.action_combo.findText(t.action)
        if idx >= 0:
            self.action_combo.setCurrentIndex(idx)
        self.spawn_check.setChecked(t.attack_on_spawn)
        self.priority_combo.setCurrentIndex(max(0, min(t.priority - 1, 4)))


class CombatTab(QWidget):
    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # ── NPC Targets ───────────────────────────────────────────────
        npc_group = QGroupBox("NPC Targets (type the NPC name, set its HP, pick action)")
        npc_lay = QVBoxLayout(npc_group)

        self.target_rows = []
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(140)
        scroll_widget = QWidget()
        self.targets_layout = QVBoxLayout(scroll_widget)
        self.targets_layout.setSpacing(4)
        scroll.setWidget(scroll_widget)
        npc_lay.addWidget(scroll)

        btn_row = QHBoxLayout()
        btn_add = QPushButton("+ Add NPC Target")
        btn_add.clicked.connect(self._add_target_row)
        btn_remove = QPushButton("- Remove Last")
        btn_remove.clicked.connect(self._remove_target_row)
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_remove)
        btn_row.addStretch()
        npc_lay.addLayout(btn_row)

        layout.addWidget(npc_group, 1)
        self._add_target_row()

        # ── Combat Settings - use form layout for clean columns ───────
        settings_group = QGroupBox("Combat Settings")
        sg = QVBoxLayout(settings_group)
        sg.setSpacing(8)

        # Food row
        food_box = QHBoxLayout()
        self.chk_eat = QCheckBox("Eat food when HP low")
        self.chk_eat.setChecked(True)
        food_box.addWidget(self.chk_eat)
        food_box.addSpacing(20)
        food_box.addWidget(QLabel("Eat at HP %:"))
        self.eat_slider = QSlider(Qt.Horizontal)
        self.eat_slider.setRange(5, 95)
        self.eat_slider.setValue(50)
        self.eat_slider.setMinimumWidth(120)
        self.eat_pct_label = QLabel("50%")
        self.eat_pct_label.setMinimumWidth(35)
        self.eat_slider.valueChanged.connect(lambda v: self.eat_pct_label.setText(f"{v}%"))
        food_box.addWidget(self.eat_slider)
        food_box.addWidget(self.eat_pct_label)
        food_box.addSpacing(20)
        food_box.addWidget(QLabel("Food slots:"))
        self.food_slots_edit = QLineEdit("25, 26, 27, 28")
        self.food_slots_edit.setMaximumWidth(140)
        self.food_slots_edit.setPlaceholderText("e.g. 25,26,27,28")
        food_box.addWidget(self.food_slots_edit)
        sg.addLayout(food_box)

        # Potions row
        pot_box = QHBoxLayout()
        self.chk_potions = QCheckBox("Use potions")
        pot_box.addWidget(self.chk_potions)
        pot_box.addSpacing(20)
        pot_box.addWidget(QLabel("Potion slots:"))
        self.potion_slots_edit = QLineEdit("")
        self.potion_slots_edit.setMaximumWidth(140)
        self.potion_slots_edit.setPlaceholderText("e.g. 1, 2, 3")
        pot_box.addWidget(self.potion_slots_edit)
        pot_box.addStretch()
        sg.addLayout(pot_box)

        # Loot + attack row
        loot_box = QHBoxLayout()
        self.chk_loot = QCheckBox("Loot after kill")
        self.chk_loot.setChecked(True)
        loot_box.addWidget(self.chk_loot)
        loot_box.addSpacing(12)
        loot_box.addWidget(QLabel("Loot delay:"))
        self.loot_delay_spin = QSpinBox()
        self.loot_delay_spin.setRange(0, 5000)
        self.loot_delay_spin.setValue(500)
        self.loot_delay_spin.setSuffix(" ms")
        loot_box.addWidget(self.loot_delay_spin)
        loot_box.addSpacing(20)
        self.chk_attack_spawn = QCheckBox("Attack next NPC immediately after kill")
        self.chk_attack_spawn.setChecked(True)
        loot_box.addWidget(self.chk_attack_spawn)
        loot_box.addStretch()
        sg.addLayout(loot_box)

        # Special + walk row
        extra_box = QHBoxLayout()
        self.chk_special = QCheckBox("Use special attack at")
        extra_box.addWidget(self.chk_special)
        self.special_spin = QSpinBox()
        self.special_spin.setRange(10, 100)
        self.special_spin.setValue(100)
        self.special_spin.setSuffix("%")
        self.special_spin.setSingleStep(10)
        self.special_spin.setMaximumWidth(80)
        extra_box.addWidget(self.special_spin)
        extra_box.addSpacing(20)
        self.chk_walk = QCheckBox("Walk to NPC if not nearby")
        self.chk_walk.setChecked(True)
        extra_box.addWidget(self.chk_walk)
        extra_box.addStretch()
        sg.addLayout(extra_box)

        layout.addWidget(settings_group)

        # ── Per-tab Start / Stop ──────────────────────────────────────
        tab_btn_row = QHBoxLayout()
        self.btn_start = QPushButton("  START Combat  ")
        self.btn_start.setStyleSheet("background:#2a7a2a; color:white; font-size:12px; font-weight:bold; padding:7px 18px;")
        self.btn_start.clicked.connect(self.start_requested.emit)
        self.btn_stop = QPushButton("  STOP Combat  ")
        self.btn_stop.setStyleSheet("background:#a02020; color:white; font-size:12px; font-weight:bold; padding:7px 18px;")
        self.btn_stop.clicked.connect(self.stop_requested.emit)
        tab_btn_row.addWidget(self.btn_start)
        tab_btn_row.addWidget(self.btn_stop)
        tab_btn_row.addStretch()
        layout.addLayout(tab_btn_row)

    def _add_target_row(self):
        row = NpcTargetRow(len(self.target_rows) + 1)
        self.target_rows.append(row)
        self.targets_layout.addWidget(row)

    def _remove_target_row(self):
        if self.target_rows:
            row = self.target_rows.pop()
            self.targets_layout.removeWidget(row)
            row.deleteLater()

    def _parse_slots(self, text: str):
        slots = []
        for part in text.split(","):
            part = part.strip()
            if part.isdigit():
                slots.append(int(part))
        return slots

    def get_targets(self):
        return [row.get_target() for row in self.target_rows if row.name_edit.text().strip()]

    def get_settings(self) -> CombatSettings:
        return CombatSettings(
            eat_food=self.chk_eat.isChecked(),
            eat_at_hp_percent=self.eat_slider.value(),
            food_slots=self._parse_slots(self.food_slots_edit.text()),
            use_potions=self.chk_potions.isChecked(),
            potion_slots=self._parse_slots(self.potion_slots_edit.text()),
            use_special_attack=self.chk_special.isChecked(),
            special_at_percent=self.special_spin.value(),
            loot_after_kill=self.chk_loot.isChecked(),
            loot_delay_ms=self.loot_delay_spin.value(),
            attack_on_spawn=self.chk_attack_spawn.isChecked(),
            walk_to_npc=self.chk_walk.isChecked(),
        )

    def load_profile(self, profile):
        while self.target_rows:
            self._remove_target_row()
        for t in profile.npc_targets:
            self._add_target_row()
            self.target_rows[-1].load_target(t)
        c = profile.combat
        self.chk_eat.setChecked(c.eat_food)
        self.eat_slider.setValue(c.eat_at_hp_percent)
        self.food_slots_edit.setText(", ".join(str(s) for s in c.food_slots))
        self.chk_potions.setChecked(c.use_potions)
        self.potion_slots_edit.setText(", ".join(str(s) for s in c.potion_slots))
        self.chk_loot.setChecked(c.loot_after_kill)
        self.loot_delay_spin.setValue(c.loot_delay_ms)
        self.chk_attack_spawn.setChecked(c.attack_on_spawn)
        self.chk_special.setChecked(c.use_special_attack)
        self.special_spin.setValue(c.special_at_percent)
        self.chk_walk.setChecked(c.walk_to_npc)
