"""
Entry point for the Robot Scenario Runner application.

- Initializes the PySide6 application
- Creates and shows the main window

Responsibility:
 - Bootstraps the GUI application and opens the main window implementation in `ui/main_window.py`.
"""
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    root = Path(__file__).parent
    window = MainWindow(project_root=root)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
