from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from .sidebar import Sidebar
from .pages.downloads_page import DownloadsPage
from .pages.converter_page import ConverterPage
from .pages.settings_page import SettingsPage


class MainWindow(QMainWindow):
    """Main application window with a modern sidebar + stacked pages layout."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Audio Hub – YouTube Downloader & Audio Converter")
        self.setMinimumSize(1100, 720)
        self.setObjectName("MainWindow")

        self._init_ui()

    def _init_ui(self) -> None:
        # Central layout: Sidebar (left) + Stacked pages (right)
        central = QWidget(self)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.setFixedWidth(180)  # Hacer el sidebar más angosto

        self.page_stack = QStackedWidget()
        self.page_stack.setObjectName("PageStack")

        self.downloads_page = DownloadsPage()
        self.converter_page = ConverterPage()
        self.settings_page = SettingsPage()

        self.page_stack.addWidget(self.downloads_page)
        self.page_stack.addWidget(self.converter_page)
        self.page_stack.addWidget(self.settings_page)

        root.addWidget(self.sidebar)
        root.addWidget(self.page_stack, 1)
        self.setCentralWidget(central)

        # Sidebar navigation wiring
        self.sidebar.navRequested.connect(self._on_nav_requested)





    # Slots
    def _on_nav_requested(self, page_name: str) -> None:
        mapping = {
            "descargas": self.downloads_page,
            "convertir": self.converter_page,
            "configuracion": self.settings_page,
        }
        widget = mapping.get(page_name)
        if widget is not None:
            self.page_stack.setCurrentWidget(widget)



    def _refresh_current(self) -> None:
        current = self.page_stack.currentWidget()
        if hasattr(current, "refresh"):
            current.refresh()  # type: ignore[attr-defined]




