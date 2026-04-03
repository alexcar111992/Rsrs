"""Universal RSPS interface detector.

Detects game state purely from built-in knowledge of how RuneScape
interfaces work plus user-provided calibration. NO AI involved.

How it works:
1. User selects a layout preset (317, 474, 667, etc.) or calibrates manually
2. The bot knows exactly where inventory, minimap, HP, chatbox, etc. are
3. Color-based detection identifies HP bars, NPC dots, ground items, login screen
4. The user tells the bot NPC names, HP values, etc. through the GUI
"""

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from .config import (
    LAYOUT_PRESETS, CalibrationData,
    HP_GREEN_RANGE, HP_RED_RANGE, NPC_HOVER_YELLOW,
    GROUND_TEXT_WHITE, GROUND_TEXT_CYAN, GROUND_TEXT_GREEN,
    MINIMAP_NPC_DOT, LOGIN_YELLOW,
)


class GameState(Enum):
    """What screen the game is currently on."""
    UNKNOWN = auto()
    LOGIN_SCREEN = auto()
    LOBBY = auto()
    IN_GAME = auto()
    DISCONNECTED = auto()
    DIALOGUE = auto()
    DEAD = auto()


@dataclass
class InterfaceSnapshot:
    """Everything the bot can see right now - no AI, pure pixel analysis."""
    game_state: GameState = GameState.UNKNOWN
    player_hp_percent: float = 100.0
    in_combat: bool = False
    target_hp_percent: float = 100.0
    inventory_empty_slots: int = 28
    inventory_full: bool = False
    npc_hp_bars: list = field(default_factory=list)       # List of (x, y, w, h, hp%)
    minimap_npc_dots: list = field(default_factory=list)   # List of (x, y)
    ground_items: list = field(default_factory=list)       # List of (x, y, w, h)
    client_width: int = 0
    client_height: int = 0
    viewport_center: Tuple[int, int] = (0, 0)
    timestamp: float = 0.0


