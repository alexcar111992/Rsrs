# RSPS Bot Client

A universal RuneScape Private Server bot that works through a simple GUI.
**No scripting. No AI. No coding knowledge needed.**

You configure everything through dropdowns, text fields, checkboxes, and sliders.

---

## Features

### Combat / NPC
- Type the NPC name, set its max HP, pick an action (Attack, Talk-to, Pickpocket, etc.)
- Add multiple NPC targets with priority ordering
- Auto re-attack when an NPC spawns
- Eat food automatically when HP drops below your set %
- Use potions on cooldown or at thresholds
- Special attack support

### Inventory Management
- Configure any inventory slot (1-28) with custom actions
- Triggers: "When HP below %", "On cooldown", "When inventory full", "When in/not in combat"
- Actions: Eat, Drop, Use, Wield, Bury, Use on NPC/Object

### Loot Pickup
- Add specific items to pick up after kills
- Or enable "Pick up ALL" mode
- Priority ordering for valuable items first

### Auto-Login
- Automatically logs back in if disconnected
- Configurable retry delay and max attempts
- Handles login screen, lobby, and disconnect messages

### Mouse Modes
- **Real Mouse**: Moves your physical cursor (1 client at a time)
- **Ghost Mouse**: Sends clicks directly to the game window - you keep your mouse free and can run multiple clients simultaneously

### Anti-Ban
- Random camera rotations
- Mouse drift
- Random short pauses
- Occasional AFK breaks
- All configurable with sliders

### Profiles
- Save/load all settings as JSON profiles
- Switch between different bot setups instantly

---

## Installation (Windows 11)

### 1. Install Python
Download from https://www.python.org/downloads/
**Check "Add Python to PATH" during installation.**

### 2. Install Dependencies
Double-click `install.bat` or run:
```
pip install PyQt5 Pillow opencv-python numpy pyautogui pywin32 keyboard mouse mss requests
```

### 3. Run the Bot
Double-click `start_bot.bat` or run:
```
python run_bot.py
```

---

## How to Use

1. **Open your RSPS client** (any revision: 317, 474, 508, 667, 718, etc.)
2. **Launch the bot** (`start_bot.bat`)
3. **Select your game window** from the dropdown at the top
4. **Pick your layout** (317/OSRS, 474, 667, etc.)
5. **Configure the Combat tab**:
   - Type the NPC name (e.g. "Rock Crab")
   - Set its max HP (e.g. 50)
   - Pick action: Attack
   - Check "Re-attack on spawn"
6. **Configure Inventory** (optional):
   - Add food slots (e.g. Slot 25 = Shark, eat when HP below 50%)
7. **Configure Loot** (optional):
   - Add items to pick up or enable "Pick up all"
8. **Set Mouse Mode**:
   - Ghost Mouse = hands-free, multi-client
   - Real Mouse = visible cursor movement
9. **Press START (F5)**

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| F5  | Start  |
| F6  | Stop   |
| F7  | Pause  |

---

## Supported Layouts

| Layout | Revisions |
|--------|-----------|
| 317 / OSRS Fixed | 317, 325, 377, OSRS |
| 474 / 508 Fixed | 474, 498, 508, 525 |
| 667 / 718 Fixed | 614, 667, 718, 742 |
| Custom (Calibrate) | Any other layout |

---

## Project Structure

```
Rsrs/
  run_bot.py          - Launch the bot
  install.bat         - Install dependencies
  start_bot.bat       - Quick launcher
  requirements.txt    - Python dependencies
  rsps_bot/
    core/
      config.py           - All settings and profile management
      screen_capture.py   - Window finding and screenshot capture
      mouse_controller.py - Real mouse + Ghost mouse modes
      interface_detector.py - Reads game screen (HP, inventory, NPCs, login)
      combat_system.py    - NPC fighting logic
      loot_system.py      - Ground item pickup
      inventory_manager.py - Inventory slot actions
      login_system.py     - Auto-login and disconnect recovery
      antiban.py          - Human-like behavior
      bot_engine.py       - Main loop tying everything together
    gui/
      main_window.py    - Main application window
      tab_combat.py     - Combat/NPC configuration tab
      tab_inventory.py  - Inventory actions tab
      tab_loot.py       - Loot pickup tab
      tab_login.py      - Auto-login tab
      tab_mouse.py      - Mouse mode tab
      tab_antiban.py    - Anti-ban settings tab
  profiles/             - Saved bot profiles (JSON)
```
