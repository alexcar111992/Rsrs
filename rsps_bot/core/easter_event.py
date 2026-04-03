"""Easter Baby Mole event automation - detection based.

Correct workflow:
  1. Check prayers are on -> toggle quick prayers if not
  2. Click spade in inventory -> mole spawns and AUTO-ATTACKS the player
  3. Wait for combat to finish (mole dies from player auto-retaliate)
  4. Short delay, then click spade again
  5. Repeat

IMPORTANT:
  - The bot NEVER attacks the mole. The mole auto-attacks the player.
  - The bot ignores other players' moles (filters HP bars by position).
  - No looting (necklace auto-banks), no eating/potting (unlimited prayers).
"""

import random
import time
from dataclasses import dataclass
from enum import Enum, auto

import numpy as np

from .config import EasterEventSettings
from .interface_detector import GameState, InterfaceDetector, InterfaceSnapshot
from .mouse_controller import MouseController


class EasterState(Enum):
    IDLE = auto()                 # Ready to click spade
    WAITING_FOR_SPAWN = auto()    # Spade clicked, waiting for mole to engage
    IN_COMBAT = auto()            # Player is fighting their mole


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
    """Automates the Easter Baby Mole event using screen detection.

    Never attacks - the mole auto-attacks the player when spawned.
    Uses player-specific combat detection to ignore other players' moles.
    """

    # How close an HP bar must be to viewport center to count as "player's combat"
    COMBAT_RADIUS_X = 150  # pixels horizontal
    COMBAT_RADIUS_Y = 120  # pixels vertical (above center - HP bars appear above NPCs)

    def __init__(self, mouse: MouseController, detector: InterfaceDetector):
        self.mouse = mouse
        self.detector = detector

        self.state = EasterState.IDLE
        self.stats = EasterStats()
        self.settings = EasterEventSettings()

        self._spade_click_time = 0.0
        self._last_kill_time = 0.0
        self._prayer_check_time = 0.0

    def configure(self, settings: EasterEventSettings):
        self.settings = settings

    def tick(self, image: np.ndarray, snap: InterfaceSnapshot) -> str:
        """Run one cycle. Decides what to do based on what it SEES."""
        if not self.settings.enabled:
            return ""

        # Allow UNKNOWN game state through - RSPS clients often don't match
        # standard detection heuristics. Only block definite non-game states.
        if snap.game_state not in (GameState.IN_GAME, GameState.UNKNOWN):
            return f"Not in game ({snap.game_state.name})"

        now = time.time()

        # ── Prayer maintenance (non-blocking, with cooldown) ──────────
        if not snap.prayers_active and (now - self._prayer_check_time > 3.0):
            self._turn_on_prayers(snap)
            self._prayer_check_time = now
            # Don't return - still run the main state machine below

        # ── State machine ─────────────────────────────────────────────
        player_fighting = self._is_player_in_combat(snap)

        if self.state == EasterState.IDLE:
            # Wait for kill delay
            kill_delay = self.settings.delay_between_kills_ms / 1000.0
            if now - self._last_kill_time < kill_delay and self._last_kill_time > 0:
                remaining = kill_delay - (now - self._last_kill_time)
                return f"Waiting between kills... ({remaining:.1f}s)"

            # Click spade to spawn mole
            msg = self._click_spade(snap)
            self.state = EasterState.WAITING_FOR_SPAWN
            self._spade_click_time = now
            return msg

        elif self.state == EasterState.WAITING_FOR_SPAWN:
            # Check if player entered combat (mole spawned and attacked)
            if player_fighting:
                self.state = EasterState.IN_COMBAT
                return "Mole spawned! In combat - waiting for kill..."

            # Timeout - click spade again
            timeout = self.settings.spawn_timeout_ms / 1000.0
            elapsed = now - self._spade_click_time
            if elapsed > timeout:
                self.state = EasterState.IDLE
                return f"Spawn timeout ({timeout:.0f}s) - will retry..."

            return f"Waiting for mole to spawn... ({elapsed:.1f}s)"

        elif self.state == EasterState.IN_COMBAT:
            # Wait for combat to end (mole dies)
            if not player_fighting:
                self.stats.moles_killed += 1
                self.state = EasterState.IDLE
                self._last_kill_time = now
                return f"Kill #{self.stats.moles_killed}! ({self.stats.kills_per_hour:.0f}/hr)"

            hp = snap.target_hp_percent
            return f"Fighting... Target HP: {hp:.0f}%"

        return f"Unknown state: {self.state.name}"

    def _is_player_in_combat(self, snap: InterfaceSnapshot) -> bool:
        """Check if the PLAYER is in combat, not just any NPC visible.

        Filters HP bars by proximity to viewport center. The player's
        mole spawns on top of them, so its HP bar appears near the
        center of the viewport. Other players' moles are further away.
        """
        if not snap.npc_hp_bars:
            return False

        cx, cy = snap.viewport_center

        for bar_x, bar_y, bar_w, bar_h, bar_hp in snap.npc_hp_bars:
            # Center of the HP bar
            bx = bar_x + bar_w // 2
            by = bar_y + bar_h // 2

            # Check if this bar is near the player (viewport center)
            dx = abs(bx - cx)
            dy = cy - by  # HP bars are ABOVE the NPC, so bar_y < cy

            if dx < self.COMBAT_RADIUS_X and 0 < dy < self.COMBAT_RADIUS_Y:
                return True

        return False

    def _turn_on_prayers(self, snap: InterfaceSnapshot) -> str:
        """Click the quick prayers orb to turn prayers on."""
        w, h = snap.client_width, snap.client_height
        x1, y1, x2, y2 = self.detector.region_px("prayer_orb", w, h)
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        self.mouse.click(cx + random.randint(-3, 3), cy + random.randint(-3, 3))
        return "Turning on prayers..."

    def _click_spade(self, snap: InterfaceSnapshot) -> str:
        """Click the spade in inventory to spawn Easter Baby Mole."""
        w, h = snap.client_width, snap.client_height
        slot_centers = self.detector.get_inventory_slot_centers(w, h)

        idx = self.settings.spade_slot - 1
        if 0 <= idx < len(slot_centers):
            cx, cy = slot_centers[idx]
            self.mouse.click(cx + random.randint(-3, 3), cy + random.randint(-3, 3))
            return f"Clicked spade (slot {self.settings.spade_slot}) - spawning mole..."

        return f"ERROR: Spade slot {self.settings.spade_slot} out of range!"

    def reset(self):
        self.state = EasterState.IDLE
        self.stats = EasterStats()
        self.stats.start_time = time.time()
        self._spade_click_time = 0.0
        self._last_kill_time = 0.0
        self._prayer_check_time = 0.0
