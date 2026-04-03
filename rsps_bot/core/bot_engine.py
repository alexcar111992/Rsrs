"""Main bot engine - the brain that ties everything together.

Runs the main loop:
  1. Capture game window screenshot
  2. Detect game state (login screen, in-game, disconnected, etc.)
  3. If not in-game → auto-login
  4. If in-game → run combat, inventory, loot, anti-ban
  5. Report status to GUI

Everything is driven by the BotProfile the user configured in the GUI.
Zero AI, zero scripting needed.
"""

import threading
import time
import traceback
from typing import Callable, Optional

import numpy as np

from .config import BotProfile
from .screen_capture import ScreenCapture, WindowInfo
from .mouse_controller import MouseController
from .interface_detector import GameState, InterfaceDetector, InterfaceSnapshot
from .combat_system import CombatSystem, CombatStats
from .loot_system import LootSystem
from .inventory_manager import InventoryManager
from .login_system import LoginSystem
from .antiban import AntibanSystem


class BotEngine:
    """The main bot engine. Runs in a background thread."""

    def __init__(self):
        self.capture = ScreenCapture()
        self.mouse = MouseController()
        self.detector = InterfaceDetector()
        self.combat = CombatSystem(self.mouse, self.detector)
        self.loot = LootSystem(self.mouse, self.detector)
        self.inventory = InventoryManager(self.mouse, self.detector)
        self.login = LoginSystem(self.mouse, self.detector)
        self.antiban = AntibanSystem(self.mouse)

        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._paused = False
        self._status = "Idle"
        self._window: Optional[WindowInfo] = None
        self._profile: Optional[BotProfile] = None
        self._tick_delay = 0.3  # seconds between ticks
        self._last_snapshot: Optional[InterfaceSnapshot] = None

        # Callback to push status updates to the GUI
        self.on_status_update: Optional[Callable[[str], None]] = None
        self.on_stats_update: Optional[Callable[[CombatStats], None]] = None
        self.on_snapshot_update: Optional[Callable[[InterfaceSnapshot], None]] = None

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def status(self) -> str:
        return self._status

    @property
    def last_snapshot(self) -> Optional[InterfaceSnapshot]:
        return self._last_snapshot

    def apply_profile(self, profile: BotProfile):
        """Load a profile and configure all subsystems."""
        self._profile = profile

        # Mouse mode
        ghost = profile.mouse.mode == "Ghost Mouse"
        self.mouse.mode = "ghost" if ghost else "real"
        self.mouse.humanize = profile.mouse.humanize
        self.mouse.misclick_chance = profile.mouse.misclick_chance

        # Speed presets
        speed_map = {
            "Slow": (0.2, 0.5),
            "Normal": (0.1, 0.3),
            "Fast": (0.05, 0.15),
            "Instant": (0.0, 0.02),
        }
        s_min, s_max = speed_map.get(profile.mouse.speed, (0.1, 0.3))
        self.mouse.speed_min = s_min
        self.mouse.speed_max = s_max

        # Interface layout
        self.detector.update_calibration(profile.calibration)

        # Combat
        self.combat.configure(profile.npc_targets, profile.combat)

        # Loot
        self.loot.configure(
            profile.loot_rules,
            pickup_all=not bool(profile.loot_rules),
            delay_ms=profile.combat.loot_delay_ms,
        )

        # Inventory actions
        self.inventory.configure(profile.inventory_actions)

        # Login
        self.login.configure(profile.login)

        # Anti-ban
        self.antiban.configure(profile.antiban)

        # Tick speed based on mouse speed
        self._tick_delay = max(0.15, s_min + 0.1)

    def set_window(self, window: WindowInfo):
        """Set the game client window."""
        self._window = window
        self.mouse.set_window(window.hwnd)

    def find_game_windows(self, title_pattern: str = "") -> list:
        """Find game client windows."""
        return self.capture.find_windows(title_pattern)

    def start(self):
        """Start the bot in a background thread."""
        if self._running:
            return
        if not self._window:
            self._set_status("No game window selected!")
            return
        if not self._profile:
            self._set_status("No profile loaded!")
            return

        self._running = True
        self._paused = False
        self.combat.reset()
        self.loot.reset()
        self.inventory.reset()
        self.login.reset()
        self.antiban.reset()

        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._set_status("Bot started")

    def stop(self):
        """Stop the bot."""
        self._running = False
        self._paused = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        self._set_status("Bot stopped")

    def pause(self):
        """Toggle pause."""
        self._paused = not self._paused
        self._set_status("Paused" if self._paused else "Resumed")

    def _run_loop(self):
        """Main bot loop - runs in background thread."""
        self._set_status("Running...")

        while self._running:
            try:
                if self._paused:
                    time.sleep(0.5)
                    continue

                # Anti-ban AFK check
                if self.antiban.is_afk:
                    msg = self.antiban.tick(InterfaceSnapshot())
                    if msg:
                        self._set_status(f"[Anti-ban] {msg}")
                    time.sleep(1.0)
                    continue

                # 1. Capture screenshot
                image = self._capture_screen()
                if image is None:
                    self._set_status("Can't capture window - is the game open?")
                    time.sleep(2.0)
                    continue

                # 2. Scan interface
                snap = self.detector.scan(image)
                self._last_snapshot = snap
                if self.on_snapshot_update:
                    self.on_snapshot_update(snap)

                # 3. Handle login if needed
                if self.login.needs_login(snap):
                    msg = self.login.tick(image, snap)
                    self._set_status(f"[Login] {msg}")
                    time.sleep(1.0)
                    continue

                # If we just logged in, notify login system
                if snap.game_state == GameState.IN_GAME:
                    self.login.on_login_success()

                # 4. Anti-ban (may cause a pause)
                ab_msg = self.antiban.tick(snap)
                if ab_msg:
                    self._set_status(f"[Anti-ban] {ab_msg}")
                    if self.antiban.is_afk:
                        continue

                # 5. Inventory management (eat, drink, etc.)
                # Skip if Simple Mode is on (user doesn't need food/inventory)
                if not self._profile.combat.simple_mode:
                    inv_msg = self.inventory.tick(image, snap)
                    if inv_msg:
                        self._set_status(f"[Inventory] {inv_msg}")
                        time.sleep(self._tick_delay)
                        continue

                # 6. Loot pickup (if items on ground and configured)
                if self.loot.has_items_to_loot(snap) and self._profile.combat.loot_after_kill:
                    msg = self.loot.pickup(image, snap)
                    self._set_status(f"[Loot] {msg}")
                    time.sleep(self._tick_delay)
                    continue

                # 7. Combat
                msg = self.combat.tick(image, snap)
                self._set_status(f"[Combat] {msg}")

                # Push stats
                if self.on_stats_update:
                    self.on_stats_update(self.combat.stats)

                time.sleep(self._tick_delay)

            except Exception as e:
                self._set_status(f"Error: {e}")
                traceback.print_exc()
                time.sleep(2.0)

        self._set_status("Bot stopped")

    def _capture_screen(self) -> Optional[np.ndarray]:
        """Capture the game window screenshot."""
        if not self._window:
            return None

        if self.mouse.mode == "ghost":
            # Ghost mode: capture using PrintWindow (works in background)
            return self.capture.capture_window(self._window)
        else:
            # Real mode: capture screen region
            return self.capture.capture_full_window_region(self._window)

    def _set_status(self, msg: str):
        """Update status and notify GUI."""
        self._status = msg
        if self.on_status_update:
            try:
                self.on_status_update(msg)
            except Exception:
                pass
