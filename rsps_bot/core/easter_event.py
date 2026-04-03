"""Easter Baby Mole event automation.

Full workflow:
  1. Turn on Protect from Melee + Piety (or quick prayers)
  2. Sip Super Combat potion (4/3/2/1)
  3. Click Spade in inventory to spawn Easter Baby Mole
  4. Right-click > Attack Easter baby mole
  5. Eat food if HP low during fight
  6. When it dies: loot ALL items on the ground
  7. Check for pet Mintor on ground - pick it up
  8. If Mintor appears in inventory - click to re-summon
  9. Repeat from step 2
"""

import random
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional, Tuple

import numpy as np

from .config import EasterEventSettings
from .interface_detector import GameState, InterfaceDetector, InterfaceSnapshot
from .mouse_controller import MouseController


class EasterState(Enum):
    IDLE = auto()
    ACTIVATING_PRAYERS = auto()
    SIPPING_POTION = auto()
    CLICKING_SPADE = auto()
    WAITING_FOR_SPAWN = auto()
    ATTACKING_MOLE = auto()
    IN_COMBAT = auto()
    LOOTING = auto()
    PICKING_UP_PET = auto()
    RESUMMONING_PET = auto()
    EATING = auto()


@dataclass
class EasterStats:
    moles_killed: int = 0
    food_eaten: int = 0
    potions_sipped: int = 0
    pet_pickups: int = 0
    items_looted: int = 0
    start_time: float = 0.0

    @property
    def runtime_minutes(self) -> float:
        if self.start_time <= 0:
            return 0.0
        return (time.time() - self.start_time) / 60.0

    @property
    def kills_per_hour(self) -> float:
        mins = self.runtime_minutes
        if mins <= 0:
            return 0.0
        return (self.moles_killed / mins) * 60.0


