"""Skilling system - handles stationary skilling activities.

For skills where you stand in one place and repeatedly click:
  Mining, Woodcutting, Fishing, Thieving (stalls), Cooking,
  Smithing, Crafting, Fletching, Firemaking, Runecrafting, etc.

The user tells the bot:
  - What skill / object type (dropdown)
  - Object name (text field, e.g. "Iron rock")
  - Click action (left-click or right-click > option)
  - What to do when inventory is full (::empty, ::bank, drop, etc.)
  - Re-click timing

No AI - the user gives the bot all the info it needs.
"""

import random
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Tuple

import numpy as np

from .config import SkillingSettings
from .interface_detector import GameState, InterfaceDetector, InterfaceSnapshot
from .mouse_controller import MouseController


class SkillingState(Enum):
    IDLE = auto()
    CLICKING_OBJECT = auto()
    WAITING_FOR_ACTION = auto()          # Waiting for mining/fishing/chopping animation
    HANDLING_FULL_INVENTORY = auto()
    USING_ITEM_ON_OBJECT = auto()


@dataclass
class SkillingStats:
    """Live skilling stats for the GUI."""
    actions_done: int = 0
    inventories_filled: int = 0
    items_dropped: int = 0
    commands_typed: int = 0
    start_time: float = 0.0

    @property
    def runtime_minutes(self) -> float:
        if self.start_time <= 0:
            return 0.0
        return (time.time() - self.start_time) / 60.0

    @property
    def actions_per_hour(self) -> float:
        mins = self.runtime_minutes
        if mins <= 0:
            return 0.0
        return (self.actions_done / mins) * 60.0


