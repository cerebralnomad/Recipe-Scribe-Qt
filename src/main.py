#!/usr/bin/env python3
"""
main.py

Entry point for Recipe Scribe Qt. Sets up the QApplication, loads config,
and launches the main recipe entry window.
"""

import sys

from PyQt6.QtWidgets import QApplication

from config import AppConfig
from theme import apply_theme
from windows.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)

    config = AppConfig()
    config.load()

    # Theme must be applied before any windows/widgets are constructed -
    # see theme.py's module docstring. A change to dark_mode at runtime
    # (via the Config menu) triggers a full restart, matching the original
    # app's behavior, rather than attempting a live palette swap.
    apply_theme(app, config.dark_mode)

    window = MainWindow(config)
    window.resize(1000, 700)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