class EasterEventSystem:
    """Automates the Easter Baby Mole event."""

    def __init__(self, mouse: MouseController, detector: InterfaceDetector):
        self.mouse = mouse
        self.detector = detector

        self.state = EasterState.IDLE
        self.stats = EasterStats()
        self.settings = EasterEventSettings()

        self._last_action_time = 0.0
        self._prayers_active = False
        self._potion_sipped = False
        self._kills_since_pet_check = 0
        self._search_index = 0
        self._loot_attempts = 0

    def configure(self, settings: EasterEventSettings):
        self.settings = settings

    def tick(self, image: np.ndarray, snap: InterfaceSnapshot) -> str:
        """Run one cycle of the Easter event loop."""
        if not self.settings.enabled:
            return ""

        if snap.game_state != GameState.IN_GAME:
            return f"Not in game ({snap.game_state.name})"

        # Always check: eat food if HP low
        if self.settings.eat_food and snap.player_hp_percent <= self.settings.eat_at_hp_percent:
            if time.time() - self._last_action_time > 1.8:
                return self._eat_food(snap)

        # State machine
        if self.state == EasterState.IDLE:
            return self._start_cycle(snap)
        elif self.state == EasterState.ACTIVATING_PRAYERS:
            return self._activate_prayers(snap)
        elif self.state == EasterState.SIPPING_POTION:
            return self._sip_potion(snap)
        elif self.state == EasterState.CLICKING_SPADE:
            return self._click_spade(snap)
        elif self.state == EasterState.WAITING_FOR_SPAWN:
            return self._wait_for_spawn(snap)
        elif self.state == EasterState.ATTACKING_MOLE:
            return self._attack_mole(snap)
        elif self.state == EasterState.IN_COMBAT:
            return self._handle_combat(snap)
        elif self.state == EasterState.LOOTING:
            return self._loot_all(snap)
        elif self.state == EasterState.PICKING_UP_PET:
            return self._pickup_pet(snap)
        elif self.state == EasterState.RESUMMONING_PET:
            return self._resummon_pet(snap)

        return f"Easter: {self.state.name}"

    def _start_cycle(self, snap: InterfaceSnapshot) -> str:
        """Begin a new kill cycle."""
        # Step 1: Prayers (if not already active or first cycle)
        if self.settings.protect_melee or self.settings.piety:
            if not self._prayers_active:
                self.state = EasterState.ACTIVATING_PRAYERS
                return "Starting cycle - activating prayers"

        # Step 2: Potion
        if self.settings.sip_super_combat and not self._potion_sipped:
            self.state = EasterState.SIPPING_POTION
            return "Starting cycle - sipping potion"

        # Step 3: Spade
        self.state = EasterState.CLICKING_SPADE
        return "Starting cycle - clicking spade"

    def _activate_prayers(self, snap: InterfaceSnapshot) -> str:
        """Turn on prayers by clicking quick prayers orb."""
        w, h = snap.client_width, snap.client_height

        if self.settings.use_quick_prayers:
            # Click the prayer orb (near HP orb on the right side)
            prayer_orb_x = int(w * 0.737)
            prayer_orb_y = int(h * 0.30)
            self.mouse.click(prayer_orb_x, prayer_orb_y)
            time.sleep(random.uniform(0.4, 0.7))
        else:
            # Click individual prayer slots in the prayer book
            # User would need to have prayer tab open
            # For now just click quick prayers as it's most common
            prayer_orb_x = int(w * 0.737)
            prayer_orb_y = int(h * 0.30)
            self.mouse.click(prayer_orb_x, prayer_orb_y)
            time.sleep(random.uniform(0.4, 0.7))

        self._prayers_active = True
        self._last_action_time = time.time()

        # Next: potion or spade
        if self.settings.sip_super_combat and not self._potion_sipped:
            self.state = EasterState.SIPPING_POTION
        else:
            self.state = EasterState.CLICKING_SPADE

        return "Prayers activated (Protect Melee + Piety)"

    def _sip_potion(self, snap: InterfaceSnapshot) -> str:
        """Sip a Super Combat potion from inventory."""
        w, h = snap.client_width, snap.client_height
        slot_centers = self.detector.get_inventory_slot_centers(w, h)

        for slot_num in self.settings.super_combat_slots:
            idx = slot_num - 1
            if 0 <= idx < len(slot_centers):
                cx, cy = slot_centers[idx]
                self.mouse.click(cx, cy)
                time.sleep(random.uniform(0.3, 0.5))
                self.stats.potions_sipped += 1
                self._potion_sipped = True
                self._last_action_time = time.time()
                self.state = EasterState.CLICKING_SPADE
                return f"Sipped Super Combat (slot {slot_num})"

        # No potion found, skip
        self._potion_sipped = True
        self.state = EasterState.CLICKING_SPADE
        return "No Super Combat potion found, skipping"

    def _click_spade(self, snap: InterfaceSnapshot) -> str:
        """Click the spade in inventory to spawn the Easter Baby Mole."""
        w, h = snap.client_width, snap.client_height
        slot_centers = self.detector.get_inventory_slot_centers(w, h)

        idx = self.settings.spade_slot - 1
        if 0 <= idx < len(slot_centers):
            cx, cy = slot_centers[idx]
            self.mouse.click(cx, cy)
            time.sleep(random.uniform(0.8, 1.2))
            self._last_action_time = time.time()
            self.state = EasterState.WAITING_FOR_SPAWN
            return f"Clicked spade (slot {self.settings.spade_slot}) - spawning mole"

        return "Spade slot not configured correctly!"

    def _wait_for_spawn(self, snap: InterfaceSnapshot) -> str:
        """Wait for the Easter Baby Mole to appear."""
        if time.time() - self._last_action_time > 2.0:
            self.state = EasterState.ATTACKING_MOLE
            self._search_index = 0
            return "Mole should have spawned, attacking"

        return "Waiting for mole to spawn..."

    def _attack_mole(self, snap: InterfaceSnapshot) -> str:
        """Right-click to find and attack the Easter Baby Mole by name."""
        cx, cy = snap.viewport_center
        npc_name = self.settings.npc_name

        # Search positions around viewport center
        offsets = [
            (0, 0), (0, -30), (0, 30), (-40, 0), (40, 0),
            (-40, -30), (40, -30), (-40, 30), (40, 30),
            (0, -60), (0, 60), (-80, 0), (80, 0),
        ]

        if self._search_index >= len(offsets):
            self._search_index = 0

        ox, oy = offsets[self._search_index]
        self._search_index += 1

        sx = cx + ox + random.randint(-8, 8)
        sy = cy + oy + random.randint(-8, 8)

        # Right-click to open menu
        self.mouse.right_click(sx, sy)
        time.sleep(random.uniform(0.3, 0.5))

        # Click "Attack <npc_name>" option (2nd entry in menu, y + 30)
        self.mouse.click(sx, sy + 30)

        self._last_action_time = time.time()
        self.state = EasterState.IN_COMBAT

        return f"Right-click > Attack {npc_name}"

    def _handle_combat(self, snap: InterfaceSnapshot) -> str:
        """Monitor combat, eat if needed, wait for kill."""
        if not snap.in_combat:
            # Check if we actually entered combat at all
            if time.time() - self._last_action_time < 3.0:
                return "Waiting for combat to start..."

            if time.time() - self._last_action_time < 5.0 and not snap.in_combat:
                # Didn't connect, try attacking again
                self.state = EasterState.ATTACKING_MOLE
                return "Didn't hit mole, retrying..."

            # Mole died!
            self.stats.moles_killed += 1
            self._kills_since_pet_check += 1
            self._potion_sipped = False  # Re-sip next cycle
            self._loot_attempts = 0
            self.state = EasterState.LOOTING

            return f"Mole #{self.stats.moles_killed} killed! Looting..."

        return f"Fighting Easter Baby Mole... Target HP: {snap.target_hp_percent:.0f}%"

    def _loot_all(self, snap: InterfaceSnapshot) -> str:
        """Pick up ALL items on the ground."""
        time.sleep(self.settings.loot_delay_ms / 1000.0)

        # Click on ground items - they appear near where the NPC died (viewport center)
        cx, cy = snap.viewport_center

        if self._loot_attempts < 8:
            # Click in a pattern around where items dropped
            offsets = [
                (0, 10), (0, -10), (15, 0), (-15, 0),
                (10, 10), (-10, 10), (10, -10), (-10, -10),
            ]
            ox, oy = offsets[self._loot_attempts % len(offsets)]
            self.mouse.click(cx + ox + random.randint(-5, 5), cy + oy + random.randint(-5, 5))
            time.sleep(random.uniform(0.3, 0.5))
            self._loot_attempts += 1
            self.stats.items_looted += 1
            return f"Picking up loot (item {self._loot_attempts})"

        # Done looting, check if we need to handle pet
        if self.settings.pet_pickup and self._kills_since_pet_check >= self.settings.pet_check_interval:
            self.state = EasterState.PICKING_UP_PET
            self._kills_since_pet_check = 0
            return "Checking for pet..."
        else:
            # Start next cycle
            self.state = EasterState.IDLE
            time.sleep(self.settings.delay_between_kills_ms / 1000.0)
            return "Loot done, starting next cycle"

    def _pickup_pet(self, snap: InterfaceSnapshot) -> str:
        """Try to pick up pet Mintor from the ground."""
        cx, cy = snap.viewport_center

        # Right-click near character to look for pet
        offsets = [(0, 20), (20, 20), (-20, 20), (0, 40), (20, 0), (-20, 0)]
        for ox, oy in offsets:
            self.mouse.right_click(cx + ox, cy + oy)
            time.sleep(random.uniform(0.3, 0.5))
            # Click "Pick-up" or "Take" option
            self.mouse.click(cx + ox, cy + oy + 30)
            time.sleep(random.uniform(0.3, 0.5))

        self.stats.pet_pickups += 1
        self._last_action_time = time.time()

        if self.settings.pet_resummon:
            self.state = EasterState.RESUMMONING_PET
            return f"Picked up {self.settings.pet_name}, re-summoning..."
        else:
            self.state = EasterState.IDLE
            return f"Picked up {self.settings.pet_name}"

    def _resummon_pet(self, snap: InterfaceSnapshot) -> str:
        """Click the pet in inventory to re-summon it."""
        w, h = snap.client_width, snap.client_height
        slot_centers = self.detector.get_inventory_slot_centers(w, h)

        # The pet will be in one of the last inventory slots (most recently picked up)
        # Check last few slots
        for idx in range(len(slot_centers) - 1, max(len(slot_centers) - 6, -1), -1):
            cx, cy = slot_centers[idx]
            self.mouse.click(cx, cy)
            time.sleep(random.uniform(0.3, 0.5))

        self._last_action_time = time.time()
        self.state = EasterState.IDLE
        time.sleep(random.uniform(0.5, 1.0))
        return f"{self.settings.pet_name} re-summoned! Starting next cycle"

    def _eat_food(self, snap: InterfaceSnapshot) -> str:
        """Eat food during combat."""
        w, h = snap.client_width, snap.client_height
        slot_centers = self.detector.get_inventory_slot_centers(w, h)

        for slot_num in self.settings.food_slots:
            idx = slot_num - 1
            if 0 <= idx < len(slot_centers):
                cx, cy = slot_centers[idx]
                self.mouse.click(cx, cy)
                self._last_action_time = time.time()
                self.stats.food_eaten += 1
                return f"Eating food (slot {slot_num}) - HP: {snap.player_hp_percent:.0f}%"

        return "No food left!"

    def reset(self):
        self.state = EasterState.IDLE
        self.stats = EasterStats()
        self.stats.start_time = time.time()
        self._prayers_active = False
        self._potion_sipped = False
        self._kills_since_pet_check = 0
        self._search_index = 0
        self._loot_attempts = 0
