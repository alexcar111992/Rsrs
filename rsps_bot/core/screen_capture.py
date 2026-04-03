"""Screen capture engine - captures game client window contents.

Supports both foreground capture (full screen) and per-window capture
for ghost mouse mode where multiple clients run simultaneously.
"""

import ctypes
import ctypes.wintypes
import time
from typing import Optional, Tuple, List

import numpy as np

try:
    import mss
    HAS_MSS = True
except ImportError:
    HAS_MSS = False

try:
    import win32gui
    import win32ui
    import win32con
    import win32api
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

from PIL import Image


class WindowInfo:
    """Information about a game client window."""

    def __init__(self, hwnd: int, title: str, rect: Tuple[int, int, int, int]):
        self.hwnd = hwnd
        self.title = title
        self.left, self.top, self.right, self.bottom = rect
        self.width = self.right - self.left
        self.height = self.bottom - self.top

    def __repr__(self):
        return f"WindowInfo(hwnd={self.hwnd}, title='{self.title}', size={self.width}x{self.height})"


class ScreenCapture:
    """Captures screenshots from game windows."""

    def __init__(self):
        self._mss = None
        if HAS_MSS:
            self._mss = mss.mss()

    def find_windows(self, title_pattern: str = "") -> List[WindowInfo]:
        """Find all windows matching a title pattern."""
        if not HAS_WIN32:
            return []

        windows = []
        pattern_lower = title_pattern.lower()

        def enum_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and (not pattern_lower or pattern_lower in title.lower()):
                    try:
                        rect = win32gui.GetWindowRect(hwnd)
                        if rect[2] - rect[0] > 100 and rect[3] - rect[1] > 100:
                            windows.append(WindowInfo(hwnd, title, rect))
                    except Exception:
                        pass
            return True

        win32gui.EnumWindows(enum_callback, None)
        return windows

    def capture_window(self, window: WindowInfo) -> Optional[np.ndarray]:
        """Capture a specific window's contents using Win32 API.

        This works even if the window is behind other windows (ghost mode).
        """
        if not HAS_WIN32:
            return None

        hwnd = window.hwnd
        try:
            # Get the window's device context
            hwnd_dc = win32gui.GetWindowDC(hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()

            # Get window dimensions
            rect = win32gui.GetClientRect(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]

            if width <= 0 or height <= 0:
                return None

            # Create bitmap
            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(save_bitmap)

            # Use PrintWindow for background capture
            ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 3)

            # Convert to numpy array
            bmp_info = save_bitmap.GetInfo()
            bmp_str = save_bitmap.GetBitmapBits(True)
            img = np.frombuffer(bmp_str, dtype=np.uint8)
            img = img.reshape((bmp_info["bmHeight"], bmp_info["bmWidth"], 4))

            # Clean up
            win32gui.DeleteObject(save_bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwnd_dc)

            # Convert BGRA to RGB
            return img[:, :, :3][:, :, ::-1].copy()

        except Exception as e:
            print(f"[ScreenCapture] Error capturing window: {e}")
            return None

    def capture_region(self, x: int, y: int, width: int, height: int) -> Optional[np.ndarray]:
        """Capture a region of the screen (foreground mode)."""
        if self._mss is None:
            return None

        try:
            monitor = {"left": x, "top": y, "width": width, "height": height}
            screenshot = self._mss.grab(monitor)
            img = np.array(screenshot)
            # Convert BGRA to RGB
            return img[:, :, :3][:, :, ::-1].copy()
        except Exception as e:
            print(f"[ScreenCapture] Error capturing region: {e}")
            return None

    def capture_full_window_region(self, window: WindowInfo) -> Optional[np.ndarray]:
        """Capture window region from full screen (real mouse mode)."""
        return self.capture_region(
            window.left, window.top, window.width, window.height
        )

    def get_pixel_color(self, image: np.ndarray, x: int, y: int) -> Tuple[int, int, int]:
        """Get RGB color of a pixel in a captured image."""
        if image is None or x < 0 or y < 0:
            return (0, 0, 0)
        if y >= image.shape[0] or x >= image.shape[1]:
            return (0, 0, 0)
        return tuple(image[y, x, :3])

    def cleanup(self):
        """Clean up resources."""
        if self._mss:
            self._mss.close()
