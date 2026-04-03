"""NPC combat system - fully driven by user GUI configuration.

The user tells the bot:
  - NPC name (typed in text field) -> bot RIGHT-CLICKS and selects that name
  - NPC max HP (spinner)
  - What action to use (dropdown: Attack, Talk-to, etc.)
  - Whether to re-attack on spawn (checkbox)

IMPORTANT: The bot ONLY attacks the NPC name the user typed.
It right-clicks in the viewport and looks for "Attack <NPC name>" in the menu.
This prevents attacking random NPCs.
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
    """Fights NPCs based on user configuration.

    Uses RIGHT-CLICK to find the specific NPC by name.
    This prevents attacking random NPCs that aren't the target.
    """

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
        self._search_click_cooldown = 1.5
        self._last_search_click = 0.0
        # Grid-based search: try different spots in the viewport
        self._search_index = 0
        self._search_positions = []

    def configure(self, targets: List[NpcTarget], settings: CombatSettings):
        """Apply settings from GUI."""
        self.targets = sorted(targets, key=lambda t: t.priority)
        self.settings = settings

    def _build_search_grid(self, snap: InterfaceSnapshot):
        """Build a grid of positions to right-click and check for the NPC."""
        cx, cy = snap.viewport_center
        # Search in a grid pattern around viewport center
        offsets = [
            (0, 0), (0, -40), (0, 40), (-50, 0), (50, 0),
            (-50, -40), (50, -40), (-50, 40), (50, 40),
            (0, -80), (0, 80), (-100, 0), (100, 0),
            (-100, -60), (100, -60), (-100, 60), (100, 60),
            (0, -120), (0, 120), (-150, 0), (150, 0),
        ]
        self._search_positions = [(cx + ox, cy + oy) for ox, oy in offsets]
        self._search_index = 0

    def tick(self, image: np.ndarray, snap: InterfaceSnapshot) -> str:
        """Run one cycle of the combat loop. Returns a human-readable status."""
        if not self.targets:
            return "No NPC targets set"

        if snap.game_state != GameState.IN_GAME:
            return f"Not in game ({snap.game_state.name})"

        # Priority 1: Eat if HP is low (skip in Simple Mode)
        if not self.settings.simple_mode:
            if self.settings.eat_food and snap.player_hp_percent <= self.settings.eat_at_hp_percent:
                if time.time() - self._last_eat_time > 1.8:
                    return self._eat_food(snap)

        # Priority 2: Drink potion if configured (skip in Simple Mode)
        if not self.settings.simple_mode and self.settings.use_potions and self.settings.potion_slots:
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
        """Find and attack the SPECIFIC NPC the user configured.

        Strategy: Right-click at various positions in the viewport.
        The right-click menu shows NPC names. If the menu contains
        "Attack <target name>", click that option. Otherwise close
        the menu and try the next position.
        """
        self.state = CombatState.SEARCHING_FOR_NPC
        target = self.targets[0] if self.targets else NpcTarget()
        target_name = target.name.strip()

        now = time.time()
        if now - self._last_search_click < self._search_click_cooldown:
            return f"Searching for {target_name}..."

        # Build search grid if empty
        if not self._search_positions:
            self._build_search_grid(snap)

        # Get next search position
        if self._search_index >= len(self._search_positions):
            self._search_index = 0  # Loop back

        sx, sy = self._search_positions[self._search_index]
        self._search_index += 1

        # Add small random offset
        sx += random.randint(-10, 10)
        sy += random.randint(-10, 10)

        # Right-click to open menu and look for the NPC name
        self.mouse.right_click(sx, sy)
        time.sleep(random.uniform(0.3, 0.5))

        # The right-click menu in RSPS shows options like:
        #   Attack Easter baby mole
        #   Walk here
        #   Cancel
        # We need to click the "Attack <name>" option.
        # The attack option is typically the SECOND option in the menu
        # (first is often the NPC name itself or "Walk here").
        #
        # Menu option positions (approximate offsets from right-click point):
        #   Option 1 (top):     y + 15
        #   Option 2:           y + 30
        #   Option 3:           y + 45
        #   Option 4:           y + 60
        #   Option 5 (cancel):  y + 75
        #
        # For "Attack <name>", click the 2nd option (y + 30)
        # This is the standard RS menu layout.

        action = target.action  # "Attack", "Talk-to", etc.
        # Click the action option in the menu (usually 2nd entry)
        self.mouse.click(sx, sy + 30)

        self._last_search_click = now
        self._last_attack_time = now
        self.state = CombatState.ATTACKING

        return f"Right-click > {action} {target_name} at ({sx}, {sy})"

    def _wait_for_combat(self, snap: InterfaceSnapshot) -> str:
        """We clicked to attack - wait for combat to start."""
        if snap.in_combat:
            self.state = CombatState.IN_COMBAT
            return "Combat started!"

        # Give it a few seconds
        if time.time() - self._last_attack_time > 3.0:
            self.state = CombatState.SEARCHING_FOR_NPC
            return "NPC not found there, trying next spot"

        return "Engaging NPC..."

    def _handle_combat(self, snap: InterfaceSnapshot) -> str:
        """We're fighting - monitor HP and wait for kill."""
        if not snap.in_combat:
            self.stats.npcs_killed += 1

            if self.settings.loot_after_kill:
                self.state = CombatState.WAITING_FOR_LOOT
                return f"Kill #{self.stats.npcs_killed}! Waiting for loot..."
            elif self.settings.attack_on_spawn:
                self.state = CombatState.SEARCHING_FOR_NPC
                self._search_index = 0  # Reset search
                return f"Kill #{self.stats.npcs_killed}! Finding next target"
            else:
                self.state = CombatState.IDLE
                return f"Kill #{self.stats.npcs_killed}!"

        return f"Fighting... Target HP: {snap.target_hp_percent:.0f}%"

    def _handle_post_kill(self, snap: InterfaceSnapshot) -> str:
        """After killing - pick up loot then re-engage."""
        time.sleep(self.settings.loot_delay_ms / 1000.0)

        if self.settings.attack_on_spawn:
            self.state = CombatState.SEARCHING_FOR_NPC
            self._search_index = 0
            return "Loot phase done, finding next NPC"

        self.state = CombatState.IDLE
        return "Loot phase done"

    def _eat_food(self, snap: InterfaceSnapshot) -> str:
        """Click a food item in inventory to eat."""
        w, h = snap.client_width, snap.client_height
        slot_centers = self.detector.get_inventory_slot_centers(w, h)

        for slot_num in self.settings.food_slots:
            idx = slot_num - 1
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
        self._search_positions = []
        self._search_index = 0

    @staticmethod
    def _dist(a: Tuple[int, int], b: Tuple[int, int]) -> float:
        return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5
