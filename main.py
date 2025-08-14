import os
import sys
from PyQt6.QtWidgets import QApplication

from app.main_window import MainWindow
from app.utils import get_resource_path


def load_stylesheet(app: QApplication) -> None:
    """Load the global QSS stylesheet if it exists.

    This keeps styling centralized and allows easy theme tweaks without
    changing Python code.
    """
    qss_path = get_resource_path("style.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Audio Hub")
    app.setOrganizationName("AudioHub")
    app.setOrganizationDomain("audiohub.local")
    load_stylesheet(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()