class InterfaceDetector:
    """Reads the game screen using calibrated regions and color detection."""

    def __init__(self, calibration: Optional[CalibrationData] = None):
        self.calibration = calibration or CalibrationData()
        self._regions = self._load_regions()

    def _load_regions(self) -> Dict[str, Tuple[float, float, float, float]]:
        """Load the region ratios from calibration or preset."""
        layout_name = self.calibration.layout_name
        if layout_name in LAYOUT_PRESETS:
            return dict(LAYOUT_PRESETS[layout_name])
        return dict(self.calibration.regions)

    def update_calibration(self, calibration: CalibrationData):
        """Update calibration data (when user changes layout in GUI)."""
        self.calibration = calibration
        self._regions = self._load_regions()

    def region_px(self, name: str, w: int, h: int) -> Tuple[int, int, int, int]:
        """Convert a named region from ratios to pixel coordinates."""
        r = self._regions.get(name, (0, 0, 1, 1))
        return (int(w * r[0]), int(h * r[1]), int(w * r[2]), int(h * r[3]))

    def crop_region(self, image: np.ndarray, name: str) -> np.ndarray:
        """Crop a named region from the image."""
        h, w = image.shape[:2]
        x1, y1, x2, y2 = self.region_px(name, w, h)
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        return image[y1:y2, x1:x2]

    # ── Main scan ─────────────────────────────────────────────────────────

    def scan(self, image: np.ndarray) -> InterfaceSnapshot:
        """Full scan of the game screen. Returns everything the bot can see."""
        if image is None or image.size == 0:
            return InterfaceSnapshot()

        snap = InterfaceSnapshot()
        snap.timestamp = time.time()
        snap.client_height, snap.client_width = image.shape[:2]
        w, h = snap.client_width, snap.client_height

        # 1. What screen are we on?
        snap.game_state = self._detect_game_state(image, w, h)

        if snap.game_state != GameState.IN_GAME:
            return snap

        # 2. Player HP (from the HP orb area)
        snap.player_hp_percent = self._read_hp_orb(image, w, h)

        # 3. Combat state - look for HP bars in viewport
        viewport = self.crop_region(image, "viewport")
        vp_x1, vp_y1, _, _ = self.region_px("viewport", w, h)
        bars = self._find_hp_bars(viewport)
        snap.npc_hp_bars = [(b[0] + vp_x1, b[1] + vp_y1, b[2], b[3], b[4]) for b in bars]
        snap.in_combat = len(bars) > 0
        if bars:
            snap.target_hp_percent = bars[0][4]

        # 4. Inventory
        snap.inventory_empty_slots = self._count_empty_inv_slots(image, w, h)
        snap.inventory_full = (snap.inventory_empty_slots == 0)

        # 5. Minimap NPC dots
        minimap = self.crop_region(image, "minimap")
        mm_x1, mm_y1, _, _ = self.region_px("minimap", w, h)
        dots = self._find_color_blobs(minimap, MINIMAP_NPC_DOT, min_area=4, max_area=80)
        snap.minimap_npc_dots = [(d[0] + mm_x1, d[1] + mm_y1) for d in dots]

        # 6. Ground items in viewport
        ground = self._find_ground_item_text(viewport)
        snap.ground_items = [(g[0] + vp_x1, g[1] + vp_y1, g[2], g[3]) for g in ground]

        # 7. Viewport center
        vp = self._regions.get("viewport", (0, 0, 0.7, 0.75))
        snap.viewport_center = (int(w * (vp[0] + vp[2]) / 2), int(h * (vp[1] + vp[3]) / 2))

        return snap

    # ── Game state detection ──────────────────────────────────────────────

    def _detect_game_state(self, image: np.ndarray, w: int, h: int) -> GameState:
        """Determine what screen we're on using color analysis."""
        # Sample the center third of the screen
        cy1, cy2 = h // 3, 2 * h // 3
        cx1, cx2 = w // 4, 3 * w // 4
        center = image[cy1:cy2, cx1:cx2]

        if center.size == 0:
            return GameState.UNKNOWN

        gray = cv2.cvtColor(center, cv2.COLOR_RGB2GRAY)
        dark_pct = np.count_nonzero(gray < 35) / gray.size
        white_pct = np.count_nonzero(gray > 220) / gray.size

        # Login screen: mostly dark with some yellow text
        yellow_mask = cv2.inRange(
            center,
            np.array(LOGIN_YELLOW[0], dtype=np.uint8),
            np.array(LOGIN_YELLOW[1], dtype=np.uint8),
        )
        yellow_pct = np.count_nonzero(yellow_mask) / yellow_mask.size

        if dark_pct > 0.65 and yellow_pct > 0.003:
            return GameState.LOGIN_SCREEN

        # Disconnected: very dark center with small white text
        if dark_pct > 0.75 and 0.005 < white_pct < 0.12:
            return GameState.DISCONNECTED

        # Death screen: red tint
        r_mean = float(np.mean(center[:, :, 0]))
        g_mean = float(np.mean(center[:, :, 1]))
        b_mean = float(np.mean(center[:, :, 2]))
        if r_mean > g_mean + 25 and r_mean > b_mean + 25 and r_mean > 80:
            return GameState.DEAD

        # Dialogue box: tan/beige colored rectangle in center
        tan_mask = cv2.inRange(center, np.array([150, 130, 90]), np.array([225, 205, 165]))
        if np.count_nonzero(tan_mask) / tan_mask.size > 0.25:
            return GameState.DIALOGUE

        # In-game: check if right sidebar (inventory panel area) has typical stone texture
        panel_x = int(w * 0.73)
        if panel_x < w:
            panel = image[0:h, panel_x:w]
            pg = cv2.cvtColor(panel, cv2.COLOR_RGB2GRAY)
            mid_tone = np.count_nonzero((pg > 35) & (pg < 180)) / pg.size
            if mid_tone > 0.25:
                return GameState.IN_GAME

        return GameState.UNKNOWN

    # ── HP reading ────────────────────────────────────────────────────────

    def _read_hp_orb(self, image: np.ndarray, w: int, h: int) -> float:
        """Read player HP from the HP orb region."""
        orb = self.crop_region(image, "hp_orb")
        if orb.size == 0:
            return 100.0

        green = cv2.inRange(orb, np.array(HP_GREEN_RANGE[0]), np.array(HP_GREEN_RANGE[1]))
        red = cv2.inRange(orb, np.array(HP_RED_RANGE[0]), np.array(HP_RED_RANGE[1]))

        g_count = int(np.count_nonzero(green))
        r_count = int(np.count_nonzero(red))
        total = g_count + r_count

        if total < 5:
            return 100.0  # Can't see orb clearly, assume full
        return (g_count / total) * 100.0

    # ── HP bar detection ──────────────────────────────────────────────────

    def _find_hp_bars(self, viewport: np.ndarray) -> List[Tuple[int, int, int, int, float]]:
        """Find NPC HP bars in the viewport. Returns (x, y, w, h, hp_percent)."""
        if viewport is None or viewport.size == 0:
            return []

        green_mask = cv2.inRange(viewport, np.array(HP_GREEN_RANGE[0]), np.array(HP_GREEN_RANGE[1]))
        red_mask = cv2.inRange(viewport, np.array(HP_RED_RANGE[0]), np.array(HP_RED_RANGE[1]))
        combined = cv2.bitwise_or(green_mask, red_mask)

        contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        bars = []
        bar_h = self.calibration.hp_bar_height
        for cnt in contours:
            x, y, bw, bh = cv2.boundingRect(cnt)
            # HP bars are thin and wide
            if bw >= 15 and bh <= max(bar_h + 4, 12) and bw > bh * 2:
                bar_region = viewport[y:y + bh, x:x + bw]
                g_px = int(np.count_nonzero(
                    cv2.inRange(bar_region, np.array(HP_GREEN_RANGE[0]), np.array(HP_GREEN_RANGE[1]))
                ))
                total_px = bw * bh
                hp_pct = (g_px / total_px) * 100.0 if total_px > 0 else 100.0
                bars.append((x, y, bw, bh, hp_pct))

        # Sort by size (bigger bars = more prominent)
        bars.sort(key=lambda b: b[2] * b[3], reverse=True)
        return bars[:10]  # Max 10 bars

    # ── Inventory slot detection ──────────────────────────────────────────

    def get_inventory_slot_centers(self, w: int, h: int) -> List[Tuple[int, int]]:
        """Get pixel center of each inventory slot (1-28). Index 0 = slot 1."""
        x1, y1, x2, y2 = self.region_px("inventory", w, h)
        inv_w = x2 - x1
        inv_h = y2 - y1

        cols = self.calibration.inventory_cols
        rows = self.calibration.inventory_rows
        slot_w = inv_w / cols
        slot_h = inv_h / rows

        centers = []
        for row in range(rows):
            for col in range(cols):
                cx = int(x1 + col * slot_w + slot_w / 2)
                cy = int(y1 + row * slot_h + slot_h / 2)
                centers.append((cx, cy))
        return centers

    def get_inventory_slot_rects(self, w: int, h: int) -> List[Tuple[int, int, int, int]]:
        """Get (x, y, w, h) rectangles for each inventory slot."""
        x1, y1, x2, y2 = self.region_px("inventory", w, h)
        inv_w = x2 - x1
        inv_h = y2 - y1

        cols = self.calibration.inventory_cols
        rows = self.calibration.inventory_rows
        sw = int(inv_w / cols)
        sh = int(inv_h / rows)

        rects = []
        for row in range(rows):
            for col in range(cols):
                sx = int(x1 + col * sw)
                sy = int(y1 + row * sh)
                rects.append((sx, sy, sw, sh))
        return rects

    def _count_empty_inv_slots(self, image: np.ndarray, w: int, h: int) -> int:
        """Count how many inventory slots are empty."""
        rects = self.get_inventory_slot_rects(w, h)
        empty = 0
        for (sx, sy, sw, sh) in rects:
            pad = max(sw // 4, 3)
            slot_img = image[sy + pad:sy + sh - pad, sx + pad:sx + sw - pad]
            if slot_img.size == 0:
                empty += 1
                continue
            # Empty slots have low color variance (uniform background)
            std = float(np.std(slot_img))
            if std < 18:
                empty += 1
        return empty

    # ── Ground item detection ─────────────────────────────────────────────

    def _find_ground_item_text(self, viewport: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Find ground item text in the viewport (colored text on the ground)."""
        results = []
        for color_range in [GROUND_TEXT_WHITE, GROUND_TEXT_CYAN, GROUND_TEXT_GREEN]:
            blobs = self._find_color_blobs(viewport, color_range, min_area=25, max_area=4000)
            for (bx, by) in blobs:
                results.append((bx - 20, by - 5, 40, 10))  # Approximate text box
        return results

    # ── Generic color blob finder ─────────────────────────────────────────

    @staticmethod
    def _find_color_blobs(
        image: np.ndarray,
        color_range: Tuple[Tuple[int, int, int], Tuple[int, int, int]],
        min_area: int = 5,
        max_area: int = 5000,
    ) -> List[Tuple[int, int]]:
        """Find center points of color blobs in an image."""
        if image is None or image.size == 0:
            return []

        mask = cv2.inRange(image, np.array(color_range[0]), np.array(color_range[1]))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        points = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if min_area <= area <= max_area:
                M = cv2.moments(cnt)
                if M["m00"] > 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    points.append((cx, cy))
        return points

    # ── Login screen helpers ──────────────────────────────────────────────

    def get_login_field_positions(self, w: int, h: int) -> Dict[str, Tuple[int, int]]:
        """Get common positions on the login screen."""
        return {
            "existing_user_button": (w // 2, int(h * 0.55)),
            "username_field": (w // 2, int(h * 0.42)),
            "password_field": (w // 2, int(h * 0.47)),
            "login_button": (w // 2, int(h * 0.53)),
            "lobby_play_button": (w // 2, int(h * 0.70)),
        }
