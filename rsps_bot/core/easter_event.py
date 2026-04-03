"""Easter Baby Mole event automation - detection based.

Simple loop driven entirely by what the bot can SEE:
  1. Are prayers on?  No -> click quick prayers orb
  2. Is there an NPC? (HP bar visible or minimap dot)
     - Yes + not in combat -> right-click attack it
     - Yes + in combat     -> wait for kill
     - No                  -> click spade to spawn one
  3. Repeat

No looting (necklace auto-banks), no eating/potting (prayers are unlimited).
"""

import random
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

import numpy as np

from .config import EasterEventSettings
from .interface_detector import GameState, InterfaceDetector, InterfaceSnapshot
from .mouse_controller import MouseController


class EasterState(Enum):
    IDLE = auto()
    TURNING_ON_PRAYERS = auto()
    CLICKING_SPADE = auto()
    WAITING_FOR_SPAWN = auto()
    ATTACKING_MOLE = auto()
    IN_COMBAT = auto()


@dataclass
class EasterStats:
    moles_killed: int = 0
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
    """Automates the Easter Baby Mole event using screen detection."""

    def __init__(self, mouse: MouseController, detector: InterfaceDetector):
        self.mouse = mouse
        self.detector = detector

        self.state = EasterState.IDLE
        self.stats = EasterStats()
        self.settings = EasterEventSettings()

        self._last_action_time = 0.0
        self._search_index = 0
        self._was_in_combat = False  # Track combat -> not combat transition

    def configure(self, settings: EasterEventSettings):
        self.settings = settings

    def tick(self, image: np.ndarray, snap: InterfaceSnapshot) -> str:
        """Run one cycle. Decides what to do based on what it SEES."""
        if not self.settings.enabled:
            return ""

        if snap.game_state != GameState.IN_GAME:
            return f"Not in game ({snap.game_state.name})"

        now = time.time()

        # ── Step 1: Prayers must be on ────────────────────────────────
        if not snap.prayers_active:
            if now - self._last_action_time > 1.0:
                return self._turn_on_prayers(snap)
            return "Waiting to activate prayers..."

        # ── Step 2: Detect combat / NPC state ─────────────────────────
        has_npc = snap.in_combat or len(snap.npc_hp_bars) > 0

        # Detect kill: was fighting, now no HP bar
        if self._was_in_combat and not snap.in_combat:
            self.stats.moles_killed += 1
            self._was_in_combat = False
            self._search_index = 0
            # Small delay before next cycle
            delay = self.settings.delay_between_kills_ms / 1000.0
            time.sleep(delay + random.uniform(0.1, 0.3))
            return f"Mole #{self.stats.moles_killed} killed! ({self.stats.kills_per_hour:.0f}/hr)"

        # Currently fighting - just wait
        if snap.in_combat:
            self._was_in_combat = True
            self._last_action_time = now
            return f"Fighting... Target HP: {snap.target_hp_percent:.0f}%"

        # ── Step 3: No NPC visible - spawn one ───────────────────────
        # Check minimap for nearby NPC dots too
        has_nearby_npc = len(snap.minimap_npc_dots) > 0

        if not has_npc and not has_nearby_npc:
            if now - self._last_action_time > 1.5:
                return self._click_spade(snap)
            return "Waiting to dig..."

        # ── Step 4: NPC exists but not in combat - attack it ─────────
        if now - self._last_action_time > 1.5:
            return self._attack_mole(snap)

        return "Searching for mole..."

    def _turn_on_prayers(self, snap: InterfaceSnapshot) -> str:
        """Click the quick prayers orb to turn prayers on."""
        w, h = snap.client_width, snap.client_height
        # Prayer orb center from the prayer_orb region
        x1, y1, x2, y2 = self.detector.region_px("prayer_orb", w, h)
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        self.mouse.click(cx + random.randint(-3, 3), cy + random.randint(-3, 3))
        self._last_action_time = time.time()
        return "Turning on prayers..."

    def _click_spade(self, snap: InterfaceSnapshot) -> str:
        """Click the spade in inventory to spawn Easter Baby Mole."""
        w, h = snap.client_width, snap.client_height
        slot_centers = self.detector.get_inventory_slot_centers(w, h)

        idx = self.settings.spade_slot - 1
        if 0 <= idx < len(slot_centers):
            cx, cy = slot_centers[idx]
            self.mouse.click(cx + random.randint(-3, 3), cy + random.randint(-3, 3))
            self._last_action_time = time.time()
            return f"Clicking spade (slot {self.settings.spade_slot}) - spawning mole"

        return "Spade slot not configured!"

    def _attack_mole(self, snap: InterfaceSnapshot) -> str:
        """Right-click attack the mole. Searches around viewport center."""
        cx, cy = snap.viewport_center

        # If we can see an NPC HP bar, click near it
        if snap.npc_hp_bars:
            bar = snap.npc_hp_bars[0]
            tx = bar[0] + bar[2] // 2
            ty = bar[1] + 20  # Below the HP bar = on the NPC
            self.mouse.right_click(tx + random.randint(-5, 5), ty + random.randint(-5, 5))
            time.sleep(random.uniform(0.3, 0.5))
            self.mouse.click(tx + random.randint(-5, 5), ty + 30)  # "Attack" menu option
            self._last_action_time = time.time()
            return "Attacking mole (found HP bar)"

        # Otherwise search in a grid pattern around center
        offsets = [
            (0, 0), (0, -40), (0, 40), (-50, 0), (50, 0),
            (-50, -40), (50, -40), (-50, 40), (50, 40),
            (0, -80), (0, 80), (-100, 0), (100, 0),
        ]

        if self._search_index >= len(offsets):
            self._search_index = 0

        ox, oy = offsets[self._search_index]
        self._search_index += 1

        sx = cx + ox + random.randint(-8, 8)
        sy = cy + oy + random.randint(-8, 8)

        self.mouse.right_click(sx, sy)
        time.sleep(random.uniform(0.3, 0.5))
        self.mouse.click(sx, sy + 30)  # Click "Attack" option

        self._last_action_time = time.time()
        return f"Right-click searching for mole (pos {self._search_index})"

    def reset(self):
        self.state = EasterState.IDLE
        self.stats = EasterStats()
        self.stats.start_time = time.time()
        self._was_in_combat = False
        self._search_index = 0
        self._last_action_time = 0.0
