#!/usr/bin/env python3
"""
main.py

Entry point for Recipe Scribe Qt. Sets up the QApplication, loads config,
and launches the main recipe entry window.
"""

import sys

from PyQt6.QtWidgets import QApplication

from config import AppConfig
from windows.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)

    config = AppConfig()
    config.load()

    window = MainWindow(config)
    window.resize(1000, 700)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
