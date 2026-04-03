"""Anti-ban / human-like behavior system.

Makes the bot look more human by:
  - Random camera rotations
  - Occasional mouse drifts
  - Random short pauses
  - Occasional AFK breaks
  - Varied click timing

All controlled via checkboxes and sliders in the GUI.
"""

import random
import time

from .config import AntibanSettings
from .mouse_controller import MouseController
from .interface_detector import InterfaceSnapshot


class AntibanSystem:
    """Adds human-like behavior to avoid detection."""

    def __init__(self, mouse: MouseController):
        self.mouse = mouse
        self.settings = AntibanSettings()

        self._last_camera_time = 0.0
        self._last_pause_time = 0.0
        self._last_afk_time = 0.0
        self._next_afk_time = 0.0
        self._is_afk = False
        self._afk_end_time = 0.0

    def configure(self, settings: AntibanSettings):
        """Apply settings from GUI."""
        self.settings = settings
        self._schedule_next_afk()

    def tick(self, snap: InterfaceSnapshot) -> str:
        """Run one cycle of anti-ban checks. Returns status if action taken."""
        if not self.settings.enabled:
            return ""

        now = time.time()

        # Handle AFK break
        if self._is_afk:
            if now >= self._afk_end_time:
                self._is_afk = False
                self._schedule_next_afk()
                return "AFK break ended"
            return f"AFK break ({self._afk_end_time - now:.0f}s left)"

        # Check if it's time for an AFK break
        if self.settings.random_afk and now >= self._next_afk_time and self._next_afk_time > 0:
            duration = random.randint(self.settings.afk_min_seconds, self.settings.afk_max_seconds)
            self._is_afk = True
            self._afk_end_time = now + duration
            self._last_afk_time = now
            return f"Starting AFK break ({duration}s)"

        # Random camera rotation
        if self.settings.random_camera and now - self._last_camera_time > random.uniform(30, 120):
            self._rotate_camera(snap)
            self._last_camera_time = now
            return "Random camera move"

        # Random mouse drift
        if self.settings.random_mouse_drift and random.random() < 0.01:
            self._mouse_drift(snap)
            return "Mouse drift"

        # Random short pause
        if self.settings.random_pauses and now - self._last_pause_time > random.uniform(20, 90):
            pause = random.uniform(
                self.settings.pause_min_seconds,
                self.settings.pause_max_seconds
            )
            time.sleep(pause)
            self._last_pause_time = now
            return f"Short pause ({pause:.1f}s)"

        return ""

    @property
    def is_afk(self) -> bool:
        return self._is_afk

    def _rotate_camera(self, snap: InterfaceSnapshot):
        """Rotate the camera randomly using arrow keys or middle-mouse."""
        # Use arrow keys to rotate camera
        try:
            import win32api
            import win32con

            key = random.choice([win32con.VK_LEFT, win32con.VK_RIGHT])
            duration = random.uniform(0.1, 0.5)

            win32api.keybd_event(key, 0, 0, 0)
            time.sleep(duration)
            win32api.keybd_event(key, 0, 2, 0)
        except ImportError:
            pass

    def _mouse_drift(self, snap: InterfaceSnapshot):
        """Move the mouse slightly in a random direction."""
        drift_x = random.randint(-50, 50)
        drift_y = random.randint(-30, 30)
        # Move relative to current position
        self.mouse.move_to(
            snap.viewport_center[0] + drift_x,
            snap.viewport_center[1] + drift_y,
            smooth=True,
        )

    def _schedule_next_afk(self):
        """Schedule the next AFK break."""
        if self.settings.random_afk:
            chance = self.settings.afk_chance_percent / 100.0
            # On average, AFK every N minutes based on chance
            interval = random.uniform(120, 600) / max(chance, 0.01)
            self._next_afk_time = time.time() + min(interval, 1800)
        else:
            self._next_afk_time = 0

    def reset(self):
        self._is_afk = False
        self._last_camera_time = 0.0
        self._last_pause_time = 0.0
        self._schedule_next_afk()
