"""Global configuration for the RSPS Bot.

All settings are driven by the GUI - no scripting, no AI.
The user configures everything through text fields, dropdowns, and checkboxes.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Tuple


PROFILES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "profiles")

# ── Known RSPS interface layouts ──────────────────────────────────────────────
# These are ratio-based regions (x1, y1, x2, y2) relative to client size.
# Covers the most common RS client layouts (317, 474, 525, 667, 718, etc.)

LAYOUT_PRESETS = {
    "317 / OSRS Fixed": {
        "inventory": (0.725, 0.555, 0.985, 0.955),
        "minimap": (0.715, 0.005, 0.995, 0.225),
        "viewport": (0.005, 0.005, 0.71, 0.76),
        "chatbox": (0.005, 0.765, 0.52, 0.995),
        "hp_orb": (0.715, 0.235, 0.76, 0.275),
        "prayer_orb": (0.715, 0.28, 0.76, 0.32),
        "run_orb": (0.715, 0.325, 0.76, 0.365),
        "tabs_row": (0.725, 0.505, 0.985, 0.55),
        "target_info": (0.005, 0.005, 0.25, 0.05),
    },
    "474 / 508 Fixed": {
        "inventory": (0.725, 0.555, 0.985, 0.955),
        "minimap": (0.715, 0.005, 0.995, 0.225),
        "viewport": (0.005, 0.005, 0.71, 0.76),
        "chatbox": (0.005, 0.765, 0.52, 0.995),
        "hp_orb": (0.715, 0.235, 0.76, 0.275),
        "prayer_orb": (0.715, 0.28, 0.76, 0.32),
        "run_orb": (0.715, 0.325, 0.76, 0.365),
        "tabs_row": (0.725, 0.505, 0.985, 0.55),
        "target_info": (0.005, 0.005, 0.25, 0.05),
    },
    "667 / 718 Fixed": {
        "inventory": (0.725, 0.555, 0.985, 0.955),
        "minimap": (0.715, 0.005, 0.995, 0.225),
        "viewport": (0.005, 0.005, 0.71, 0.76),
        "chatbox": (0.005, 0.765, 0.52, 0.995),
        "hp_orb": (0.715, 0.235, 0.76, 0.275),
        "prayer_orb": (0.715, 0.28, 0.76, 0.32),
        "run_orb": (0.715, 0.325, 0.76, 0.365),
        "tabs_row": (0.725, 0.505, 0.985, 0.55),
        "target_info": (0.005, 0.005, 0.25, 0.05),
    },
    "Custom (Calibrate)": {
        "inventory": (0.725, 0.555, 0.985, 0.955),
        "minimap": (0.715, 0.005, 0.995, 0.225),
        "viewport": (0.005, 0.005, 0.71, 0.76),
        "chatbox": (0.005, 0.765, 0.52, 0.995),
        "hp_orb": (0.715, 0.235, 0.76, 0.275),
        "prayer_orb": (0.715, 0.28, 0.76, 0.32),
        "run_orb": (0.715, 0.325, 0.76, 0.365),
        "tabs_row": (0.725, 0.505, 0.985, 0.55),
        "target_info": (0.005, 0.005, 0.25, 0.05),
    },
}

# ── Color definitions for detection ───────────────────────────────────────────

# HP bar green (healthy portion)
HP_GREEN_RANGE = ((0, 120, 0), (80, 255, 80))
# HP bar red (damaged portion)
HP_RED_RANGE = ((120, 0, 0), (255, 80, 80))
# Yellow NPC hover text
NPC_HOVER_YELLOW = ((190, 190, 0), (255, 255, 80))
# White text on ground items
GROUND_TEXT_WHITE = ((200, 200, 200), (255, 255, 255))
# Cyan (valuable) ground items
GROUND_TEXT_CYAN = ((0, 200, 200), (100, 255, 255))
# Green ground items
GROUND_TEXT_GREEN = ((0, 180, 0), (100, 255, 100))
# Red NPC dots on minimap
MINIMAP_NPC_DOT = ((200, 0, 0), (255, 60, 60))
# Login screen yellow text
LOGIN_YELLOW = ((190, 170, 0), (255, 255, 70))


# ── NPC Interaction Options (dropdown choices) ────────────────────────────────

NPC_ACTIONS = [
    "Attack",
    "Talk-to",
    "Pickpocket",
    "Trade",
    "Examine",
    "Use item on NPC",
    "Custom...",
]

# ── Inventory item actions (dropdown choices) ─────────────────────────────────

ITEM_ACTIONS = [
    "Left-click (Eat / Drink / Use)",
    "Right-click > Drop",
    "Right-click > Use",
    "Right-click > Wield / Wear",
    "Right-click > Bury",
    "Use on NPC",
    "Use on object",
]

# ── Skilling types (dropdown choices) ─────────────────────────────────────────

SKILLING_TYPES = [
    "Mining (Rocks)",
    "Woodcutting (Trees)",
    "Fishing (Fishing spot)",
    "Thieving (Stalls)",
    "Cooking (Range / Fire)",
    "Smithing (Anvil / Furnace)",
    "Crafting (Spinning wheel / Pottery)",
    "Herblore (Clean / Mix)",
    "Fletching (Knife + Logs)",
    "Firemaking (Tinderbox + Logs)",
    "Runecrafting (Altar)",
    "Custom (click object)",
]

# What to do when inventory is full during skilling
INVENTORY_FULL_ACTIONS = [
    "Type ::empty (empties inventory)",
    "Type ::bank (opens bank)",
    "Drop all items",
    "Drop specific items",
    "Bank at nearest banker",
    "Stop skilling",
    "Do nothing (wait)",
]


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class NpcTarget:
    """An NPC the user wants to fight/interact with."""
    name: str = ""                     # User types NPC name
    max_health: int = 100              # User enters NPC max HP
    action: str = "Attack"             # Dropdown: Attack, Talk-to, etc.
    attack_on_spawn: bool = True       # Checkbox: re-attack as soon as one dies
    search_area: str = "Near player"   # Dropdown: Near player, Minimap, Whole viewport
    priority: int = 1                  # Dropdown: 1 (highest) to 5


@dataclass
class LootRule:
    """A loot pickup rule configured by the user."""
    item_name: str = ""                # User types item name (or "All")
    pickup: bool = True                # Checkbox: pick this up?
    priority: int = 1                  # Higher = pick up first


@dataclass
class InventorySlotAction:
    """An action to perform on a specific inventory slot/item."""
    slot_number: int = 0               # 1-28, user picks from dropdown
    item_description: str = ""         # User describes what's in this slot
    action: str = "Left-click (Eat / Drink / Use)"  # Dropdown
    trigger: str = "When HP below %"   # Dropdown: When HP below %, On cooldown, etc.
    trigger_value: int = 50            # The % or seconds value
    enabled: bool = True               # Checkbox


@dataclass
class LoginSettings:
    """Auto-login configuration."""
    enabled: bool = True               # Checkbox
    username: str = ""                 # Text field
    password: str = ""                 # Password field
    world: int = 1                     # Spinner
    retry_delay_seconds: int = 10      # Spinner
    max_retries: int = 10              # Spinner


@dataclass
class MouseSettings:
    """Mouse behavior settings."""
    mode: str = "Ghost Mouse"          # Dropdown: "Real Mouse", "Ghost Mouse"
    speed: str = "Normal"              # Dropdown: Slow, Normal, Fast, Instant
    humanize: bool = True              # Checkbox: add random human-like movement
    misclick_chance: float = 0.02      # Slider: 0-10%


@dataclass
class CombatSettings:
    """Combat behavior settings."""
    simple_mode: bool = False              # Checkbox: just attack+loot, no food/inventory
    eat_food: bool = True                  # Checkbox
    eat_at_hp_percent: int = 50            # Slider / spinner
    food_slots: List[int] = field(default_factory=lambda: [25, 26, 27, 28])
    use_potions: bool = False              # Checkbox
    potion_slots: List[int] = field(default_factory=list)
    drink_potion_trigger: str = "When stat below %"  # Dropdown
    drink_potion_value: int = 30           # Spinner
    use_special_attack: bool = False       # Checkbox
    special_at_percent: int = 100          # Spinner
    use_prayer: bool = False               # Checkbox
    prayer_name: str = ""                  # Dropdown of common prayers
    loot_after_kill: bool = True           # Checkbox
    loot_delay_ms: int = 500               # Spinner
    attack_on_spawn: bool = True           # Checkbox
    walk_to_npc: bool = True               # Checkbox


@dataclass
class AntibanSettings:
    """Anti-detection settings."""
    enabled: bool = True
    random_camera: bool = True
    random_mouse_drift: bool = True
    random_pauses: bool = True
    pause_min_seconds: int = 3
    pause_max_seconds: int = 30
    random_afk: bool = True
    afk_min_seconds: int = 30
    afk_max_seconds: int = 180
    afk_chance_percent: int = 5


@dataclass
class SkillingSettings:
    """Skilling configuration - for stationary skilling activities."""
    enabled: bool = False
    skill_type: str = "Mining (Rocks)"         # Dropdown: what skill
    object_name: str = ""                      # User types: e.g. "Iron rock", "Yew tree"
    object_action: str = "Left-click"          # Dropdown: Left-click or Right-click > option
    right_click_option: str = ""               # If right-click, what option text
    click_same_spot: bool = True               # Stay in place and re-click same spot
    re_click_delay_ms: int = 1000              # How long to wait before re-clicking
    wait_for_animation: bool = True            # Wait for idle before re-clicking
    inventory_full_action: str = "Type ::empty (empties inventory)"  # Dropdown
    drop_item_names: List[str] = field(default_factory=list)  # Items to drop if using "Drop specific"
    custom_command: str = ""                   # Custom ::command to type (e.g. ::empty, ::bank)
    use_item_on_object: bool = False           # E.g. knife on logs, tinderbox on logs
    use_item_slot: int = 1                     # Which inventory slot has the tool/item


@dataclass
class CalibrationData:
    """Stores calibration results for custom layouts."""
    layout_name: str = "317 / OSRS Fixed"
    regions: dict = field(default_factory=lambda: dict(LAYOUT_PRESETS["317 / OSRS Fixed"]))
    inventory_cols: int = 4
    inventory_rows: int = 7
    hp_bar_height: int = 5           # Pixel height of NPC HP bars


@dataclass
class BotProfile:
    """Complete bot profile - everything the user configured in the GUI."""
    name: str = "Default"
    window_title: str = ""                 # Text field - game window title to look for
    client_jar_path: str = ""              # File path to .jar client (e.g. Launcher Retro.jar)
    layout: str = "317 / OSRS Fixed"       # Dropdown

    npc_targets: List[NpcTarget] = field(default_factory=lambda: [NpcTarget()])
    loot_rules: List[LootRule] = field(default_factory=list)
    inventory_actions: List[InventorySlotAction] = field(default_factory=list)
    login: LoginSettings = field(default_factory=LoginSettings)
    mouse: MouseSettings = field(default_factory=MouseSettings)
    combat: CombatSettings = field(default_factory=CombatSettings)
    skilling: SkillingSettings = field(default_factory=SkillingSettings)
    antiban: AntibanSettings = field(default_factory=AntibanSettings)
    calibration: CalibrationData = field(default_factory=CalibrationData)

    # Hotkeys
    start_hotkey: str = "F5"
    stop_hotkey: str = "F6"
    pause_hotkey: str = "F7"

    def save(self, filepath: Optional[str] = None) -> str:
        """Save profile to JSON file."""
        if filepath is None:
            os.makedirs(PROFILES_DIR, exist_ok=True)
            safe_name = "".join(c if c.isalnum() or c in "-_ " else "" for c in self.name)
            filepath = os.path.join(PROFILES_DIR, f"{safe_name}.json")
        with open(filepath, "w") as f:
            json.dump(asdict(self), f, indent=2)
        return filepath

    @classmethod
    def load(cls, filepath: str) -> "BotProfile":
        """Load profile from JSON file."""
        with open(filepath, "r") as f:
            data = json.load(f)

        profile = cls()
        # Simple fields
        for key in ("name", "window_title", "layout", "start_hotkey", "stop_hotkey", "pause_hotkey"):
            if key in data:
                setattr(profile, key, data[key])

        # Nested dataclasses
        if "npc_targets" in data:
            profile.npc_targets = [NpcTarget(**n) for n in data["npc_targets"]]
        if "loot_rules" in data:
            profile.loot_rules = [LootRule(**r) for r in data["loot_rules"]]
        if "inventory_actions" in data:
            profile.inventory_actions = [InventorySlotAction(**a) for a in data["inventory_actions"]]
        if "login" in data:
            profile.login = LoginSettings(**data["login"])
        if "mouse" in data:
            profile.mouse = MouseSettings(**data["mouse"])
        if "combat" in data:
            profile.combat = CombatSettings(**data["combat"])
        if "skilling" in data:
            profile.skilling = SkillingSettings(**data["skilling"])
        if "antiban" in data:
            profile.antiban = AntibanSettings(**data["antiban"])
        if "calibration" in data:
            profile.calibration = CalibrationData(**data["calibration"])

        return profile

    @classmethod
    def list_profiles(cls) -> List[str]:
        """List all saved profile files."""
        if not os.path.exists(PROFILES_DIR):
            return []
        return [
            os.path.join(PROFILES_DIR, f)
            for f in os.listdir(PROFILES_DIR)
            if f.endswith(".json")
        ]
