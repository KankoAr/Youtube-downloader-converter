from __future__ import annotations

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QWidget, QHBoxLayout
from PyQt6.QtGui import QIcon
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtGui import QPixmap, QPainter
from .utils import get_icon_path


class Sidebar(QFrame):
    """Modern vertical sidebar with navigation and a dark mode toggle."""

    navRequested = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("Sidebar")
        # Hacer la barra lateral más angosta
        try:
            # Un ancho fijo más angosto para ocupar menos espacio
            self.setFixedWidth(160)
        except Exception:
            pass
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 16)  # Reducir márgenes laterales
        layout.setSpacing(10)  # Reducir espaciado entre elementos

        title = QLabel("Menu")
        title.setObjectName("SidebarTitle")
        layout.addWidget(title)

        # Navigation buttons with modern icons
        self.btn_downloads = QPushButton("  Descargas")
        self.btn_downloads.setIcon(self._create_svg_icon(get_icon_path("download-white-svg.svg")))
        self.btn_convert = QPushButton("  Convertir")
        self.btn_convert.setIcon(self._create_svg_icon(get_icon_path("converter-white.svg")))
        self.btn_settings = QPushButton("  Configuración")
        self.btn_settings.setIcon(self._create_svg_icon(get_icon_path("configuration-white.svg")))
        for b in (self.btn_downloads, self.btn_convert):
            b.setObjectName("NavButton")
            b.setCheckable(True)
        self.btn_settings.setObjectName("NavButton")
        self.btn_settings.setCheckable(True)

        self.btn_downloads.setChecked(True)

        self.btn_downloads.clicked.connect(lambda: self._emit_nav("descargas"))
        self.btn_convert.clicked.connect(lambda: self._emit_nav("convertir"))
        self.btn_settings.clicked.connect(lambda: self._emit_nav("configuracion"))

        layout.addWidget(self.btn_downloads)
        layout.addWidget(self.btn_convert)
        layout.addWidget(self.btn_settings)

        layout.addStretch(1)

    def _create_svg_icon(self, svg_path: str, size: int = 16) -> QIcon:
        """Create a QIcon from an SVG file"""
        try:
            renderer = QSvgRenderer(svg_path)
            if not renderer.isValid():
                return QIcon()  # Return empty icon if SVG is invalid
            
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            
            return QIcon(pixmap)
        except Exception:
            return QIcon()  # Return empty icon on error

    def _emit_nav(self, name: str) -> None:
        # ensure exclusive selection
        mapping = {
            "descargas": self.btn_downloads,
            "convertir": self.btn_convert,
            "configuracion": self.btn_settings,
        }
        for key, btn in mapping.items():
            btn.setChecked(key == name)
        self.navRequested.emit(name)




