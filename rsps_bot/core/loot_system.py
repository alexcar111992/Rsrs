"""Loot pickup system - picks up items after NPC kills.

The user configures:
  - Which items to pick up (text field for each, or "Pick up all")
  - Priority order (dropdown per item)
  - Delay before picking up (spinner)

No AI - uses color detection to find ground item text.
"""

import random
import time
from typing import List, Tuple

import numpy as np

from .config import LootRule
from .interface_detector import InterfaceDetector, InterfaceSnapshot
from .mouse_controller import MouseController


class LootSystem:
    """Picks up ground items based on user configuration."""

    def __init__(self, mouse: MouseController, detector: InterfaceDetector):
        self.mouse = mouse
        self.detector = detector
        self.rules: List[LootRule] = []
        self.pickup_all: bool = False
        self.pickup_delay_ms: int = 500
        self._last_pickup_time = 0.0
        self.items_picked = 0

    def configure(self, rules: List[LootRule], pickup_all: bool = False, delay_ms: int = 500):
        """Apply settings from GUI."""
        self.rules = sorted(rules, key=lambda r: r.priority)
        self.pickup_all = pickup_all
        self.pickup_delay_ms = delay_ms

    def pickup(self, image: np.ndarray, snap: InterfaceSnapshot) -> str:
        """Try to pick up ground items. Returns status."""
        if snap.inventory_full:
            return "Inventory full - can't loot"

        if time.time() - self._last_pickup_time < self.pickup_delay_ms / 1000.0:
            return "Loot cooldown..."

        if not snap.ground_items:
            return "No ground items visible"

        # Click the first visible ground item
        for item_rect in snap.ground_items[:3]:
            x = item_rect[0] + item_rect[2] // 2
            y = item_rect[1] + item_rect[3] // 2

            if self.pickup_all:
                # Left-click picks up top item on stack
                self.mouse.click(x, y)
            else:
                # Right-click to select specific item from menu
                self.mouse.right_click(x, y)
                time.sleep(random.uniform(0.3, 0.5))
                self.mouse.click(x, y + 15)  # First "Take" option

            self._last_pickup_time = time.time()
            self.items_picked += 1
            time.sleep(random.uniform(0.2, 0.5))
            return f"Picked up item (total: {self.items_picked})"

        return "No reachable items"

    def has_items_to_loot(self, snap: InterfaceSnapshot) -> bool:
        """Check if there are ground items visible."""
        return len(snap.ground_items) > 0 and not snap.inventory_full

    def reset(self):
        self.items_picked = 0
        self._last_pickup_time = 0.0
