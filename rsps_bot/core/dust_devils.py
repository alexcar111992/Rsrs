"""Dust Devils farming automation.

Workflow:
  1. Right-click around viewport to find a Dust Devil by name
  2. Click "Attack Dust devil" from the right-click menu
  3. Wait for it to die (monitor HP bar near player)
  4. INSTANTLY attack the next one (zero delay)
  5. Repeat

Never attacks desert lizards or other NPCs - only clicks the
"Attack Dust devil" menu option which matches by NPC name.
No prayers/eating/potting needed (already set by player).
"""

import random
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Tuple

import cv2
import numpy as np

from .config import DustDevilsSettings
from .interface_detector import GameState, InterfaceDetector, InterfaceSnapshot
from .mouse_controller import MouseController


# Orange color range for dust devils (various shades)
DUST_DEVIL_ORANGE = ((140, 70, 20), (255, 180, 90))


class DustDevilState(Enum):
    SEARCHING = auto()     # Looking for a dust devil to attack
    IN_COMBAT = auto()     # Fighting one, waiting for it to die


@dataclass
class DustDevilStats:
    kills: int = 0
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
        return (self.kills / mins) * 60.0


class DustDevilsSystem:
    """Farms Dust Devils by right-click attacking them.

    Uses orange color detection to prioritize clicking on actual dust devils
    instead of empty space. Falls back to grid search if no orange blobs found.
    """

    # How close an HP bar must be to count as player's combat
    COMBAT_RADIUS_X = 200
    COMBAT_RADIUS_Y = 150

    # Search cooldown - very short for instant re-attack
    SEARCH_COOLDOWN = 0.4

    def __init__(self, mouse: MouseController, detector: InterfaceDetector):
        self.mouse = mouse
        self.detector = detector

        self.state = DustDevilState.SEARCHING
        self.stats = DustDevilStats()
        self.settings = DustDevilsSettings()

        self._last_search_time = 0.0
        self._search_index = 0
        self._grid_positions: List[Tuple[int, int]] = []

    def configure(self, settings: DustDevilsSettings):
        self.settings = settings

    def tick(self, image: np.ndarray, snap: InterfaceSnapshot) -> str:
        """Run one cycle. Right-click attacks dust devils, waits for kills."""
        if not self.settings.enabled:
            return ""

        # Allow UNKNOWN game state (RSPS clients often don't match detection)
        if snap.game_state not in (GameState.IN_GAME, GameState.UNKNOWN):
            return f"Not in game ({snap.game_state.name})"

        now = time.time()
        player_fighting = self._is_player_in_combat(snap)

        if self.state == DustDevilState.IN_COMBAT:
            if not player_fighting:
                # Kill detected - instantly go back to searching
                self.stats.kills += 1
                self.state = DustDevilState.SEARCHING
                self._search_index = 0
                self._grid_positions = []
                # No delay - attack next one immediately
                return f"Kill #{self.stats.kills}! ({self.stats.kills_per_hour:.0f}/hr) - finding next..."

            return f"Fighting Dust Devil... HP: {snap.target_hp_percent:.0f}%"

        # SEARCHING state
        if player_fighting:
            # We're already in combat (maybe clicked one last tick)
            self.state = DustDevilState.IN_COMBAT
            return "In combat with Dust Devil..."

        # Search cooldown for responsiveness
        if now - self._last_search_time < self.SEARCH_COOLDOWN:
            return "Searching for Dust Devil..."

        return self._search_and_attack(image, snap)

    def _search_and_attack(self, image: np.ndarray, snap: InterfaceSnapshot) -> str:
        """Find and right-click attack a Dust Devil.

        Strategy:
        1. First try orange blob detection - click directly on dust devils
        2. Fall back to grid search if no orange blobs found
        """
        # Try orange blob detection first - find dust devils by color
        viewport = self.detector.crop_region(image, "viewport")
        vp_x1, vp_y1, _, _ = self.detector.region_px(
            "viewport", snap.client_width, snap.client_height
        )

        orange_blobs = InterfaceDetector._find_color_blobs(
            viewport, DUST_DEVIL_ORANGE, min_area=80, max_area=8000
        )

        if orange_blobs:
            # Pick a random orange blob to avoid always clicking the same one
            blob = random.choice(orange_blobs)
            tx = vp_x1 + blob[0] + random.randint(-5, 5)
            ty = vp_y1 + blob[1] + random.randint(-5, 5)

            self.mouse.right_click(tx, ty)
            time.sleep(random.uniform(0.15, 0.25))
            # Click "Attack Dust devil" - 2nd menu option (~30px below)
            self.mouse.click(tx, ty + 30)

            self._last_search_time = time.time()
            return f"Attacking orange NPC at ({tx}, {ty})"

        # Fallback: grid search around viewport center
        cx, cy = snap.viewport_center

        if not self._grid_positions:
            offsets = [
                (0, 0), (0, -50), (0, 50), (-60, 0), (60, 0),
                (-60, -50), (60, -50), (-60, 50), (60, 50),
                (0, -100), (0, 100), (-120, 0), (120, 0),
                (-120, -80), (120, -80), (-120, 80), (120, 80),
                (0, -150), (0, 150), (-180, 0), (180, 0),
            ]
            self._grid_positions = [(cx + ox, cy + oy) for ox, oy in offsets]

        if self._search_index >= len(self._grid_positions):
            self._search_index = 0

        sx, sy = self._grid_positions[self._search_index]
        self._search_index += 1

        sx += random.randint(-8, 8)
        sy += random.randint(-8, 8)

        self.mouse.right_click(sx, sy)
        time.sleep(random.uniform(0.15, 0.25))
        self.mouse.click(sx, sy + 30)

        self._last_search_time = time.time()
        return f"Grid searching... (pos {self._search_index}/{len(self._grid_positions)})"

    def _is_player_in_combat(self, snap: InterfaceSnapshot) -> bool:
        """Check if the PLAYER is in combat (HP bar near viewport center).

        Wider radius than Easter event since dust devils are spread around
        and the player may be standing at different positions.
        """
        if not snap.npc_hp_bars:
            return False

        cx, cy = snap.viewport_center

        for bar_x, bar_y, bar_w, bar_h, bar_hp in snap.npc_hp_bars:
            bx = bar_x + bar_w // 2
            by = bar_y + bar_h // 2

            dx = abs(bx - cx)
            dy = cy - by  # HP bars appear above the NPC

            if dx < self.COMBAT_RADIUS_X and 0 < dy < self.COMBAT_RADIUS_Y:
                return True

        return False

    def reset(self):
        self.state = DustDevilState.SEARCHING
        self.stats = DustDevilStats()
        self.stats.start_time = time.time()
        self._last_search_time = 0.0
        self._search_index = 0
        self._grid_positions = []
