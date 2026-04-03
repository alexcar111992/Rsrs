"""Main GUI window - ties all tabs together."""

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QStatusBar, QMessageBox,
    QFileDialog, QComboBox, QGroupBox,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont

from rsps_bot.core.bot_engine import BotEngine
from rsps_bot.core.config import BotProfile, LAYOUT_PRESETS
from rsps_bot.core.screen_capture import WindowInfo
from rsps_bot.gui.tab_combat import CombatTab
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
        self.setMinimumSize(750, 620)

        self.engine = BotEngine()
        self.profile = BotProfile()
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

        # Top bar: window selection + layout
        top = QGroupBox("Game Window")
        top_lay = QHBoxLayout(top)
        top_lay.addWidget(QLabel("Window:"))
        self.window_combo = QComboBox()
        self.window_combo.setMinimumWidth(250)
        top_lay.addWidget(self.window_combo, 1)
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self._refresh_windows)
        top_lay.addWidget(btn_refresh)
        top_lay.addWidget(QLabel("Layout:"))
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(LAYOUT_PRESETS.keys())
        top_lay.addWidget(self.layout_combo)
        root.addWidget(top)

        # Tabs
        self.tabs = QTabWidget()
        self.tab_combat = CombatTab()
        self.tab_inventory = InventoryTab()
        self.tab_loot = LootTab()
        self.tab_login = LoginTab()
        self.tab_mouse = MouseTab()
        self.tab_antiban = AntibanTab()

        self.tabs.addTab(self.tab_combat, "Combat / NPC")
        self.tabs.addTab(self.tab_inventory, "Inventory")
        self.tabs.addTab(self.tab_loot, "Loot")
        self.tabs.addTab(self.tab_login, "Auto-Login")
        self.tabs.addTab(self.tab_mouse, "Mouse Mode")
        self.tabs.addTab(self.tab_antiban, "Anti-Ban")
        root.addWidget(self.tabs, 1)

        # Stats bar
        stats_box = QGroupBox("Live Stats")
        stats_lay = QHBoxLayout(stats_box)
        self.lbl_kills = QLabel("Kills: 0")
        self.lbl_kph = QLabel("K/hr: 0")
        self.lbl_food = QLabel("Food: 0")
        self.lbl_loot = QLabel("Loot: 0")
        self.lbl_runtime = QLabel("Time: 0m")
        for lbl in (self.lbl_kills, self.lbl_kph, self.lbl_food, self.lbl_loot, self.lbl_runtime):
            lbl.setFont(QFont("Consolas", 10))
            stats_lay.addWidget(lbl)
        root.addWidget(stats_box)

        # Control buttons
        btn_row = QHBoxLayout()
        self.btn_start = QPushButton("START (F5)")
        self.btn_start.setStyleSheet("background:#2a7a2a;color:white;font-size:14px;padding:8px;")
        self.btn_start.clicked.connect(self._start)
        self.btn_pause = QPushButton("PAUSE (F7)")
        self.btn_pause.setStyleSheet("background:#b58a00;color:white;font-size:14px;padding:8px;")
        self.btn_pause.clicked.connect(self._pause)
        self.btn_stop = QPushButton("STOP (F6)")
        self.btn_stop.setStyleSheet("background:#a02020;color:white;font-size:14px;padding:8px;")
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
        self.status_bar.showMessage("Ready - Configure your settings and press START")

    # ── Actions ───────────────────────────────────────────────────────

    def _refresh_windows(self):
        current_text = self.window_combo.currentText()
        self.window_combo.clear()
        windows = self.engine.find_game_windows()
        self._windows = windows
        for w in windows:
            self.window_combo.addItem(f"{w.title} ({w.width}x{w.height})", w)
        # Restore selection
        for i in range(self.window_combo.count()):
            if self.window_combo.itemText(i) == current_text:
                self.window_combo.setCurrentIndex(i)
                break

    def _collect_profile(self) -> BotProfile:
        """Read all GUI fields into a BotProfile."""
        p = BotProfile()
        p.layout = self.layout_combo.currentText()
        p.npc_targets = self.tab_combat.get_targets()
        p.combat = self.tab_combat.get_settings()
        p.inventory_actions = self.tab_inventory.get_actions()
        p.loot_rules = self.tab_loot.get_rules()
        p.login = self.tab_login.get_settings()
        p.mouse = self.tab_mouse.get_settings()
        p.antiban = self.tab_antiban.get_settings()
        # Set calibration layout
        from rsps_bot.core.config import CalibrationData
        p.calibration = CalibrationData(layout_name=p.layout)
        return p

    def _start(self):
        # Get selected window
        idx = self.window_combo.currentIndex()
        if idx < 0 or idx >= len(self._windows):
            QMessageBox.warning(self, "No Window", "Select a game window first!")
            return
        window = self._windows[idx]
        self.engine.set_window(window)

        # Collect profile from GUI
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
                self.tab_inventory.load_profile(profile)
                self.tab_loot.load_profile(profile)
                self.tab_login.load_profile(profile)
                self.tab_mouse.load_profile(profile)
                self.tab_antiban.load_profile(profile)
                self.layout_combo.setCurrentText(profile.layout)
                self.status_bar.showMessage(f"Loaded: {profile.name}")
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
            QMainWindow, QWidget { background: #1e1e2e; color: #cdd6f4; }
            QGroupBox { border: 1px solid #45475a; border-radius: 6px; margin-top: 8px; padding-top: 14px; font-weight: bold; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; }
            QTabWidget::pane { border: 1px solid #45475a; border-radius: 4px; }
            QTabBar::tab { background: #313244; padding: 6px 16px; margin-right: 2px; border-radius: 4px 4px 0 0; }
            QTabBar::tab:selected { background: #45475a; }
            QComboBox, QLineEdit, QSpinBox { background: #313244; border: 1px solid #585b70; border-radius: 4px; padding: 4px 8px; color: #cdd6f4; }
            QPushButton { background: #45475a; border: none; border-radius: 4px; padding: 6px 14px; color: #cdd6f4; }
            QPushButton:hover { background: #585b70; }
            QCheckBox { spacing: 6px; }
            QSlider::groove:horizontal { background: #313244; height: 6px; border-radius: 3px; }
            QSlider::handle:horizontal { background: #89b4fa; width: 14px; margin: -4px 0; border-radius: 7px; }
            QStatusBar { background: #181825; color: #a6adc8; }
            QLabel { color: #cdd6f4; }
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
