"""Easter Event tab - Easter Baby Mole boss automation.

Full workflow configured through simple checkboxes and slot numbers:
  1. Prayers on (Protect Melee + Piety)
  2. Sip Super Combat potion
  3. Click Spade to spawn mole
  4. Attack Easter Baby Mole
  5. Loot ALL drops
  6. Pick up pet Mintor + re-summon
  7. Repeat
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox, QLabel,
    QLineEdit, QSpinBox, QCheckBox, QScrollArea, QSlider, QHBoxLayout,
    QPushButton,
)
from PyQt5.QtCore import Qt, pyqtSignal

from rsps_bot.core.config import EasterEventSettings


class EasterEventTab(QWidget):
    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setSpacing(10)
        layout.setContentsMargins(8, 8, 8, 8)

        # Info
        info = QLabel(
            "Easter Baby Mole Event - automated boss farming.\n"
            "The bot will: activate prayers, sip potion, click spade to spawn mole,\n"
            "attack it, loot everything, pick up and re-summon your pet, then repeat."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #f9e2af; padding: 8px; font-size: 11px;")
        layout.addWidget(info)

        # ── Enable ────────────────────────────────────────────────────
        self.chk_enabled = QCheckBox("Enable Easter Event mode (overrides combat + skilling)")
        self.chk_enabled.setStyleSheet("color: #f9e2af; font-weight: bold; font-size: 13px; padding: 6px;")
        layout.addWidget(self.chk_enabled)

        # ── Prayers ───────────────────────────────────────────────────
        prayer_group = QGroupBox("Prayers")
        pf = QFormLayout(prayer_group)
        pf.setSpacing(12)
        pf.setContentsMargins(12, 24, 12, 12)

        self.chk_protect = QCheckBox("Enable Protect from Melee")
        self.chk_protect.setChecked(True)
        pf.addRow(self.chk_protect)

        self.chk_piety = QCheckBox("Enable Piety")
        self.chk_piety.setChecked(True)
        pf.addRow(self.chk_piety)

        self.chk_quick_prayers = QCheckBox("Use Quick Prayers orb (recommended - set up prayers first in-game)")
        self.chk_quick_prayers.setChecked(True)
        pf.addRow(self.chk_quick_prayers)

        layout.addWidget(prayer_group)

        # ── Potion ────────────────────────────────────────────────────
        pot_group = QGroupBox("Super Combat Potion")
        potf = QFormLayout(pot_group)
        potf.setSpacing(12)
        potf.setContentsMargins(12, 24, 12, 12)

        self.chk_potion = QCheckBox("Sip Super Combat potion before each fight")
        self.chk_potion.setChecked(True)
        potf.addRow(self.chk_potion)

        self.potion_slots_edit = QLineEdit("1, 2, 3, 4")
        self.potion_slots_edit.setPlaceholderText("Inventory slots with Super Combat potions (e.g. 1, 2, 3, 4)")
        self.potion_slots_edit.setMinimumHeight(28)
        potf.addRow("Potion slots:", self.potion_slots_edit)

        layout.addWidget(pot_group)

        # ── Spade + NPC ───────────────────────────────────────────────
        spawn_group = QGroupBox("Spawn & Attack")
        sf = QFormLayout(spawn_group)
        sf.setSpacing(12)
        sf.setContentsMargins(12, 24, 12, 12)

        self.spade_slot_spin = QSpinBox()
        self.spade_slot_spin.setRange(1, 28)
        self.spade_slot_spin.setValue(5)
        self.spade_slot_spin.setMaximumWidth(80)
        sf.addRow("Spade inventory slot:", self.spade_slot_spin)

        self.npc_name_edit = QLineEdit("Easter baby mole")
        self.npc_name_edit.setMinimumHeight(28)
        sf.addRow("NPC name:", self.npc_name_edit)

        layout.addWidget(spawn_group)

        # ── Loot ──────────────────────────────────────────────────────
        loot_group = QGroupBox("Loot")
        lf = QFormLayout(loot_group)
        lf.setSpacing(12)
        lf.setContentsMargins(12, 24, 12, 12)

        self.chk_loot_all = QCheckBox("Pick up ALL items on the ground after kill")
        self.chk_loot_all.setChecked(True)
        lf.addRow(self.chk_loot_all)

        self.loot_delay_spin = QSpinBox()
        self.loot_delay_spin.setRange(100, 5000)
        self.loot_delay_spin.setValue(600)
        self.loot_delay_spin.setSuffix(" ms")
        self.loot_delay_spin.setMaximumWidth(120)
        lf.addRow("Loot delay:", self.loot_delay_spin)

        layout.addWidget(loot_group)

        # ── Pet ───────────────────────────────────────────────────────
        pet_group = QGroupBox("Pet (Mintor)")
        petf = QFormLayout(pet_group)
        petf.setSpacing(12)
        petf.setContentsMargins(12, 24, 12, 12)

        self.pet_name_edit = QLineEdit("Mintor")
        self.pet_name_edit.setMinimumHeight(28)
        petf.addRow("Pet name:", self.pet_name_edit)

        self.chk_pet_pickup = QCheckBox("Pick up pet from ground when it appears")
        self.chk_pet_pickup.setChecked(True)
        petf.addRow(self.chk_pet_pickup)

        self.chk_pet_resummon = QCheckBox("Instantly re-summon pet from inventory after picking up")
        self.chk_pet_resummon.setChecked(True)
        petf.addRow(self.chk_pet_resummon)

        self.pet_check_spin = QSpinBox()
        self.pet_check_spin.setRange(1, 50)
        self.pet_check_spin.setValue(5)
        self.pet_check_spin.setMaximumWidth(80)
        petf.addRow("Check for pet every N kills:", self.pet_check_spin)

        layout.addWidget(pet_group)

        # ── Food ──────────────────────────────────────────────────────
        food_group = QGroupBox("Food (during fight)")
        ff = QFormLayout(food_group)
        ff.setSpacing(12)
        ff.setContentsMargins(12, 24, 12, 12)

        self.chk_eat = QCheckBox("Eat food during fight")
        self.chk_eat.setChecked(True)
        ff.addRow(self.chk_eat)

        hp_row = QHBoxLayout()
        self.eat_slider = QSlider(Qt.Horizontal)
        self.eat_slider.setRange(10, 90)
        self.eat_slider.setValue(50)
        self.eat_slider.setMaximumWidth(200)
        self.eat_label = QLabel("50%")
        self.eat_label.setMinimumWidth(35)
        self.eat_slider.valueChanged.connect(lambda v: self.eat_label.setText(f"{v}%"))
        hp_row.addWidget(self.eat_slider)
        hp_row.addWidget(self.eat_label)
        hp_row.addStretch()
        ff.addRow("Eat at HP %:", hp_row)

        self.food_slots_edit = QLineEdit("24, 25, 26, 27, 28")
        self.food_slots_edit.setPlaceholderText("Inventory slots with food")
        self.food_slots_edit.setMinimumHeight(28)
        ff.addRow("Food slots:", self.food_slots_edit)

        layout.addWidget(food_group)

        # ── Timing ────────────────────────────────────────────────────
        self.cycle_delay_spin = QSpinBox()
        self.cycle_delay_spin.setRange(0, 10000)
        self.cycle_delay_spin.setValue(1000)
        self.cycle_delay_spin.setSuffix(" ms")
        self.cycle_delay_spin.setMaximumWidth(120)
        timing_form = QFormLayout()
        timing_form.addRow("Delay between kills:", self.cycle_delay_spin)
        layout.addLayout(timing_form)

        # ── Per-tab Start / Stop ──────────────────────────────────────
        tab_btn_row = QHBoxLayout()
        self.btn_start = QPushButton("  START Easter Event  ")
        self.btn_start.setStyleSheet("background:#2a7a2a; color:white; font-size:12px; font-weight:bold; padding:7px 18px;")
        self.btn_start.clicked.connect(self.start_requested.emit)
        self.btn_stop = QPushButton("  STOP Easter Event  ")
        self.btn_stop.setStyleSheet("background:#a02020; color:white; font-size:12px; font-weight:bold; padding:7px 18px;")
        self.btn_stop.clicked.connect(self.stop_requested.emit)
        tab_btn_row.addWidget(self.btn_start)
        tab_btn_row.addWidget(self.btn_stop)
        tab_btn_row.addStretch()
        layout.addLayout(tab_btn_row)

        layout.addStretch()
        scroll.setWidget(inner)
        outer.addWidget(scroll)

    def _parse_slots(self, text: str):
        slots = []
        for part in text.split(","):
            p = part.strip()
            if p.isdigit():
                slots.append(int(p))
        return slots

    def get_settings(self) -> EasterEventSettings:
        return EasterEventSettings(
            enabled=self.chk_enabled.isChecked(),
            protect_melee=self.chk_protect.isChecked(),
            piety=self.chk_piety.isChecked(),
            use_quick_prayers=self.chk_quick_prayers.isChecked(),
            sip_super_combat=self.chk_potion.isChecked(),
            super_combat_slots=self._parse_slots(self.potion_slots_edit.text()),
            spade_slot=self.spade_slot_spin.value(),
            npc_name=self.npc_name_edit.text(),
            loot_all=self.chk_loot_all.isChecked(),
            loot_delay_ms=self.loot_delay_spin.value(),
            pet_name=self.pet_name_edit.text(),
            pet_pickup=self.chk_pet_pickup.isChecked(),
            pet_resummon=self.chk_pet_resummon.isChecked(),
            pet_check_interval=self.pet_check_spin.value(),
            delay_between_kills_ms=self.cycle_delay_spin.value(),
            eat_food=self.chk_eat.isChecked(),
            eat_at_hp_percent=self.eat_slider.value(),
            food_slots=self._parse_slots(self.food_slots_edit.text()),
        )

    def load_profile(self, profile):
        s = profile.easter_event
        self.chk_enabled.setChecked(s.enabled)
        self.chk_protect.setChecked(s.protect_melee)
        self.chk_piety.setChecked(s.piety)
        self.chk_quick_prayers.setChecked(s.use_quick_prayers)
        self.chk_potion.setChecked(s.sip_super_combat)
        self.potion_slots_edit.setText(", ".join(str(x) for x in s.super_combat_slots))
        self.spade_slot_spin.setValue(s.spade_slot)
        self.npc_name_edit.setText(s.npc_name)
        self.chk_loot_all.setChecked(s.loot_all)
        self.loot_delay_spin.setValue(s.loot_delay_ms)
        self.pet_name_edit.setText(s.pet_name)
        self.chk_pet_pickup.setChecked(s.pet_pickup)
        self.chk_pet_resummon.setChecked(s.pet_resummon)
        self.pet_check_spin.setValue(s.pet_check_interval)
        self.cycle_delay_spin.setValue(s.delay_between_kills_ms)
        self.chk_eat.setChecked(s.eat_food)
        self.eat_slider.setValue(s.eat_at_hp_percent)
        self.food_slots_edit.setText(", ".join(str(x) for x in s.food_slots))
