"""Mouse controller with Real Mouse and Ghost Mouse modes.

Real Mouse Mode: Moves the actual system cursor (one client at a time).
Ghost Mouse Mode: Sends input messages directly to a window handle,
    allowing multiple clients to be botted simultaneously while the
    user retains control of their physical mouse.
"""

import ctypes
import math
import random
import time
from typing import Optional, Tuple

import numpy as np

try:
    import win32gui
    import win32con
    import win32api
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False


# Windows message constants
WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_CHAR = 0x0102

MK_LBUTTON = 0x0001
MK_RBUTTON = 0x0002


def _make_lparam(x: int, y: int) -> int:
    """Pack x,y coordinates into an LPARAM."""
    return (y << 16) | (x & 0xFFFF)


def _bezier_curve(start: Tuple[int, int], end: Tuple[int, int], steps: int = 20) -> list:
    """Generate a human-like bezier curve path between two points."""
    sx, sy = start
    ex, ey = end

    # Random control points for natural movement
    dist = math.sqrt((ex - sx) ** 2 + (ey - sy) ** 2)
    spread = max(dist * 0.3, 10)

    cx1 = sx + random.uniform(-spread, spread)
    cy1 = sy + random.uniform(-spread, spread)
    cx2 = ex + random.uniform(-spread, spread)
    cy2 = ey + random.uniform(-spread, spread)

    points = []
    for i in range(steps + 1):
        t = i / steps
        t2 = t * t
        t3 = t2 * t
        mt = 1 - t
        mt2 = mt * mt
        mt3 = mt2 * mt

        x = mt3 * sx + 3 * mt2 * t * cx1 + 3 * mt * t2 * cx2 + t3 * ex
        y = mt3 * sy + 3 * mt2 * t * cy1 + 3 * mt * t2 * cy2 + t3 * ey

        points.append((int(x), int(y)))

    return points


