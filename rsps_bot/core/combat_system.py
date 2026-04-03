"""NPC combat system - fully driven by user GUI configuration.

The user tells the bot:
  - NPC name (typed in text field)
  - NPC max HP (spinner)
  - What action to use (dropdown: Attack, Talk-to, etc.)
  - Whether to re-attack on spawn (checkbox)
  - What food slots to eat from (multi-select)
  - At what HP% to eat (slider)

The bot uses this info + color detection to fight. No AI, no scripts.
"""

import random
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional, Tuple

import numpy as np

from .config import NpcTarget, CombatSettings
from .interface_detector import GameState, InterfaceDetector, InterfaceSnapshot
from .mouse_controller import MouseController


class CombatState(Enum):
    IDLE = auto()
    SEARCHING_FOR_NPC = auto()
    ATTACKING = auto()
    IN_COMBAT = auto()
    WAITING_FOR_LOOT = auto()
    EATING = auto()


@dataclass
class CombatStats:
    """Live stats shown in the GUI."""
    npcs_killed: int = 0
    food_eaten: int = 0
    potions_used: int = 0
    loot_picked: int = 0
    deaths: int = 0
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
        return (self.npcs_killed / mins) * 60.0


class CombatSystem:
    """Fights NPCs based on user configuration."""

    def __init__(self, mouse: MouseController, detector: InterfaceDetector):
        self.mouse = mouse
        self.detector = detector

        self.state = CombatState.IDLE
        self.stats = CombatStats()

        # Set from GUI
        self.targets: List[NpcTarget] = []
        self.settings = CombatSettings()

        self._last_attack_time = 0.0
        self._last_eat_time = 0.0
        self._search_click_cooldown = 2.0
        self._last_search_click = 0.0

    def configure(self, targets: List[NpcTarget], settings: CombatSettings):
        """Apply settings from GUI."""
        self.targets = sorted(targets, key=lambda t: t.priority)
        self.settings = settings

    def tick(self, image: np.ndarray, snap: InterfaceSnapshot) -> str:
        """Run one cycle of the combat loop. Returns a human-readable status."""
        if not self.targets:
            return "No NPC targets set"

        if snap.game_state != GameState.IN_GAME:
            return f"Not in game ({snap.game_state.name})"

        # Priority 1: Eat if HP is low (skip in Simple Mode)
        if not self.settings.simple_mode:
            if self.settings.eat_food and snap.player_hp_percent <= self.settings.eat_at_hp_percent:
                if time.time() - self._last_eat_time > 1.8:  # Eat tick cooldown
                    return self._eat_food(snap)

        # Priority 2: Drink potion if configured (skip in Simple Mode)
        if not self.settings.simple_mode and self.settings.use_potions and self.settings.potion_slots:
            # For now, drink when HP is below a threshold (user configured)
            if snap.player_hp_percent <= self.settings.drink_potion_value:
                return self._drink_potion(snap)

        # Combat state machine
        if self.state in (CombatState.IDLE, CombatState.SEARCHING_FOR_NPC):
            return self._search_and_attack(image, snap)
        elif self.state == CombatState.ATTACKING:
            return self._wait_for_combat(snap)
        elif self.state == CombatState.IN_COMBAT:
            return self._handle_combat(snap)
        elif self.state == CombatState.WAITING_FOR_LOOT:
            return self._handle_post_kill(snap)

        return f"State: {self.state.name}"

    def _search_and_attack(self, image: np.ndarray, snap: InterfaceSnapshot) -> str:
        """Find and attack an NPC."""
        self.state = CombatState.SEARCHING_FOR_NPC

        # Method 1: Click on an HP bar we can see (NPC is right there)
        if snap.npc_hp_bars:
            bar = snap.npc_hp_bars[0]
            # Click just below the HP bar to hit the NPC model
            target_x = bar[0] + bar[2] // 2
            target_y = bar[1] + 20
            self._do_attack_click(target_x, target_y)
            return f"Attacking NPC at HP bar ({bar[4]:.0f}%)"

        # Method 2: Click on minimap NPC dots
        if snap.minimap_npc_dots:
            dot = min(snap.minimap_npc_dots, key=lambda d: self._dist(d, snap.viewport_center))
            self.mouse.click(dot[0], dot[1])
            time.sleep(random.uniform(0.8, 1.5))
            return "Walking to NPC via minimap"

        # Method 3: Click near viewport center to search
        if time.time() - self._last_search_click > self._search_click_cooldown:
            cx, cy = snap.viewport_center
            # Random offset to scan different areas
            ox = random.randint(-80, 80)
            oy = random.randint(-60, 60)
            self.mouse.click(cx + ox, cy + oy)
            self._last_search_click = time.time()
            return "Scanning for NPCs..."

        return "Waiting for NPC to appear..."

    def _do_attack_click(self, x: int, y: int):
        """Perform the attack action on coordinates."""
        target = self.targets[0] if self.targets else NpcTarget()

        if target.action == "Attack":
            self.mouse.click(x, y)
        else:
            # Right-click menu for non-attack actions
            self.mouse.right_click(x, y)
            time.sleep(random.uniform(0.3, 0.6))
            self.mouse.click(x, y + 18)  # Click option in menu

        self._last_attack_time = time.time()
        self.state = CombatState.ATTACKING

    def _wait_for_combat(self, snap: InterfaceSnapshot) -> str:
        """We clicked to attack - wait for combat to start."""
        if snap.in_combat:
            self.state = CombatState.IN_COMBAT
            return "Combat started!"

        # Give it a few seconds
        if time.time() - self._last_attack_time > 4.0:
            self.state = CombatState.SEARCHING_FOR_NPC
            return "Attack didn't connect, re-searching"

        return "Engaging NPC..."

    def _handle_combat(self, snap: InterfaceSnapshot) -> str:
        """We're fighting - monitor HP and wait for kill."""
        if not snap.in_combat:
            # NPC died
            self.stats.npcs_killed += 1

            if self.settings.loot_after_kill:
                self.state = CombatState.WAITING_FOR_LOOT
                return f"Kill #{self.stats.npcs_killed}! Waiting for loot..."
            elif self.settings.attack_on_spawn:
                self.state = CombatState.SEARCHING_FOR_NPC
                return f"Kill #{self.stats.npcs_killed}! Finding next target"
            else:
                self.state = CombatState.IDLE
                return f"Kill #{self.stats.npcs_killed}!"

        return f"Fighting... Target HP: {snap.target_hp_percent:.0f}%"

    def _handle_post_kill(self, snap: InterfaceSnapshot) -> str:
        """After killing - pick up loot then re-engage."""
        # Wait for loot to appear
        time.sleep(self.settings.loot_delay_ms / 1000.0)

        if self.settings.attack_on_spawn:
            self.state = CombatState.SEARCHING_FOR_NPC
            return "Loot phase done, finding next NPC"

        self.state = CombatState.IDLE
        return "Loot phase done"

    def _eat_food(self, snap: InterfaceSnapshot) -> str:
        """Click a food item in inventory to eat."""
        w, h = snap.client_width, snap.client_height
        slot_centers = self.detector.get_inventory_slot_centers(w, h)

        for slot_num in self.settings.food_slots:
            idx = slot_num - 1  # Convert 1-based to 0-based
            if 0 <= idx < len(slot_centers):
                cx, cy = slot_centers[idx]
                self.mouse.click(cx, cy)
                self._last_eat_time = time.time()
                self.stats.food_eaten += 1
                return f"Eating food (slot {slot_num}) - HP: {snap.player_hp_percent:.0f}%"

        return "No food left!"

    def _drink_potion(self, snap: InterfaceSnapshot) -> str:
        """Click a potion in inventory."""
        w, h = snap.client_width, snap.client_height
        slot_centers = self.detector.get_inventory_slot_centers(w, h)

        for slot_num in self.settings.potion_slots:
            idx = slot_num - 1
            if 0 <= idx < len(slot_centers):
                cx, cy = slot_centers[idx]
                self.mouse.click(cx, cy)
                self.stats.potions_used += 1
                return f"Drinking potion (slot {slot_num})"

        return "No potions left!"

    def reset(self):
        """Reset for a fresh session."""
        self.state = CombatState.IDLE
        self.stats = CombatStats()
        self.stats.start_time = time.time()

    @staticmethod
    def _dist(a: Tuple[int, int], b: Tuple[int, int]) -> float:
        return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