class SkillingSystem:
    """Handles stationary skilling automation."""

    def __init__(self, mouse: MouseController, detector: InterfaceDetector):
        self.mouse = mouse
        self.detector = detector

        self.state = SkillingState.IDLE
        self.stats = SkillingStats()
        self.settings = SkillingSettings()

        # The spot the user first clicked (or viewport center)
        self._click_x: int = 0
        self._click_y: int = 0
        self._last_click_time: float = 0.0
        self._was_full: bool = False

    def configure(self, settings: SkillingSettings):
        """Apply settings from GUI."""
        self.settings = settings

    def tick(self, image: np.ndarray, snap: InterfaceSnapshot) -> str:
        """Run one cycle of the skilling loop. Returns status message."""
        if not self.settings.enabled:
            return ""

        if snap.game_state != GameState.IN_GAME:
            return f"Not in game ({snap.game_state.name})"

        # Set initial click position to viewport center if not set
        if self._click_x == 0 and self._click_y == 0:
            self._click_x, self._click_y = snap.viewport_center

        # Priority: handle full inventory
        if snap.inventory_full and not self._was_full:
            self._was_full = True
            self.stats.inventories_filled += 1
            self.state = SkillingState.HANDLING_FULL_INVENTORY

        if self.state == SkillingState.HANDLING_FULL_INVENTORY:
            return self._handle_full_inventory(snap)

        # Reset full flag when inventory has space again
        if not snap.inventory_full:
            self._was_full = False

        # Main skilling loop
        if self.state in (SkillingState.IDLE, SkillingState.CLICKING_OBJECT):
            return self._click_skill_object(snap)
        elif self.state == SkillingState.WAITING_FOR_ACTION:
            return self._wait_for_action(snap)
        elif self.state == SkillingState.USING_ITEM_ON_OBJECT:
            return self._use_item_on_object(snap)

        return f"Skilling: {self.state.name}"

    def _click_skill_object(self, snap: InterfaceSnapshot) -> str:
        """Click the skilling object (rock, tree, fishing spot, stall, etc.)."""
        now = time.time()

        # Respect re-click delay
        if now - self._last_click_time < self.settings.re_click_delay_ms / 1000.0:
            return "Waiting to re-click..."

        # If using item on object (e.g. knife on logs)
        if self.settings.use_item_on_object:
            self.state = SkillingState.USING_ITEM_ON_OBJECT
            return self._use_item_on_object(snap)

        x = self._click_x + random.randint(-5, 5)
        y = self._click_y + random.randint(-5, 5)

        if self.settings.object_action == "Left-click":
            self.mouse.click(x, y)
        else:
            # Right-click then select the option
            self.mouse.right_click(x, y)
            time.sleep(random.uniform(0.3, 0.6))
            # Click the option below (approximate menu offset)
            self.mouse.click(x, y + 20)

        self._last_click_time = now
        self.stats.actions_done += 1
        self.state = SkillingState.WAITING_FOR_ACTION

        return f"Clicking {self.settings.object_name or self.settings.skill_type} (#{self.stats.actions_done})"

    def _wait_for_action(self, snap: InterfaceSnapshot) -> str:
        """Wait for the skilling action to complete before re-clicking."""
        now = time.time()
        elapsed = now - self._last_click_time
        delay = self.settings.re_click_delay_ms / 1000.0

        if elapsed >= delay:
            self.state = SkillingState.CLICKING_OBJECT
            return "Ready to click again"

        return f"Skilling... ({delay - elapsed:.1f}s until re-click)"

    def _use_item_on_object(self, snap: InterfaceSnapshot) -> str:
        """Use an inventory item on the object (e.g. knife on logs)."""
        w, h = snap.client_width, snap.client_height
        slot_centers = self.detector.get_inventory_slot_centers(w, h)

        idx = self.settings.use_item_slot - 1
        if 0 <= idx < len(slot_centers):
            # Click the item in inventory
            cx, cy = slot_centers[idx]
            self.mouse.click(cx, cy)
            time.sleep(random.uniform(0.3, 0.5))

            # Click the object in viewport
            x = self._click_x + random.randint(-5, 5)
            y = self._click_y + random.randint(-5, 5)
            self.mouse.click(x, y)

            self._last_click_time = time.time()
            self.stats.actions_done += 1
            self.state = SkillingState.WAITING_FOR_ACTION
            return f"Using item on {self.settings.object_name or 'object'} (#{self.stats.actions_done})"

        return "Invalid item slot configured"

    def _handle_full_inventory(self, snap: InterfaceSnapshot) -> str:
        """Handle what to do when inventory is full."""
        action = self.settings.inventory_full_action

        if action == "Type ::empty (empties inventory)":
            return self._type_command("::empty")

        elif action == "Type ::bank (opens bank)":
            return self._type_command("::bank")

        elif action == "Drop all items":
            return self._drop_all_items(snap)

        elif action == "Drop specific items":
            return self._drop_specific_items(snap)

        elif action == "Bank at nearest banker":
            # Just type ::bank as fallback for most RSPS
            return self._type_command("::bank")

        elif action == "Stop skilling":
            self.settings.enabled = False
            return "Inventory full - stopped skilling"

        elif action == "Do nothing (wait)":
            return "Inventory full - waiting"

        # If custom command configured
        if self.settings.custom_command:
            return self._type_command(self.settings.custom_command)

        self.state = SkillingState.IDLE
        return "Inventory full - no action configured"

    def _type_command(self, command: str) -> str:
        """Type a ::command in the chatbox."""
        self.mouse.type_text(command, delay_per_char=0.03)
        time.sleep(0.1)
        self.mouse.press_enter()
        self.stats.commands_typed += 1
        time.sleep(random.uniform(0.5, 1.0))

        # Go back to skilling
        self.state = SkillingState.IDLE
        self._was_full = False
        return f"Typed {command}"

    def _drop_all_items(self, snap: InterfaceSnapshot) -> str:
        """Drop all items in inventory."""
        w, h = snap.client_width, snap.client_height
        slot_centers = self.detector.get_inventory_slot_centers(w, h)

        for cx, cy in slot_centers:
            # Right-click > Drop for each slot
            self.mouse.right_click(cx + random.randint(-2, 2), cy + random.randint(-2, 2))
            time.sleep(random.uniform(0.15, 0.3))
            self.mouse.click(cx, cy + 65)  # "Drop" option offset
            time.sleep(random.uniform(0.1, 0.2))
            self.stats.items_dropped += 1

        self.state = SkillingState.IDLE
        self._was_full = False
        return f"Dropped all items ({self.stats.items_dropped} total)"

    def _drop_specific_items(self, snap: InterfaceSnapshot) -> str:
        """Drop only items matching the configured names."""
        # Without AI/OCR we can't read item names, so drop all filled slots
        # The user should configure which slots to keep vs drop via inventory tab
        return self._drop_all_items(snap)

    def set_click_position(self, x: int, y: int):
        """Set where to click (called when user clicks on game viewport)."""
        self._click_x = x
        self._click_y = y

    def reset(self):
        """Reset for a fresh session."""
        self.state = SkillingState.IDLE
        self.stats = SkillingStats()
        self.stats.start_time = time.time()
        self._click_x = 0
        self._click_y = 0
        self._was_full = False
