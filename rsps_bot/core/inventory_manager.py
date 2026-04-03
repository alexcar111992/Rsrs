"""Inventory manager - clicks items based on user-defined rules.

The user sets up each inventory slot through the GUI:
  - Slot number (dropdown 1-28)
  - What item is in it (text description)
  - Action (dropdown: Eat, Drop, Use, Wield, Bury, Use on NPC/Object)
  - Trigger (dropdown: When HP below %, On cooldown, Manual, Always)
  - Trigger value (spinner: the % or seconds)
  - Enabled (checkbox)

No scripts, no AI - the user tells the bot exactly what to do.
"""

import random
import time
from typing import List, Optional, Tuple

import numpy as np

from .config import InventorySlotAction, ITEM_ACTIONS
from .interface_detector import InterfaceDetector, InterfaceSnapshot
from .mouse_controller import MouseController


class InventoryManager:
    """Manages inventory interactions based on user-defined rules."""

    def __init__(self, mouse: MouseController, detector: InterfaceDetector):
        self.mouse = mouse
        self.detector = detector
        self.actions: List[InventorySlotAction] = []
        self._cooldowns: dict = {}  # slot_number -> last_action_time

    def configure(self, actions: List[InventorySlotAction]):
        """Apply settings from GUI."""
        self.actions = [a for a in actions if a.enabled]

    def tick(self, image: np.ndarray, snap: InterfaceSnapshot) -> Optional[str]:
        """Check all inventory rules and perform any that should trigger.

        Returns status message if an action was taken, None otherwise.
        """
        w, h = snap.client_width, snap.client_height
        slot_centers = self.detector.get_inventory_slot_centers(w, h)
        now = time.time()

        for action in self.actions:
            idx = action.slot_number - 1
            if idx < 0 or idx >= len(slot_centers):
                continue

            # Check trigger condition
            if not self._should_trigger(action, snap, now):
                continue

            cx, cy = slot_centers[idx]
            self._perform_action(action, cx, cy)
            self._cooldowns[action.slot_number] = now

            return f"Slot {action.slot_number}: {action.action} ({action.item_description})"

        return None

    def click_slot(self, slot_number: int, snap: InterfaceSnapshot, right_click: bool = False):
        """Directly click an inventory slot (1-28)."""
        w, h = snap.client_width, snap.client_height
        centers = self.detector.get_inventory_slot_centers(w, h)
        idx = slot_number - 1
        if 0 <= idx < len(centers):
            cx, cy = centers[idx]
            cx += random.randint(-3, 3)
            cy += random.randint(-3, 3)
            if right_click:
                self.mouse.right_click(cx, cy)
            else:
                self.mouse.click(cx, cy)

    def _should_trigger(self, action: InventorySlotAction, snap: InterfaceSnapshot, now: float) -> bool:
        """Check if an inventory action should trigger based on its condition."""
        trigger = action.trigger

        if trigger == "When HP below %":
            return snap.player_hp_percent <= action.trigger_value

        elif trigger == "On cooldown (seconds)":
            last = self._cooldowns.get(action.slot_number, 0)
            return (now - last) >= action.trigger_value

        elif trigger == "When inventory full":
            return snap.inventory_full

        elif trigger == "When not in combat":
            return not snap.in_combat

        elif trigger == "When in combat":
            return snap.in_combat

        elif trigger == "Always (every tick)":
            last = self._cooldowns.get(action.slot_number, 0)
            return (now - last) >= 1.0  # Max once per second

        return False

    def _perform_action(self, action: InventorySlotAction, cx: int, cy: int):
        """Perform the configured action on a slot."""
        act = action.action

        if act == "Left-click (Eat / Drink / Use)":
            self.mouse.click(cx, cy)
            time.sleep(random.uniform(0.2, 0.5))

        elif act.startswith("Right-click >"):
            self.mouse.right_click(cx, cy)
            time.sleep(random.uniform(0.3, 0.6))
            # Click the appropriate menu option
            # Drop is usually ~60px below, Use ~30px, Wield ~45px, Bury ~60px
            offsets = {
                "Right-click > Drop": 65,
                "Right-click > Use": 30,
                "Right-click > Wield / Wear": 45,
                "Right-click > Bury": 60,
            }
            offset = offsets.get(act, 40)
            self.mouse.click(cx, cy + offset)
            time.sleep(random.uniform(0.1, 0.3))

        elif act == "Use on NPC":
            # Click item, then user must have NPC nearby
            self.mouse.click(cx, cy)
            time.sleep(random.uniform(0.5, 0.8))

        elif act == "Use on object":
            self.mouse.click(cx, cy)
            time.sleep(random.uniform(0.5, 0.8))

    def reset(self):
        self._cooldowns.clear()
