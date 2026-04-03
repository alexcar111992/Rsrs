"""Combat / NPC tab - user configures who to fight and how."""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QLineEdit, QSpinBox, QComboBox, QCheckBox, QPushButton,
    QSlider, QScrollArea, QFrame,
)
from PyQt5.QtCore import Qt

from rsps_bot.core.config import NpcTarget, CombatSettings, NPC_ACTIONS


class NpcTargetRow(QFrame):
    """One row for configuring a single NPC target."""

    def __init__(self, index: int = 1):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)

        lay.addWidget(QLabel(f"#{index}"))

        lay.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Rock Crab, Guard, Cow...")
        self.name_edit.setMinimumWidth(140)
        lay.addWidget(self.name_edit, 1)

        lay.addWidget(QLabel("HP:"))
        self.hp_spin = QSpinBox()
        self.hp_spin.setRange(1, 100000)
        self.hp_spin.setValue(100)
        lay.addWidget(self.hp_spin)

        lay.addWidget(QLabel("Action:"))
        self.action_combo = QComboBox()
        self.action_combo.addItems(NPC_ACTIONS)
        lay.addWidget(self.action_combo)

        lay.addWidget(QLabel("Priority:"))
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["1 (Highest)", "2", "3", "4", "5 (Lowest)"])
        lay.addWidget(self.priority_combo)

        self.spawn_check = QCheckBox("Re-attack on spawn")
        self.spawn_check.setChecked(True)
        lay.addWidget(self.spawn_check)

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
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # NPC Targets section
        npc_group = QGroupBox("NPC Targets (type the NPC name, set its HP, pick action)")
        npc_lay = QVBoxLayout(npc_group)

        self.target_rows = []
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.targets_layout = QVBoxLayout(scroll_widget)
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

        # Add one default row
        self._add_target_row()

        # Combat Settings section
        settings_group = QGroupBox("Combat Settings")
        sg = QHBoxLayout(settings_group)

        # Left column
        left = QVBoxLayout()
        self.chk_eat = QCheckBox("Eat food when HP low")
        self.chk_eat.setChecked(True)
        left.addWidget(self.chk_eat)

        hp_row = QHBoxLayout()
        hp_row.addWidget(QLabel("Eat at HP %:"))
        self.eat_slider = QSlider(Qt.Horizontal)
        self.eat_slider.setRange(5, 95)
        self.eat_slider.setValue(50)
        self.eat_pct_label = QLabel("50%")
        self.eat_slider.valueChanged.connect(lambda v: self.eat_pct_label.setText(f"{v}%"))
        hp_row.addWidget(self.eat_slider)
        hp_row.addWidget(self.eat_pct_label)
        left.addLayout(hp_row)

        food_row = QHBoxLayout()
        food_row.addWidget(QLabel("Food in slots:"))
        self.food_slots_edit = QLineEdit("25, 26, 27, 28")
        self.food_slots_edit.setPlaceholderText("e.g. 25, 26, 27, 28")
        food_row.addWidget(self.food_slots_edit)
        left.addLayout(food_row)

        self.chk_potions = QCheckBox("Use potions")
        left.addWidget(self.chk_potions)

        pot_row = QHBoxLayout()
        pot_row.addWidget(QLabel("Potion slots:"))
        self.potion_slots_edit = QLineEdit("")
        self.potion_slots_edit.setPlaceholderText("e.g. 1, 2, 3")
        pot_row.addWidget(self.potion_slots_edit)
        left.addLayout(pot_row)

        sg.addLayout(left)

        # Right column
        right = QVBoxLayout()
        self.chk_loot = QCheckBox("Loot after kill")
        self.chk_loot.setChecked(True)
        right.addWidget(self.chk_loot)

        loot_delay_row = QHBoxLayout()
        loot_delay_row.addWidget(QLabel("Loot delay (ms):"))
        self.loot_delay_spin = QSpinBox()
        self.loot_delay_spin.setRange(0, 5000)
        self.loot_delay_spin.setValue(500)
        loot_delay_row.addWidget(self.loot_delay_spin)
        right.addLayout(loot_delay_row)

        self.chk_attack_spawn = QCheckBox("Attack new NPC immediately after kill")
        self.chk_attack_spawn.setChecked(True)
        right.addWidget(self.chk_attack_spawn)

        self.chk_special = QCheckBox("Use special attack")
        right.addWidget(self.chk_special)

        spec_row = QHBoxLayout()
        spec_row.addWidget(QLabel("Special at %:"))
        self.special_spin = QSpinBox()
        self.special_spin.setRange(10, 100)
        self.special_spin.setValue(100)
        self.special_spin.setSingleStep(10)
        spec_row.addWidget(self.special_spin)
        right.addLayout(spec_row)

        self.chk_walk = QCheckBox("Walk to NPC if not nearby")
        self.chk_walk.setChecked(True)
        right.addWidget(self.chk_walk)

        sg.addLayout(right)
        layout.addWidget(settings_group)

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
        # Clear existing
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
