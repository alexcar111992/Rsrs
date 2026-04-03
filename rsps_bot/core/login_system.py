"""Auto-login system - logs back in when disconnected.

User configures (in GUI):
  - Username (text field)
  - Password (password field)
  - World number (spinner)
  - Retry delay (spinner)
  - Max retries (spinner)
  - Enabled (checkbox)

Uses known login screen positions (from calibration data) to
click fields and type credentials. No AI needed.
"""

import random
import time
from typing import Optional

import numpy as np

try:
    import win32con
    import win32api
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

from .config import LoginSettings
from .interface_detector import GameState, InterfaceDetector, InterfaceSnapshot
from .mouse_controller import MouseController


class LoginSystem:
    """Handles auto-login and disconnect recovery."""

    def __init__(self, mouse: MouseController, detector: InterfaceDetector):
        self.mouse = mouse
        self.detector = detector
        self.settings = LoginSettings()

        self._attempts = 0
        self._last_attempt = 0.0
        self._stage = 0  # 0=click existing, 1=username, 2=password, 3=login

    def configure(self, settings: LoginSettings):
        """Apply settings from GUI."""
        self.settings = settings
        self._attempts = 0
        self._stage = 0

    def needs_login(self, snap: InterfaceSnapshot) -> bool:
        """Check if we need to log in."""
        if not self.settings.enabled:
            return False
        return snap.game_state in (GameState.LOGIN_SCREEN, GameState.DISCONNECTED, GameState.LOBBY)

    def tick(self, image: np.ndarray, snap: InterfaceSnapshot) -> str:
        """Attempt one step of the login process. Returns status."""
        if not self.settings.enabled:
            return "Auto-login disabled"

        if self._attempts >= self.settings.max_retries:
            return f"Max retries ({self.settings.max_retries}) reached"

        # Respect retry delay
        elapsed = time.time() - self._last_attempt
        if elapsed < self.settings.retry_delay_seconds and self._stage == 0:
            return f"Waiting {self.settings.retry_delay_seconds - elapsed:.0f}s to retry"

        w, h = snap.client_width, snap.client_height
        positions = self.detector.get_login_field_positions(w, h)

        # Handle disconnect overlay first
        if snap.game_state == GameState.DISCONNECTED:
            self.mouse.click(w // 2, h // 2)
            time.sleep(random.uniform(1.0, 2.0))
            self._last_attempt = time.time()
            return "Dismissing disconnect message"

        # Handle lobby
        if snap.game_state == GameState.LOBBY:
            self.mouse.click(*positions["lobby_play_button"])
            time.sleep(random.uniform(1.0, 2.0))
            self._last_attempt = time.time()
            return "Clicking Play in lobby"

        # Handle login screen (multi-step)
        if snap.game_state == GameState.LOGIN_SCREEN:
            return self._do_login_step(positions)

        return "Waiting..."

    def _do_login_step(self, positions: dict) -> str:
        """Execute one step of the login sequence."""
        if not self.settings.username or not self.settings.password:
            return "No credentials configured"

        if self._stage == 0:
            # Click "Existing User" / "Login" area
            self.mouse.click(*positions["existing_user_button"])
            time.sleep(random.uniform(0.6, 1.0))
            self._stage = 1
            return "Clicked login area"

        elif self._stage == 1:
            # Click username field and type
            self.mouse.click(*positions["username_field"])
            time.sleep(random.uniform(0.3, 0.5))
            self._clear_field()
            self.mouse.type_text(self.settings.username, delay_per_char=0.04)
            time.sleep(random.uniform(0.3, 0.5))
            self._stage = 2
            return "Entered username"

        elif self._stage == 2:
            # Click password field and type
            self.mouse.click(*positions["password_field"])
            time.sleep(random.uniform(0.3, 0.5))
            self._clear_field()
            self.mouse.type_text(self.settings.password, delay_per_char=0.04)
            time.sleep(random.uniform(0.3, 0.5))
            self._stage = 3
            return "Entered password"

        elif self._stage == 3:
            # Click login button or press Enter
            self.mouse.click(*positions["login_button"])
            self._last_attempt = time.time()
            self._attempts += 1
            self._stage = 0
            return f"Logging in (attempt {self._attempts}/{self.settings.max_retries})"

        return "Login in progress"

    def _clear_field(self):
        """Select all text in current field and delete it."""
        if not HAS_WIN32:
            return
        # Ctrl+A then Delete
        win32api.keybd_event(0x11, 0, 0, 0)         # Ctrl down
        time.sleep(0.03)
        win32api.keybd_event(0x41, 0, 0, 0)         # A down
        time.sleep(0.03)
        win32api.keybd_event(0x41, 0, 2, 0)         # A up
        win32api.keybd_event(0x11, 0, 2, 0)         # Ctrl up
        time.sleep(0.05)
        win32api.keybd_event(0x2E, 0, 0, 0)         # Delete down
        time.sleep(0.03)
        win32api.keybd_event(0x2E, 0, 2, 0)         # Delete up
        time.sleep(0.05)

    def on_login_success(self):
        """Call when login succeeds (game state becomes IN_GAME)."""
        self._stage = 0
        self._attempts = 0

    def reset(self):
        self._attempts = 0
        self._stage = 0
        self._last_attempt = 0.0