class MouseController:
    """Controls mouse input in both real and ghost modes."""

    def __init__(self, mode: str = "real", hwnd: Optional[int] = None):
        """
        Args:
            mode: "real" for physical mouse, "ghost" for virtual/background input
            hwnd: Window handle for ghost mode
        """
        self.mode = mode
        self.hwnd = hwnd
        self.speed_min = 0.1
        self.speed_max = 0.3
        self.click_delay_min = 50
        self.click_delay_max = 150
        self.humanize = True
        self.misclick_chance = 0.02
        self._last_x = 0
        self._last_y = 0

    def set_window(self, hwnd: int):
        """Set the target window handle for ghost mode."""
        self.hwnd = hwnd

    def move_to(self, x: int, y: int, smooth: bool = True):
        """Move the mouse to a position.

        In real mode, moves the physical cursor.
        In ghost mode, sends WM_MOUSEMOVE to the window.
        """
        # Add small random offset for human-like behavior
        if self.humanize:
            x += random.randint(-2, 2)
            y += random.randint(-2, 2)

        if self.mode == "real":
            self._real_move(x, y, smooth)
        else:
            self._ghost_move(x, y, smooth)

        self._last_x = x
        self._last_y = y

    def click(self, x: Optional[int] = None, y: Optional[int] = None, button: str = "left"):
        """Click at position. If x,y are None, clicks at current position."""
        if x is not None and y is not None:
            self.move_to(x, y)

        # Random delay before click
        delay = random.randint(self.click_delay_min, self.click_delay_max) / 1000.0
        time.sleep(delay)

        if self.mode == "real":
            self._real_click(button)
        else:
            self._ghost_click(self._last_x, self._last_y, button)

    def right_click(self, x: Optional[int] = None, y: Optional[int] = None):
        """Right-click at position."""
        self.click(x, y, button="right")

    def type_text(self, text: str, delay_per_char: float = 0.05):
        """Type text character by character."""
        for char in text:
            if self.mode == "real":
                self._real_type_char(char)
            else:
                self._ghost_type_char(char)
            time.sleep(delay_per_char + random.uniform(0, 0.03))

    def press_key(self, key_code: int):
        """Press and release a key."""
        if self.mode == "real":
            self._real_press_key(key_code)
        else:
            self._ghost_press_key(key_code)

    def press_enter(self):
        """Press the Enter key."""
        self.press_key(win32con.VK_RETURN if HAS_WIN32 else 0x0D)

    def press_tab(self):
        """Press the Tab key."""
        self.press_key(win32con.VK_TAB if HAS_WIN32 else 0x09)

    def press_escape(self):
        """Press the Escape key."""
        self.press_key(win32con.VK_ESCAPE if HAS_WIN32 else 0x1B)

    # --- Real Mouse Methods ---

    def _real_move(self, x: int, y: int, smooth: bool = True):
        """Move physical cursor."""
        if not HAS_PYAUTOGUI:
            return

        if smooth and self.humanize:
            # Use bezier curve for human-like movement
            current = pyautogui.position()
            points = _bezier_curve((current.x, current.y), (x, y))
            duration = random.uniform(self.speed_min, self.speed_max)
            step_delay = duration / max(len(points), 1)

            for px, py in points:
                pyautogui.moveTo(px, py, _pause=False)
                time.sleep(step_delay)
        else:
            pyautogui.moveTo(x, y, _pause=False)

    def _real_click(self, button: str = "left"):
        """Click physical mouse."""
        if not HAS_PYAUTOGUI:
            return
        if button == "left":
            pyautogui.click(_pause=False)
        else:
            pyautogui.rightClick(_pause=False)

    def _real_type_char(self, char: str):
        """Type a character using physical keyboard."""
        if HAS_PYAUTOGUI:
            pyautogui.press(char, _pause=False)

    def _real_press_key(self, key_code: int):
        """Press a key using physical keyboard."""
        if not HAS_WIN32:
            return
        scan_code = win32api.MapVirtualKey(key_code, 0)
        win32api.keybd_event(key_code, scan_code, 0, 0)
        time.sleep(0.05)
        win32api.keybd_event(key_code, scan_code, win32con.KEYEVENTF_KEYUP, 0)

    # --- Ghost Mouse Methods ---

    def _ghost_move(self, x: int, y: int, smooth: bool = True):
        """Move ghost cursor by sending messages to window."""
        if not HAS_WIN32 or not self.hwnd:
            return

        if smooth and self.humanize:
            points = _bezier_curve((self._last_x, self._last_y), (x, y), steps=10)
            duration = random.uniform(self.speed_min, self.speed_max)
            step_delay = duration / max(len(points), 1)

            for px, py in points:
                lparam = _make_lparam(px, py)
                win32gui.PostMessage(self.hwnd, WM_MOUSEMOVE, 0, lparam)
                time.sleep(step_delay)
        else:
            lparam = _make_lparam(x, y)
            win32gui.PostMessage(self.hwnd, WM_MOUSEMOVE, 0, lparam)

    def _ghost_click(self, x: int, y: int, button: str = "left"):
        """Click by sending messages to window."""
        if not HAS_WIN32 or not self.hwnd:
            return

        lparam = _make_lparam(x, y)

        if button == "left":
            win32gui.PostMessage(self.hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam)
            time.sleep(random.uniform(0.04, 0.10))
            win32gui.PostMessage(self.hwnd, WM_LBUTTONUP, 0, lparam)
        else:
            win32gui.PostMessage(self.hwnd, WM_RBUTTONDOWN, MK_RBUTTON, lparam)
            time.sleep(random.uniform(0.04, 0.10))
            win32gui.PostMessage(self.hwnd, WM_RBUTTONUP, 0, lparam)

    def _ghost_type_char(self, char: str):
        """Type a character by sending messages to window."""
        if not HAS_WIN32 or not self.hwnd:
            return
        win32gui.PostMessage(self.hwnd, WM_CHAR, ord(char), 0)

    def _ghost_press_key(self, key_code: int):
        """Press a key by sending messages to window."""
        if not HAS_WIN32 or not self.hwnd:
            return
        scan_code = win32api.MapVirtualKey(key_code, 0) if HAS_WIN32 else 0
        lparam_down = (scan_code << 16) | 1
        lparam_up = (scan_code << 16) | 1 | (1 << 30) | (1 << 31)
        win32gui.PostMessage(self.hwnd, WM_KEYDOWN, key_code, lparam_down)
        time.sleep(0.05)
        win32gui.PostMessage(self.hwnd, WM_KEYUP, key_code, lparam_up)
