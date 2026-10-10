"""Application entry point."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from mixmind.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("MixMind AI")
    app.setOrganizationName("MixMind AI")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
