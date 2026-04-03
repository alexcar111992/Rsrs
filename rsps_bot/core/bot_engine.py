"""Bot engine - runs a single mode (combat, skilling, or easter) in its own thread.

Each activity tab in the GUI creates its own engine instance.
Engines share nothing - each has its own capture, mouse, detector, etc.
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
from .skilling_system import SkillingSystem
from .easter_event import EasterEventSystem


class BotEngine:
    """One bot engine per activity tab. Runs a single mode."""

    def __init__(self):
        self.capture = ScreenCapture()
        self.mouse = MouseController()
        self.detector = InterfaceDetector()
        self.combat = CombatSystem(self.mouse, self.detector)
        self.loot = LootSystem(self.mouse, self.detector)
        self.inventory = InventoryManager(self.mouse, self.detector)
        self.login = LoginSystem(self.mouse, self.detector)
        self.antiban = AntibanSystem(self.mouse)
        self.skilling = SkillingSystem(self.mouse, self.detector)
        self.easter = EasterEventSystem(self.mouse, self.detector)

        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._paused = False
        self._status = "Idle"
        self._window: Optional[WindowInfo] = None
        self._profile: Optional[BotProfile] = None
        self._run_mode: str = "combat"
        self._tick_delay = 0.3

        # Callbacks to push updates to the GUI
        self.on_status_update: Optional[Callable[[str], None]] = None
        self.on_stats_update: Optional[Callable] = None

    @property
    def is_running(self) -> bool:
        return self._running

    def apply_profile(self, profile: BotProfile):
        """Load a profile and configure all subsystems."""
        self._profile = profile

        # Mouse mode
        ghost = profile.mouse.mode == "Ghost Mouse"
        self.mouse.mode = "ghost" if ghost else "real"
        self.mouse.humanize = profile.mouse.humanize
        self.mouse.misclick_chance = profile.mouse.misclick_chance

        speed_map = {
            "Slow": (0.2, 0.5),
            "Normal": (0.1, 0.3),
            "Fast": (0.05, 0.15),
            "Instant": (0.0, 0.02),
        }
        s_min, s_max = speed_map.get(profile.mouse.speed, (0.1, 0.3))
        self.mouse.speed_min = s_min
        self.mouse.speed_max = s_max

        self.detector.update_calibration(profile.calibration)
        self.combat.configure(profile.npc_targets, profile.combat)
        self.loot.configure(
            profile.loot_rules,
            pickup_all=not bool(profile.loot_rules),
            delay_ms=profile.combat.loot_delay_ms,
        )
        self.inventory.configure(profile.inventory_actions)
        self.login.configure(profile.login)
        self.skilling.configure(profile.skilling)
        self.easter.configure(profile.easter_event)
        self.antiban.configure(profile.antiban)

        self._tick_delay = max(0.15, s_min + 0.1)

    def set_window(self, window: WindowInfo):
        self._window = window
        self.mouse.set_window(window.hwnd)

    def find_game_windows(self, title_pattern: str = "") -> list:
        return self.capture.find_windows(title_pattern)

    def start(self, mode: str):
        """Start the bot in a specific mode: 'combat', 'skilling', or 'easter'."""
        if self._running:
            self.stop()

        if not self._window:
            self._set_status("No game window selected!")
            return
        if not self._profile:
            self._set_status("No profile loaded!")
            return

        self._run_mode = mode
        self._running = True
        self._paused = False

        # Reset only the relevant subsystem
        if mode == "combat":
            self.combat.reset()
            self.loot.reset()
            self.inventory.reset()
        elif mode == "skilling":
            self.skilling.reset()
        elif mode == "easter":
            self.easter.reset()

        self.login.reset()
        self.antiban.reset()

        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._set_status(f"{mode.title()} started")

    def stop(self):
        self._running = False
        self._paused = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        self._set_status(f"{self._run_mode.title()} stopped")

    def pause(self):
        self._paused = not self._paused
        self._set_status("Paused" if self._paused else "Resumed")

    def _run_loop(self):
        """Main loop - only runs the active mode."""
        mode = self._run_mode
        self._set_status(f"Running {mode}...")

        while self._running:
            try:
                if self._paused:
                    time.sleep(0.5)
                    continue

                # Capture
                image = self._capture_screen()
                if image is None:
                    self._set_status("Can't capture window - is the game open?")
                    time.sleep(2.0)
                    continue

                # Scan
                snap = self.detector.scan(image)

                # Auto-login if needed
                if self.login.needs_login(snap):
                    msg = self.login.tick(image, snap)
                    self._set_status(f"[Login] {msg}")
                    time.sleep(1.0)
                    continue

                if snap.game_state == GameState.IN_GAME:
                    self.login.on_login_success()

                # Anti-ban
                ab_msg = self.antiban.tick(snap)
                if ab_msg:
                    self._set_status(f"[Anti-ban] {ab_msg}")
                    if self.antiban.is_afk:
                        time.sleep(1.0)
                        continue

                # Run the active mode
                if mode == "easter":
                    msg = self.easter.tick(image, snap)
                    if msg:
                        self._set_status(f"[Easter] {msg}")

                elif mode == "skilling":
                    msg = self.skilling.tick(image, snap)
                    if msg:
                        self._set_status(f"[Skilling] {msg}")

                elif mode == "combat":
                    # Inventory management
                    if self._profile and not self._profile.combat.simple_mode:
                        inv_msg = self.inventory.tick(image, snap)
                        if inv_msg:
                            self._set_status(f"[Inventory] {inv_msg}")
                            time.sleep(self._tick_delay)
                            continue

                    # Loot
                    if (self._profile and self._profile.combat.loot_after_kill
                            and self.loot.has_items_to_loot(snap)):
                        msg = self.loot.pickup(image, snap)
                        self._set_status(f"[Loot] {msg}")
                        time.sleep(self._tick_delay)
                        continue

                    # Combat
                    msg = self.combat.tick(image, snap)
                    self._set_status(f"[Combat] {msg}")

                    if self.on_stats_update:
                        self.on_stats_update(self.combat.stats)

                time.sleep(self._tick_delay)

            except Exception as e:
                self._set_status(f"Error: {e}")
                traceback.print_exc()
                time.sleep(2.0)

        self._set_status(f"{mode.title()} stopped")

    def _capture_screen(self) -> Optional[np.ndarray]:
        if not self._window:
            return None
        if self.mouse.mode == "ghost":
            return self.capture.capture_window(self._window)
        else:
            return self.capture.capture_full_window_region(self._window)

    def _set_status(self, msg: str):
        self._status = msg
        if self.on_status_update:
            try:
                self.on_status_update(msg)
            except Exception:
                pass
