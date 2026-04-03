"""Main GUI window - ties all tabs together."""

import subprocess
import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QFormLayout, QPushButton, QLabel, QStatusBar, QMessageBox,
    QFileDialog, QComboBox, QGroupBox, QLineEdit, QCheckBox,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont

from rsps_bot.core.bot_engine import BotEngine
from rsps_bot.core.config import BotProfile, LAYOUT_PRESETS
from rsps_bot.core.screen_capture import WindowInfo
from rsps_bot.gui.tab_combat import CombatTab
from rsps_bot.gui.tab_skilling import SkillingTab
from rsps_bot.gui.tab_inventory import InventoryTab
from rsps_bot.gui.tab_loot import LootTab
from rsps_bot.gui.tab_login import LoginTab
from rsps_bot.gui.tab_mouse import MouseTab
from rsps_bot.gui.tab_antiban import AntibanTab


class StatusBridge(QObject):
    """Thread-safe bridge to push status updates to GUI."""
    status_signal = pyqtSignal(str)
    stats_signal = pyqtSignal(object)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RSPS Bot Client v1.0 - No Scripts Needed")
        self.setMinimumSize(920, 720)
        self.resize(960, 760)

        self.engine = BotEngine()
        self.profile = BotProfile()
        self._windows = []
        self.bridge = StatusBridge()
        self.bridge.status_signal.connect(self._on_status)
        self.bridge.stats_signal.connect(self._on_stats)
        self.engine.on_status_update = lambda msg: self.bridge.status_signal.emit(msg)
        self.engine.on_stats_update = lambda s: self.bridge.stats_signal.emit(s)

        self._build_ui()
        self._apply_dark_theme()

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_windows)
        self.refresh_timer.start(5000)
        self._refresh_windows()

    # ── UI Construction ───────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(6)
        root.setContentsMargins(8, 8, 8, 8)

        # ── Game Client Section ───────────────────────────────────────
        client_group = QGroupBox("Game Client")
        client_form = QFormLayout(client_group)
        client_form.setSpacing(8)
        client_form.setContentsMargins(12, 20, 12, 10)

        # Row 1: .jar file path
        jar_row = QHBoxLayout()
        self.jar_path_edit = QLineEdit()
        self.jar_path_edit.setPlaceholderText(r"e.g. C:\Users\Conor\Desktop\Launcher Retro.jar")
        jar_row.addWidget(self.jar_path_edit, 1)
        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self._browse_jar)
        jar_row.addWidget(btn_browse)
        btn_launch = QPushButton("Launch Client")
        btn_launch.setStyleSheet("background:#1a6b1a; color:white;")
        btn_launch.clicked.connect(self._launch_client)
        jar_row.addWidget(btn_launch)
        client_form.addRow("Client Path:", jar_row)

        # Row 2: Game window
        win_row = QHBoxLayout()
        self.window_combo = QComboBox()
        self.window_combo.setEditable(True)
        self.window_combo.lineEdit().setPlaceholderText("Select detected window or type window title...")
        win_row.addWidget(self.window_combo, 1)
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self._refresh_windows)
        win_row.addWidget(btn_refresh)
        client_form.addRow("Game Window:", win_row)

        # Row 3: Layout
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(LAYOUT_PRESETS.keys())
        self.layout_combo.setMaximumWidth(250)
        client_form.addRow("Interface Layout:", self.layout_combo)

        # Row 4: Simple mode
        self.chk_simple_mode = QCheckBox("SIMPLE MODE  -  just attack + loot, skip food/inventory (for easy NPCs)")
        self.chk_simple_mode.setStyleSheet("color: #a6e3a1; font-weight: bold; font-size: 11px;")
        client_form.addRow(self.chk_simple_mode)

        root.addWidget(client_group)

        # ── Tabs ──────────────────────────────────────────────────────
        self.tabs = QTabWidget()
        self.tab_combat = CombatTab()
        self.tab_skilling = SkillingTab()
        self.tab_inventory = InventoryTab()
        self.tab_loot = LootTab()
        self.tab_login = LoginTab()
        self.tab_mouse = MouseTab()
        self.tab_antiban = AntibanTab()

        self.tabs.addTab(self.tab_combat, "Combat / NPC")
        self.tabs.addTab(self.tab_skilling, "Skilling")
        self.tabs.addTab(self.tab_inventory, "Inventory")
        self.tabs.addTab(self.tab_loot, "Loot")
        self.tabs.addTab(self.tab_login, "Auto-Login")
        self.tabs.addTab(self.tab_mouse, "Mouse Mode")
        self.tabs.addTab(self.tab_antiban, "Anti-Ban")
        root.addWidget(self.tabs, 1)

        # Simple mode toggles
        self.chk_simple_mode.toggled.connect(self._on_simple_mode_toggled)

        # ── Live Stats ────────────────────────────────────────────────
        stats_box = QGroupBox("Live Stats")
        stats_lay = QHBoxLayout(stats_box)
        stats_lay.setSpacing(20)
        self.lbl_kills = QLabel("Kills: 0")
        self.lbl_kph = QLabel("K/hr: 0")
        self.lbl_food = QLabel("Food: 0")
        self.lbl_loot = QLabel("Loot: 0")
        self.lbl_runtime = QLabel("Time: 0m")
        for lbl in (self.lbl_kills, self.lbl_kph, self.lbl_food, self.lbl_loot, self.lbl_runtime):
            lbl.setFont(QFont("Consolas", 10, QFont.Bold))
            stats_lay.addWidget(lbl)
        stats_lay.addStretch()
        root.addWidget(stats_box)

        # ── Control Buttons ───────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.btn_start = QPushButton("  START (F5)  ")
        self.btn_start.setStyleSheet("background:#2a7a2a; color:white; font-size:13px; padding:8px 16px;")
        self.btn_start.clicked.connect(self._start)
        self.btn_pause = QPushButton("  PAUSE (F7)  ")
        self.btn_pause.setStyleSheet("background:#b58a00; color:white; font-size:13px; padding:8px 16px;")
        self.btn_pause.clicked.connect(self._pause)
        self.btn_stop = QPushButton("  STOP (F6)  ")
        self.btn_stop.setStyleSheet("background:#a02020; color:white; font-size:13px; padding:8px 16px;")
        self.btn_stop.clicked.connect(self._stop)
        btn_save = QPushButton("Save Profile")
        btn_save.clicked.connect(self._save_profile)
        btn_load = QPushButton("Load Profile")
        btn_load.clicked.connect(self._load_profile)
        btn_row.addWidget(self.btn_start)
        btn_row.addWidget(self.btn_pause)
        btn_row.addWidget(self.btn_stop)
        btn_row.addStretch()
        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_load)
        root.addLayout(btn_row)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Select your game client, configure settings, press START")

    # ── Actions ───────────────────────────────────────────────────────

    def _browse_jar(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select RSPS Client",
            os.path.expanduser("~\\Desktop"),
            "Java Files (*.jar);;All Files (*)",
        )
        if path:
            self.jar_path_edit.setText(path)
            self.status_bar.showMessage(f"Client path set: {path}")

    def _launch_client(self):
        path = self.jar_path_edit.text().strip()
        if not path:
            QMessageBox.warning(self, "No Path", "Enter or browse for a .jar client file first!")
            return
        if not os.path.isfile(path):
            QMessageBox.warning(self, "File Not Found", f"File not found:\n{path}")
            return
        try:
            subprocess.Popen(["java", "-jar", path], cwd=os.path.dirname(path))
            self.status_bar.showMessage(f"Launching: {os.path.basename(path)} ... wait a few seconds then click Refresh")
        except FileNotFoundError:
            try:
                subprocess.Popen(["javaw", "-jar", path], cwd=os.path.dirname(path))
                self.status_bar.showMessage(f"Launching: {os.path.basename(path)}")
            except FileNotFoundError:
                QMessageBox.critical(self, "Java Not Found",
                    "Java is not installed or not in PATH.\n"
                    "Install Java from https://adoptium.net/ or https://java.com")
        except Exception as e:
            QMessageBox.critical(self, "Launch Error", f"Failed to launch client:\n{e}")

    def _on_simple_mode_toggled(self, checked: bool):
        self.tab_inventory.setEnabled(not checked)
        inv_idx = self.tabs.indexOf(self.tab_inventory)
        if checked:
            self.tabs.setTabText(inv_idx, "Inventory (Simple Mode)")
            self.status_bar.showMessage("Simple Mode ON - attack + loot only, no food/inventory needed")
        else:
            self.tabs.setTabText(inv_idx, "Inventory")

    def _refresh_windows(self):
        custom_text = self.window_combo.currentText()
        self.window_combo.clear()
        self._windows = []
        windows = self.engine.find_game_windows()
        self._windows = windows
        for w in windows:
            self.window_combo.addItem(f"{w.title} ({w.width}x{w.height})")
        if custom_text:
            idx = self.window_combo.findText(custom_text)
            if idx >= 0:
                self.window_combo.setCurrentIndex(idx)
            else:
                self.window_combo.setEditText(custom_text)

    def _find_window_by_text(self, text: str):
        for w in self._windows:
            display = f"{w.title} ({w.width}x{w.height})"
            if display == text:
                return w
        if text.strip():
            matches = self.engine.find_game_windows(text.strip())
            if matches:
                return matches[0]
        return None

    def _collect_profile(self) -> BotProfile:
        p = BotProfile()
        p.layout = self.layout_combo.currentText()
        p.client_jar_path = self.jar_path_edit.text().strip()
        p.npc_targets = self.tab_combat.get_targets()
        p.combat = self.tab_combat.get_settings()
        p.combat.simple_mode = self.chk_simple_mode.isChecked()
        p.skilling = self.tab_skilling.get_settings()
        p.inventory_actions = self.tab_inventory.get_actions()
        p.loot_rules = self.tab_loot.get_rules()
        p.login = self.tab_login.get_settings()
        p.mouse = self.tab_mouse.get_settings()
        p.antiban = self.tab_antiban.get_settings()
        from rsps_bot.core.config import CalibrationData
        p.calibration = CalibrationData(layout_name=p.layout)
        return p

    def _start(self):
        text = self.window_combo.currentText().strip()
        if not text:
            QMessageBox.warning(self, "No Window",
                "Select a game window from the dropdown, or type the window title!")
            return
        window = self._find_window_by_text(text)
        if not window:
            QMessageBox.warning(self, "Window Not Found",
                f"Could not find a window matching:\n\"{text}\"\n\n"
                "Make sure your RSPS client is open, then click Refresh.")
            return
        self.engine.set_window(window)
        self.status_bar.showMessage(f"Attached to: {window.title} ({window.width}x{window.height})")
        profile = self._collect_profile()
        self.engine.apply_profile(profile)
        self.engine.start()

    def _pause(self):
        self.engine.pause()

    def _stop(self):
        self.engine.stop()

    def _save_profile(self):
        profile = self._collect_profile()
        path, _ = QFileDialog.getSaveFileName(self, "Save Profile", "", "JSON Files (*.json)")
        if path:
            profile.save(path)
            self.status_bar.showMessage(f"Profile saved to {path}")

    def _load_profile(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load Profile", "", "JSON Files (*.json)")
        if path:
            try:
                profile = BotProfile.load(path)
                self.tab_combat.load_profile(profile)
                self.tab_skilling.load_profile(profile)
                self.tab_inventory.load_profile(profile)
                self.tab_loot.load_profile(profile)
                self.tab_login.load_profile(profile)
                self.tab_mouse.load_profile(profile)
                self.tab_antiban.load_profile(profile)
                self.layout_combo.setCurrentText(profile.layout)
                self.jar_path_edit.setText(profile.client_jar_path)
                self.chk_simple_mode.setChecked(profile.combat.simple_mode)
                self.status_bar.showMessage(f"Loaded profile: {profile.name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load profile:\n{e}")

    # ── Callbacks ─────────────────────────────────────────────────────

    def _on_status(self, msg: str):
        self.status_bar.showMessage(msg)

    def _on_stats(self, stats):
        self.lbl_kills.setText(f"Kills: {stats.npcs_killed}")
        self.lbl_kph.setText(f"K/hr: {stats.kills_per_hour:.0f}")
        self.lbl_food.setText(f"Food: {stats.food_eaten}")
        self.lbl_loot.setText(f"Loot: {stats.loot_picked}")
        self.lbl_runtime.setText(f"Time: {stats.runtime_minutes:.0f}m")

    def _apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background: #1e1e2e; color: #cdd6f4;
                font-size: 11px;
            }
            QGroupBox {
                border: 1px solid #45475a; border-radius: 6px;
                margin-top: 10px; padding-top: 16px;
                font-weight: bold; font-size: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin; left: 10px; padding: 0 4px;
            }
            QTabWidget::pane {
                border: 1px solid #45475a; border-radius: 4px;
            }
            QTabBar::tab {
                background: #313244; padding: 7px 18px; margin-right: 2px;
                border-radius: 4px 4px 0 0; font-size: 11px;
            }
            QTabBar::tab:selected { background: #45475a; }
            QComboBox, QLineEdit, QSpinBox {
                background: #313244; border: 1px solid #585b70;
                border-radius: 4px; padding: 5px 8px; color: #cdd6f4;
                min-height: 22px;
            }
            QPushButton {
                background: #45475a; border: none; border-radius: 4px;
                padding: 6px 14px; color: #cdd6f4;
            }
            QPushButton:hover { background: #585b70; }
            QCheckBox { spacing: 8px; }
            QSlider::groove:horizontal {
                background: #313244; height: 6px; border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #89b4fa; width: 14px; margin: -4px 0; border-radius: 7px;
            }
            QStatusBar { background: #181825; color: #a6adc8; font-size: 11px; }
            QLabel { color: #cdd6f4; }
            QScrollArea { border: none; }
        """)

    def closeEvent(self, event):
        self.engine.stop()
        event.accept()


def run_gui():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
