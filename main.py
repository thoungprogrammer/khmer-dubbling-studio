"""
Khmer Dubbing Studio - Main Entry Point
Automatic multi-language to Khmer video dubbing using AI.
"""
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontDatabase

from ui.main_window import MainWindow
from config import APP_NAME, APP_VERSION


# Priority list of Khmer fonts to try
KHMER_FONTS_PRIORITY = [
    "Noto Sans Khmer",
    "Khmer OS",
    "Khmer OS Content",
    "Kantumruy",
    "Battambang",
    "Khmer UI",
    "Khmer",
]


def _select_best_khmer_font() -> str:
    """Return the best Khmer font available on this system."""
    available = QFontDatabase.families()
    for name in KHMER_FONTS_PRIORITY:
        if name in available:
            return name
    # Last resort — scan for any Khmer font
    for name in available:
        if "Khmer" in name:
            return name
    return "Arial"


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    # Pick the best Khmer font and set it as the app default
    # This ensures all widgets that display Khmer text render correctly
    best_khmer_font = _select_best_khmer_font()
    print(f"[Font] Using Khmer font: {best_khmer_font}")

    # Default app font — Segoe UI for Latin, Khmer font for Khmer chars
    # Qt automatically uses the fallback font for characters not in the primary
    app_font = QFont("Segoe UI", 10)
    app.setFont(app_font)

    # Store selected Khmer font globally so widgets can access it
    app.setProperty("khmerFont", best_khmer_font)

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
