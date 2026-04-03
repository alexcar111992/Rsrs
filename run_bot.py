"""Launch the RSPS Bot Client GUI."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from rsps_bot.gui.main_window import run_gui

if __name__ == "__main__":
    run_gui()
