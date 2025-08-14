from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional

import requests
import subprocess
import json
import urllib.parse
import traceback
from datetime import datetime
from PyQt6.QtCore import QBasicTimer, QRect, Qt, pyqtSignal, QObject, QSettings, QTimer
from PyQt6.QtGui import QPixmap, QGuiApplication
from PyQt6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QMessageBox,
)
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtCore import QUrl
from ..utils import get_icon_path


def clean_channel_name(channel_name: str) -> str:
    """Remove '- Topic' suffix from channel names."""
    if channel_name and "- Topic" in channel_name:
        return channel_name.replace("- Topic", "").strip()
    return channel_name


@dataclass
class DownloadItemData:
    title: str
    size_text: str
    speed_text: str
    progress: int = 0
    thumbnail_url: str = ""
    duration: str = ""
    channel: str = ""
    format_info: str = ""


class DownloadItemWidget(QWidget):
    def __init__(self, data: DownloadItemData) -> None:
        super().__init__()
        self.data = data
        self.worker = None  # Referencia al worker asociado
        self.worker_url = None  # URL del worker asociado
        self._build()

    def _build(self) -> None:
        # Layout principal con márgenes y espaciado optimizados
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 24, 20, 24)  # Aumentar márgenes verticales
        layout.setSpacing(20)

        # === THUMBNAIL SECTION ===
        self._build_thumbnail_section(layout)
        
        # === CONTENT SECTION ===
        content_layout = QVBoxLayout()
        content_layout.setSpacing(12)  # Reducir espaciado entre secciones
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header con título y botón cancelar
        self._build_header_section(content_layout)
        
        # Información del video (canal, duración, formato)
        self._build_video_info_section(content_layout)
        
        # Barra de progreso
        self._build_progress_section(content_layout)
        
        layout.addLayout(content_layout, 1)

    def _build_thumbnail_section(self, parent_layout):
        """Construye la sección de thumbnail"""
        # Contenedor para el thumbnail con bordes redondeados
        thumb_container = QWidget()
        thumb_container.setFixedSize(160, 90)  # Tamaño más grande manteniendo 16:9
        thumb_container.setStyleSheet("""
            QWidget {
                background: #1a1a27;
                border: 1px solid #2a2a3f;
                border-radius: 8px;
            }
        """)
        
        thumb_layout = QVBoxLayout(thumb_container)
        thumb_layout.setContentsMargins(4, 4, 4, 4)
        
        self.thumb = QLabel()
        self.thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb.setScaledContents(False)
        
        # Cargar thumbnail si está disponible
        if self.data.thumbnail_url or (hasattr(self.data, 'thumbnail_pixmap') and self.data.thumbnail_pixmap):
            self._load_thumbnail()
        else:
            self.thumb.setText("🎬")
            self.thumb.setStyleSheet("color: #6b7280; font-size: 36px;")
        
        thumb_layout.addWidget(self.thumb)
        parent_layout.addWidget(thumb_container)

    def _build_header_section(self, parent_layout):
        """Construye la sección del header con título y botón cancelar"""
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)
        
        # Título del video
        title_container = QVBoxLayout()
        title_container.setSpacing(6)  # Aumentar espaciado entre título y canal
        
        self.title = QLabel(self.data.title)
        self.title.setObjectName("DownloadTitle")
        self.title.setWordWrap(True)
        self.title.setMaximumHeight(48)  # Aumentar altura máxima para 3 líneas si es necesario
        self.title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.title.setMinimumHeight(20)  # Altura mínima para evitar colapso
        title_container.addWidget(self.title)
        
        # Canal del video
        self.channel = QLabel(self.data.channel or "")
        self.channel.setObjectName("DownloadMeta")
        self.channel.setMaximumHeight(20)  # Aumentar altura máxima del canal
        self.channel.setMinimumHeight(16)  # Altura mínima para el canal
        self.channel.setVisible(bool(self.data.channel))
        self.channel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)  # Altura fija para el canal
        title_container.addWidget(self.channel)
        
        header_layout.addLayout(title_container, 1)
        
        # Botón cancelar
        self.btn_cancel = QPushButton()
        self.btn_cancel.setIcon(self._create_svg_icon(get_icon_path("cancel-red.svg"), color="#e74c3c"))
        self.btn_cancel.setObjectName("CancelButton")
        self.btn_cancel.setToolTip("Cancelar descarga")
        self.btn_cancel.setFixedSize(28, 28)
        self.btn_cancel.clicked.connect(self._on_cancel_clicked)
        
        header_layout.addWidget(self.btn_cancel, alignment=Qt.AlignmentFlag.AlignTop)
        parent_layout.addLayout(header_layout)

    def _build_video_info_section(self, parent_layout):
        """Construye la sección de información del video"""
        print(f"DEBUG CARD: Construyendo info del video - formato: '{getattr(self.data, 'format_info', 'NO HAY')}'")
        
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(0, 4, 0, 4)  # Añadir margen vertical
        info_layout.setSpacing(8)  # Aumentar espaciado entre elementos
        
        # Formato
        if hasattr(self.data, 'format_info') and self.data.format_info:
            format_text = self.data.format_info
            # Mostrar el formato completo, no solo la primera parte
            print(f"DEBUG CARD: Mostrando formato: '{format_text}'")
            
            self.format_label = QLabel(format_text)
            self.format_label.setObjectName("DownloadFormat")
            info_layout.addWidget(self.format_label)
        
        # Separador
        if hasattr(self.data, 'format_info') and self.data.format_info:
            separator1 = QLabel("•")
            separator1.setObjectName("DownloadSeparator")
            separator1.setFixedWidth(8)
            separator1.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info_layout.addWidget(separator1)
        
        # Tamaño
        self.size_format = QLabel("")
        self.size_format.setObjectName("DownloadFormat")
        if self.data.size_text and self.data.size_text.strip():
            self.size_format.setText(self.data.size_text)
            self.size_format.setVisible(True)
        else:
            self.size_format.setVisible(False)
        info_layout.addWidget(self.size_format)
        
        # Separador
        if self.data.size_text and self.data.size_text.strip():
            separator2 = QLabel("•")
            separator2.setObjectName("DownloadSeparator")
            separator2.setFixedWidth(8)
            separator2.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info_layout.addWidget(separator2)
        
        # Duración
        self.duration_label = QLabel("")
        self.duration_label.setObjectName("DownloadFormat")
        if self.data.duration and self.data.duration.strip():
            self.duration_label.setText(self.data.duration)
            self.duration_label.setVisible(True)
        else:
            self.duration_label.setVisible(False)
        info_layout.addWidget(self.duration_label)
        
        info_layout.addStretch()
        parent_layout.addLayout(info_layout)

    def _build_progress_section(self, parent_layout):
        """Construye la sección del porcentaje y estado de progreso"""
        progress_layout = QHBoxLayout()
        progress_layout.setContentsMargins(0, 2, 0, 2)  # Reducir margen vertical
        progress_layout.setSpacing(8)  # Reducir espaciado entre elementos
        
        # Porcentaje a la izquierda
        self.progress_label = QLabel(f"{self.data.progress}%")
        self.progress_label.setObjectName("ProgressLabel")
        self.progress_label.setFixedWidth(45)
        

        
        # Estado de descarga a la derecha
        self.speed = QLabel(self.data.speed_text or "Preparando...")
        self.speed.setObjectName("SpeedLabel")
        
        progress_layout.addWidget(self.progress_label)
        progress_layout.addStretch()
        progress_layout.addWidget(self.speed)
        parent_layout.addLayout(progress_layout)



    def set_size_text(self, text: str) -> None:
        """Actualizar/mostrar el tamaño total en la fila de formato."""
        if hasattr(self, 'size_format') and isinstance(self.size_format, QLabel):
            if text:
                # Limpiar el texto de cualquier punto medio que pueda venir
                clean_text = text.replace("• ", "").replace(" •", "").strip()
                print(f"DEBUG: Actualizando tamaño en la tarjeta: '{text}' -> '{clean_text}'")
                self.size_format.setText(clean_text)
                self.size_format.setVisible(True)
                
                # Mostrar/ocultar el separador correspondiente
                if hasattr(self, 'separator2'):
                    self.separator2.setVisible(True)
                
                # Guardar el tamaño en los datos del widget para mantener consistencia
                if hasattr(self, 'data') and hasattr(self.data, 'size_text'):
                    self.data.size_text = clean_text
            else:
                print(f"DEBUG: Limpiando tamaño de la tarjeta")
                self.size_format.clear()
                self.size_format.setVisible(False)
                
                # Ocultar el separador si no hay tamaño
                if hasattr(self, 'separator2'):
                    self.separator2.setVisible(False)

    def set_duration_text(self, text: str) -> None:
        """Actualizar/mostrar la duración en la fila de formato y guardarla en los datos."""
        if hasattr(self, 'duration_label') and isinstance(self.duration_label, QLabel):
            if text:
                if text.startswith("• "):
                    self.duration_label.setText(text)
                    plain = text[2:].strip()
                else:
                    self.duration_label.setText(f"• {text}")
                    plain = text.strip()
                self.duration_label.setVisible(True)
                try:
                    if hasattr(self, 'data') and hasattr(self.data, 'duration'):
                        self.data.duration = plain
                except Exception:
                    pass
            else:
                self.duration_label.clear()
                self.duration_label.setVisible(False)
                try:
                    if hasattr(self, 'data') and hasattr(self.data, 'duration'):
                        self.data.duration = ""
                except Exception:
                    pass

    def set_channel_text(self, text: str) -> None:
        """Actualizar/mostrar el canal debajo del título."""
        # Clean the channel name before setting it
        cleaned_text = clean_channel_name(text)
        if hasattr(self, 'channel') and isinstance(self.channel, QLabel):
            if cleaned_text:
                self.channel.setText(cleaned_text)
                self.channel.setVisible(True)
                # Asegurar que el canal tenga la altura correcta
                self.channel.setMinimumHeight(16)
                self.channel.setMaximumHeight(20)
                try:
                    if hasattr(self, 'data') and hasattr(self.data, 'channel'):
                        self.data.channel = cleaned_text
                except Exception:
                    pass
            else:
                self.channel.clear()
                self.channel.setVisible(False)

    def _load_thumbnail(self) -> None:
        """Load thumbnail from URL or use existing pixmap"""
        if hasattr(self.data, 'thumbnail_pixmap') and self.data.thumbnail_pixmap:
            scaled_pixmap = self._scale_thumbnail(self.data.thumbnail_pixmap)
            self.thumb.setPixmap(scaled_pixmap)
            return
        
        if not self.data.thumbnail_url:
            self.thumb.setText("🎬")
            self.thumb.setStyleSheet("color: #6b7280; font-size: 32px;")
            return
        
        self.thumb.setText("⏳")
        self.thumb.setStyleSheet("color: #6b7280; font-size: 28px;")
        threading.Thread(target=self._fetch_and_set_thumbnail, daemon=True).start()
    
    def _scale_thumbnail(self, pixmap: QPixmap) -> QPixmap:
        """Escala la miniatura para llenar el contenedor sin bordes"""
        if pixmap.isNull():
            return pixmap
        
        # Escalar para llenar el contenedor completamente
        scaled_pixmap = pixmap.scaled(
            160,  # Ancho completo del contenedor
            90,   # Alto completo del contenedor
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Si la imagen escalada es más grande que el contenedor, recortar el centro
        if scaled_pixmap.width() > 160 or scaled_pixmap.height() > 90:
            x = (scaled_pixmap.width() - 160) // 2
            y = (scaled_pixmap.height() - 90) // 2
            scaled_pixmap = scaled_pixmap.copy(x, y, 160, 90)
        
        return scaled_pixmap

    def _fetch_and_set_thumbnail(self) -> None:
        """Fetch thumbnail and set it to the label"""
        try:
            import requests
            r = requests.get(self.data.thumbnail_url, timeout=5)
            r.raise_for_status()
            from PyQt6.QtGui import QPixmap
            pix = QPixmap()
            pix.loadFromData(r.content)
            if not pix.isNull():
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(0, lambda: self.thumb.setPixmap(self._scale_thumbnail(pix)))
        except Exception:
            pass

    def _create_svg_icon(self, svg_path: str, size: int = 16, color: str = None):
        """Create a QIcon from an SVG file with optional color override"""
        try:
            from PyQt6.QtSvg import QSvgRenderer
            from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
            from PyQt6.QtCore import Qt
            
            with open(svg_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            
            if color:
                svg_content = svg_content.replace('stroke="#000000"', f'stroke="{color}"')
                svg_content = svg_content.replace('stroke="#ffffff"', f'stroke="{color}"')
                svg_content = svg_content.replace('fill="#000000"', f'fill="{color}"')
                svg_content = svg_content.replace('fill="#ffffff"', f'fill="{color}"')
                svg_content = svg_content.replace('stroke="white"', f'stroke="{color}"')
                svg_content = svg_content.replace('stroke="black"', f'stroke="{color}"')
            
            renderer = QSvgRenderer(svg_content.encode('utf-8'))
            if not renderer.isValid():
                return QIcon()
            
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            
            return QIcon(pixmap)
        except Exception:
            return QIcon()

    def _on_cancel_clicked(self) -> None:
        """Handle cancel button click"""
        if self.worker:
            try:
                self.worker.cancel()
                
                if self.worker.is_alive():
                    self.worker.join(timeout=2.0)
                
                try:
                    self.worker.progressChanged.disconnect()
                except Exception:
                    pass
                try:
                    self.worker.sizeTextChanged.disconnect()
                except Exception:
                    pass
                try:
                    self.worker.downloadStatsChanged.disconnect()
                except Exception:
                    pass
                try:
                    self.worker.finished.disconnect()
                except Exception:
                    pass
                try:
                    self.worker.errorOccurred.disconnect()
                except Exception:
                    pass
                
                if hasattr(self.parent(), 'parent') and self.parent().parent():
                    downloads_page = self.parent().parent()
                    if hasattr(downloads_page, '_workers') and self.worker_url:
                        downloads_page._workers.pop(self.worker_url, None)
                
            except Exception:
                pass
        
        self._cleanup_partial_files_widget()
        
        parent_widget = self.parent()
        if parent_widget:
            list_widget = parent_widget.parent()
            if hasattr(list_widget, 'takeItem'):
                for i in range(list_widget.count()):
                    item = list_widget.item(i)
                    if list_widget.itemWidget(item) == self:
                        list_widget.takeItem(i)
                        break
    
    def _cleanup_partial_files_widget(self) -> None:
        """Limpia archivos .part y .ytdl residuales desde el widget"""
        try:
            import glob
            import os
            
            from PyQt6.QtCore import QSettings
            settings = QSettings("AudioHub", "AudioHubApp")
            download_dir = settings.value("downloadDir", os.path.join(os.path.expanduser("~"), "Downloads"), type=str)
            
            pattern = os.path.join(download_dir, "*.part")
            part_files = glob.glob(pattern)
            
            ytdl_pattern = os.path.join(download_dir, "*.ytdl")
            ytdl_files = glob.glob(ytdl_pattern)
            
            for part_file in part_files:
                try:
                    if os.path.exists(part_file):
                        os.remove(part_file)
                        print(f"Archivo parcial eliminado desde widget: {part_file}")
                except Exception as e:
                    print(f"No se pudo eliminar {part_file}: {e}")
            
            for ytdl_file in ytdl_files:
                try:
                    if os.path.exists(ytdl_file):
                        os.remove(ytdl_file)
                        print(f"Archivo .ytdl eliminado desde widget: {ytdl_file}")
                except Exception as e:
                    print(f"No se pudo eliminar {ytdl_file}: {e}")
                    
        except Exception as e:
            print(f"Error al limpiar archivos residuales desde widget: {e}")


class DownloadsPage(QWidget):
    """Page that lists ongoing downloads with modern cards and progress bars.

    Real download logic can be connected later. For now, a timer simulates
    progress to illustrate the UI and transitions.
    """

    # Signal to inform MainWindow to move items to CompletedPage

    metaTextReady = pyqtSignal(str)
    
    # Signal para ajuste de calidad detectado en segundo plano
    quality_adjustment_detected = pyqtSignal(object, int, int)  # card_widget, selected_res, max_resolution

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("DownloadsPage")
        self._timer: Optional[QBasicTimer] = None
        self._workers: Dict[str, "_DownloadWorker"] = {}
        self._build()
        self.metaTextReady.connect(self._set_meta_text)
        self.quality_adjustment_detected.connect(self._handle_quality_adjustment)
        self._seed_demo()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header / URL form
        header = QLabel("Descargas")
        header.setObjectName("PageTitle")
        layout.addWidget(header)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.input_url = QLineEdit()
        self.input_url.setPlaceholderText("Pega la URL de YouTube…")
        self.input_url.setClearButtonEnabled(True)
        # Búsqueda instantánea con debounce
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.timeout.connect(self._trigger_preview_from_timer)
        self.input_url.textChanged.connect(self._on_url_changed)
        self.input_url.returnPressed.connect(self._on_enter_submit)
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        row.addWidget(self.input_url, 1)
        roww = QWidget(); 
        roww.setLayout(row)
        url_label = QLabel("URL")
        url_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        url_label.setFixedHeight(42)  # Match input height for perfect alignment
        form.addRow(url_label, roww)

        # Destino se configura en la página de Configuración; aquí lo usamos de QSettings
        layout.addLayout(form)

        self.preview_box = QGroupBox("Previsualización")
        pv = QHBoxLayout(self.preview_box)
        self.thumb = QLabel(); self.thumb.setFixedSize(300, 168); self.thumb.setStyleSheet("border-radius:8px;"); self.thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Placeholder text (shown initially)
        self.placeholder_label = QLabel("Pega una URL de YouTube")
        self.placeholder_label.setWordWrap(True)
        self.placeholder_label.setObjectName("PreviewPlaceholder")
        
        # Video title (shown after loading)
        self.title_label = QLabel()
        self.title_label.setWordWrap(True)
        self.title_label.setObjectName("PreviewTitle")
        self.title_label.setVisible(False)
        
        pv.addWidget(self.thumb)
        pv.addSpacing(12)
        # Right area with title on top, and a row: channel (left) + duration (right)
        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(8)
        right.addWidget(self.placeholder_label)
        right.addWidget(self.title_label)
        info_row = QHBoxLayout()
        self.channel_lbl = QLabel("")
        self.channel_lbl.setObjectName("PreviewSub")
        self.duration_lbl = QLabel("")
        self.duration_lbl.setObjectName("PreviewDuration")
        self.duration_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        info_row.addWidget(self.channel_lbl)
        info_row.addStretch(1)
        info_row.addWidget(self.duration_lbl)
        right.addLayout(info_row)
        # format selector + descargar en la misma fila
        self.format_combo = QComboBox()
        self.format_combo.setEnabled(False)
        self.format_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.btn_download = QPushButton("Descargar")
        self.btn_download.setEnabled(False)
        self.btn_download.clicked.connect(self._start_download)
        

        # wrapper visible solo cuando hay preview
        self.controls_wrap = QWidget()
        controls_row = QHBoxLayout(self.controls_wrap)
        controls_row.setContentsMargins(0, 0, 0, 0)
        controls_row.setSpacing(8)
        controls_row.addWidget(self.format_combo)
        controls_row.addStretch(1)
        controls_row.addWidget(self.btn_download)
        self.controls_wrap.setVisible(False)
        right.addWidget(self.controls_wrap)
        wrapper = QWidget(); wrapper.setLayout(right)
        pv.addWidget(wrapper, 1)
        # button moved next to dropdown
        layout.addWidget(self.preview_box)

        title = QLabel("Descargando ahora")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName("CardList")
        layout.addWidget(self.list_widget, 1)

    def _seed_demo(self) -> None:
        # Remove demo timer; real progress handled per download
        pass

    def _add_item(self, data: DownloadItemData) -> None:
        item = QListWidgetItem()
        widget = DownloadItemWidget(data)
        item.setSizeHint(widget.sizeHint())
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, widget)

    # --- URL preview & download logic ---
    def _on_preview(self) -> None:
        url = self.input_url.text().strip()
        if not url:
            self.meta.setText("Introduce una URL válida de YouTube.")
            return
        # Limpiar URL (ignorar playlist para rapidez y consistencia)
        clean_url = self._strip_playlist(url)
        try:
            info = self._fetch_oembed(clean_url)
            if not info:
                raise RuntimeError("No se obtuvo respuesta del oEmbed")
            # thumbnail
            pix = self._fetch_thumbnail(info["thumbnail_url"])
            if pix:
                scaled = pix.scaled(
                    self.thumb.size(),
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.thumb.setPixmap(scaled)
            # Hide placeholder, show title
            self.placeholder_label.setVisible(False)
            self.title_label.setText(info['title'])
            self.title_label.setVisible(True)
            self.channel_lbl.setText(clean_channel_name(info['author_name']))
            self.duration_lbl.setText("...")
            self._last_url = clean_url
            self._last_title = info["title"]
            self._last_thumbnail_url = info.get("thumbnail_url", "")
            self._last_channel = clean_channel_name(info.get('author_name', ''))
            self._last_duration = ""  # Will be set by duration worker
            # Predefined format options (mantener selección actual)
            current_selection = self.format_combo.currentText()
            self._preset_formats()
            # Restaurar selección si existe
            if current_selection:
                index = self.format_combo.findText(current_selection)
                if index >= 0:
                    self.format_combo.setCurrentIndex(index)
            self.controls_wrap.setVisible(True)
            # Habilitar descarga inmediatamente, sin esperar duración
            self.btn_download.setEnabled(True)

            # Augment duration asynchronously con yt-dlp
            threading.Thread(target=self._augment_with_ytdlp, args=(clean_url, None), daemon=True).start()
            # Fallback timeout (6s)
            QTimer.singleShot(6000, self._duration_timeout_check)
        except Exception as e:
            # Show error in placeholder, hide title
            self.placeholder_label.setText(f"No se pudo obtener la info: {e}")
            self.placeholder_label.setVisible(True)
            self.title_label.setVisible(False)
            self.btn_download.setEnabled(False)
            self.controls_wrap.setVisible(False)

    def _fetch_thumbnail(self, url: str) -> Optional[QPixmap]:
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            pix = QPixmap()
            pix.loadFromData(r.content)
            return pix
        except Exception:
            return None

    def _fetch_oembed(self, url: str) -> Optional[dict]:
        endpoint = "https://www.youtube.com/oembed"
        try:
            r = requests.get(endpoint, params={"url": url, "format": "json"}, timeout=10)
            r.raise_for_status()
            return r.json()
        except Exception:
            return None

    def _choose_dir(self) -> None:
        pass

    def _customize_clear_button(self) -> None:
        """Try to customize the clear button with our cancel icon"""
        try:
            # Get the clear button from the line edit
            clear_button = None
            for child in self.input_url.findChildren(QPushButton):
                if hasattr(child, 'clicked'):
                    clear_button = child
                    break
            
            if clear_button:
                # Set our custom icon
                icon = self._create_svg_icon_for_lineedit(get_icon_path("cancel_white.svg"), color="#9ca3af")
                if not icon.isNull():
                    clear_button.setIcon(icon)
        except Exception:
            # If customization fails, the default clear button will still work
            pass

    def _create_svg_icon_for_lineedit(self, svg_path: str, size: int = 16, color: str = None):
        """Create a QIcon from an SVG file with optional color override for line edit"""
        try:
            from PyQt6.QtSvg import QSvgRenderer
            from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
            from PyQt6.QtCore import Qt
            
            # Read and optionally modify SVG content
            with open(svg_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            
            # If color is specified, replace the stroke/fill color
            if color:
                # Replace common color attributes
                svg_content = svg_content.replace('stroke="#000000"', f'stroke="{color}"')
                svg_content = svg_content.replace('stroke="#ffffff"', f'stroke="{color}"')
                svg_content = svg_content.replace('fill="#000000"', f'fill="{color}"')
                svg_content = svg_content.replace('fill="#ffffff"', f'fill="{color}"')
                svg_content = svg_content.replace('stroke="white"', f'stroke="{color}"')
                svg_content = svg_content.replace('stroke="black"', f'stroke="{color}"')
            
            renderer = QSvgRenderer(svg_content.encode('utf-8'))
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

    def _set_meta_text(self, duration_text: str) -> None:
        # Update only the right-aligned duration label
        self.duration_lbl.setText(duration_text or "desconocida")
        # Save duration for download items
        self._last_duration = duration_text or "desconocida"
        # Now that we have duration, enable the download button
        self.btn_download.setEnabled(True)

    def _augment_with_ytdlp(self, url: str, _unused_base: str | None) -> None:
        duration_seconds = 0
        duration_string = None
        self._log_debug("augment_start", f"URL={url}")
        # Try Python API first (does not require yt-dlp in PATH).
        # Avoid android client (may need PO token). Try iOS → web as fallbacks.
        try:
            from yt_dlp import YoutubeDL  # type: ignore
            for client in ("ios", "web"):  # ordered fallbacks
                try:
                    ydl_opts = {
                        "quiet": True,
                        "no_warnings": True,
                        "skip_download": True,
                        "extractor_args": {"youtube": {"player_client": [client]}},
                    }
                    with YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                        duration_seconds = int(info.get("duration", 0) or 0)
                        duration_string = info.get("duration_string")
                        self._log_debug(
                            "yt_dlp_api",
                            f"client={client} duration={duration_seconds} duration_string={duration_string}",
                        )
                        if duration_seconds or duration_string:
                            break
                except Exception:
                    self._log_debug("yt_dlp_api_error", traceback.format_exc())
                    continue
        except Exception:
            self._log_debug("yt_dlp_import_error", traceback.format_exc())

        if not (duration_seconds or duration_string):
            # Fallback to CLI if available (use iOS client)
            try:
                p = subprocess.run(
                    [
                        "yt-dlp",
                        "-J",
                        "--no-warnings",
                        "--extractor-args",
                        "youtube:player_client=ios",
                        url,
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                self._log_debug("yt_dlp_cli_stdout", p.stdout[:2000])
                if p.stderr:
                    self._log_debug("yt_dlp_cli_stderr", p.stderr[:2000])
                data = json.loads(p.stdout)
                duration_seconds = int(data.get("duration", 0) or 0)
                duration_string = data.get("duration_string")
            except Exception:
                self._log_debug("yt_dlp_cli_error", traceback.format_exc())
                duration_seconds = 0
                duration_string = None

        if not duration_string and duration_seconds > 0:
            mins, secs = divmod(duration_seconds, 60)
            duration_string = f"{mins:02d}:{secs:02d}"

        if duration_string:
            self.metaTextReady.emit(duration_string)
            self._log_debug("augment_done", f"OK duration={duration_string}")
        else:
            self.metaTextReady.emit("desconocida")
            self._log_debug("augment_done", "unknown")

    def _duration_timeout_check(self) -> None:
        # If still showing '...', set to desconocida on the duration label
        current = self.duration_lbl.text().strip()
        if current == "..." or not current:
            self.metaTextReady.emit("desconocida")

    def _fetch_duration_for_card(self, url: str, card_widget: 'DownloadItemWidget') -> None:
        """Obtiene la duración (y canal si falta) con yt-dlp y actualiza la tarjeta en vivo."""
        duration_seconds = 0
        duration_string = None
        channel_name = ""
        # Intentar API Python
        try:
            try:
                from yt_dlp import YoutubeDL  # type: ignore
                ydl_opts = {
                    "quiet": True,
                    "no_warnings": True,
                    "skip_download": True,
                    "extractor_args": {"youtube": {"player_client": ["ios", "web"]}},
                }
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    duration_seconds = int(info.get("duration", 0) or 0)
                    duration_string = info.get("duration_string")
                    channel_name = clean_channel_name(info.get("uploader") or info.get("channel") or "")
            except Exception:
                # Fallback CLI
                p = subprocess.run([
                    "yt-dlp", "-J", "--no-warnings",
                    "--extractor-args", "youtube:player_client=ios",
                    url,
                ], capture_output=True, text=True, check=True)
                data = json.loads(p.stdout)
                duration_seconds = int(data.get("duration", 0) or 0)
                duration_string = data.get("duration_string")
                channel_name = clean_channel_name(data.get("uploader") or data.get("channel") or "")
        except Exception:
            duration_seconds = 0
            duration_string = None
            channel_name = ""
        # Formatear duración
        if not duration_string and duration_seconds > 0:
            mins, secs = divmod(duration_seconds, 60)
            duration_string = f"{mins:02d}:{secs:02d}"
        # Actualizar UI en el hilo principal
        from PyQt6.QtCore import QTimer
        if duration_string:
            QTimer.singleShot(0, lambda: card_widget.set_duration_text(duration_string))
        # Si el canal está vacío en la tarjeta y lo obtuvimos, actualizarlo
        try:
            if channel_name and (not getattr(card_widget.data, 'channel', "")):
                QTimer.singleShot(0, lambda: card_widget.set_channel_text(channel_name))
        except Exception:
            pass

    def _log_debug(self, tag: str, text: str) -> None:
        try:
            stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("ytdlp_debug.log", "a", encoding="utf-8") as f:
                f.write(f"[{stamp}] {tag}: {text}\n")
        except Exception:
            pass

    def _strip_playlist(self, url: str) -> str:
        try:
            parsed = urllib.parse.urlparse(url)
            if "youtu.be" in parsed.netloc:
                return url  # short link usually only video id
            q = urllib.parse.parse_qs(parsed.query)
            if "v" in q:
                video_id = q["v"][0]
                return f"https://www.youtube.com/watch?v={video_id}"
        except Exception:
            return url
        return url

    def _preset_formats(self) -> None:
        # Predefined list independent of yt streams. The actual stream chosen
        # will adapt internally (best available <= selected target).
        options = {
            "Video • MP4 • 4K": "video_2160",
            "Video • MP4 • 2K": "video_1440",
            "Video • MP4 • 1080p": "video_1080",
            "Video • MP4 • 720p": "video_720",
            "Video • MP4 • 480p": "video_480",
            "Audio • MP3 • 320 kbps": "mp3_320",
            "Audio • MP3 • 256 kbps": "mp3_256",
            "Audio • MP3 • 192 kbps": "mp3_192",
            "Audio • MP3 • 128 kbps": "mp3_128",
            "Audio • MP3 • 96 kbps": "mp3_96",
            "Audio • MP3 • 64 kbps": "mp3_64",
            "Audio • M4A • 320 kbps": "m4a_320",
            "Audio • M4A • 192 kbps": "m4a_best",
            "Audio • OGG • 320 kbps": "ogg_320",
            "Audio • OGG • 192 kbps": "ogg_best",
            "Audio • WMA • 320 kbps": "wma_320",
            "Audio • WMA • 192 kbps": "wma_best",
        }
        self._preset_map = options
        self.format_combo.clear()
        self.format_combo.addItems(list(options.keys()))
        
        # Cargar la última selección guardada
        from PyQt6.QtCore import QSettings
        settings = QSettings()
        last_format = settings.value("last_format_selection", "Video • MP4 • 1080p")
        
        # Buscar y seleccionar el último formato
        index = self.format_combo.findText(last_format)
        if index >= 0:
            self.format_combo.setCurrentIndex(index)
        
        # Conectar el signal DESPUÉS de cargar la selección para evitar guardado innecesario
        # Solo conectar si no está ya conectado
        try:
            self.format_combo.currentTextChanged.disconnect(self._on_format_changed)
        except TypeError:
            pass  # No estaba conectado
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        
        self.format_combo.setEnabled(True)

    def _on_format_changed(self, format_text: str) -> None:
        """Guardar la selección de formato cuando cambia y re-habilitar el botón descargar."""
        if format_text:  # Solo guardar si no está vacío
            from PyQt6.QtCore import QSettings
            settings = QSettings()
            settings.setValue("last_format_selection", format_text)
            settings.sync()  # Forzar escritura inmediata
        # Si el panel de controles está visible (hay preview), habilitar descargar
        try:
            if hasattr(self, 'controls_wrap') and self.controls_wrap.isVisible():
                self.btn_download.setEnabled(True)
        except Exception:
            pass

    # --- Debounce & auto-preview helpers ---
    def _on_url_changed(self, text: str) -> None:
        # Si detectamos enlace de YouTube, lanzamos preview tras 500 ms
        self._last_typed = text.strip()
        self._preview_timer.start(500)

    def _is_youtube_url(self, text: str) -> bool:
        t = text.lower()
        return ("youtube.com/watch" in t) or ("youtu.be/" in t)

    def _trigger_preview_from_timer(self) -> None:
        text = getattr(self, "_last_typed", "").strip()
        if self._is_youtube_url(text):
            # Evitar repetir misma URL consecutivamente
            if text and text != getattr(self, "_last_url", ""):
                self.input_url.blockSignals(True)
                try:
                    self.input_url.setText(text)
                finally:
                    self.input_url.blockSignals(False)
                self._on_preview()

    def _on_enter_submit(self) -> None:
        # Enter: ejecuta preview inmediata y, si es válida, inicia descarga
        self._preview_timer.stop()
        self._on_preview()
        if self.btn_download.isEnabled() and self.controls_wrap.isVisible():
            self._start_download()

    def _start_download(self) -> None:
        if not hasattr(self, "_last_url"):
            print("DEBUG: No hay URL para descargar")
            return
        url: str = self._last_url  # type: ignore[attr-defined]
        title: str = getattr(self, "_last_title", "Descarga")
        
        print(f"DEBUG: Iniciando descarga de: {url}")
        print(f"DEBUG: Título: {title}")
        
        # Get duration and channel from preview
        duration = getattr(self, "_last_duration", "")
        channel = getattr(self, "_last_channel", "")
        
        print(f"DEBUG: Canal: {channel}")
        
        # Create list item UI for progress with thumbnail
        thumbnail_pixmap = None
        if hasattr(self, 'thumb') and self.thumb.pixmap():
            thumbnail_pixmap = self.thumb.pixmap()
        
        # Get format info from dropdown selection
        format_info = self.format_combo.currentText()
        print(f"DEBUG: Formato seleccionado: {format_info}")
        
        card = DownloadItemData(title, "", "", 0, "", duration, channel, format_info)
        card.thumbnail_pixmap = thumbnail_pixmap
        self._add_item(card)
        row_index = self.list_widget.count() - 1
        card_widget = self.list_widget.itemWidget(self.list_widget.item(row_index))
        assert isinstance(card_widget, DownloadItemWidget)

        # Worker
        selected_label = self.format_combo.currentText()
        mode = getattr(self, "_preset_map", {}).get(selected_label, "video_best")
        print(f"DEBUG: Modo de descarga: {mode}")
        
        s = QSettings("AudioHub", "AudioHubApp")
        out_dir = s.value("downloadDir", os.path.join(os.path.expanduser("~"), "Downloads"), type=str)
        no_playlist_val = s.value("noPlaylist", True)
        no_playlist = True
        if isinstance(no_playlist_val, str):
            no_playlist = no_playlist_val.lower() in ("1", "true", "yes", "on")
        elif isinstance(no_playlist_val, (int, bool)):
            no_playlist = bool(no_playlist_val)

        print(f"DEBUG: Directorio de salida: {out_dir}")
        print(f"DEBUG: No playlist: {no_playlist}")

        # Verificar si el archivo ya existe antes de iniciar la descarga
        if self._check_file_exists_and_handle_duplicate(url, out_dir, mode, no_playlist, card_widget):
            print("DEBUG: Descarga iniciada correctamente")
        else:
            print("DEBUG: Descarga cancelada por el usuario o archivo duplicado")

    def _on_finished(self, title: str, path: str, card_widget: DownloadItemWidget) -> None:
        # Actualizar progreso a 100%
        self._update_progress(card_widget, 100)
        
        # Gather all the data from the widget
        data = card_widget.data
        # Use the actual video title from the widget, not the parameter which might be URL
        actual_title = data.title if data.title else title
        channel = data.channel if data.channel else ""
        duration = data.duration if data.duration else ""
        format_info = data.format_info if hasattr(data, 'format_info') and data.format_info else ""
        
        # Get file size if possible
        file_size = ""
        try:
            import os
            if path and os.path.exists(path) and os.path.isfile(path):
                size_bytes = os.path.getsize(path)
                print(f"DEBUG: Tamaño del archivo final: {size_bytes} bytes")
                if size_bytes >= 1024 * 1024:  # MB
                    file_size = f"{size_bytes / (1024 * 1024):.1f} MB"
                elif size_bytes >= 1024:  # KB
                    file_size = f"{size_bytes / 1024:.1f} KB"
                else:
                    file_size = f"{size_bytes} bytes"
                print(f"DEBUG: Tamaño formateado: {file_size}")
            else:
                print(f"DEBUG: Archivo no encontrado o no es un archivo: {path}")
        except Exception as e:
            print(f"DEBUG: Error al obtener tamaño del archivo: {e}")
            file_size = "Desconocido"
        
        # Mostrar en la UI final: solo "Completado"
        try:
            if file_size:
                print(f"DEBUG: Marcando descarga como completada con tamaño: {file_size}")
                card_widget.speed.setText("Completado")
                card_widget.speed.setObjectName("CompletedLabel")  # Estilo verde para completado
                
                # Actualizar el tamaño del archivo con el tamaño real del archivo descargado
                # Esto asegura que se muestre el tamaño correcto del archivo final
                print(f"DEBUG: Llamando a set_size_text con: {file_size}")
                card_widget.set_size_text(file_size)
                
                # También actualizar los datos del widget para mantener consistencia
                if hasattr(card_widget, 'data') and hasattr(card_widget.data, 'size_text'):
                    card_widget.data.size_text = file_size
                    print(f"DEBUG: Tamaño guardado en data: {card_widget.data.size_text}")
        except Exception as e:
            print(f"DEBUG: Error al marcar como completado: {e}")
            pass
        
        # Get thumbnail pixmap
        thumbnail_pixmap = None
        if hasattr(data, 'thumbnail_pixmap') and data.thumbnail_pixmap:
            thumbnail_pixmap = data.thumbnail_pixmap
        elif card_widget.thumb.pixmap():
            thumbnail_pixmap = card_widget.thumb.pixmap()
        
        # Verificar si la calidad descargada es diferente a la seleccionada
        self._check_and_update_actual_quality(card_widget, path, format_info)
        
        # ALERTAS DE DESCARGA COMPLETADA (ahora incluye acciones para abrir carpeta)
        self._show_download_notification(actual_title, file_size, path, channel, duration, format_info, thumbnail_pixmap)
        
        # Emit all the data for completed page
        # Download completed - no longer sending to completed page
    def _show_download_notification(self, title: str, file_size: str, path: str, channel: str = "", duration: str = "", format_info: str = "", thumbnail_pixmap: Optional[QPixmap] = None) -> None:
        """Mostrar notificación cuando la descarga esté completa"""
        # Notificación del sistema (Windows)
        self._show_system_notification(title, file_size)
        
        # Sonido de notificación (opcional)
        self._play_notification_sound()
        
        # Alerta visual opcional (mensaje emergente con acciones)
        self._show_visual_alert(title, file_size, path, channel, duration, format_info, thumbnail_pixmap)
    
    def _show_system_notification(self, title: str, file_size: str) -> None:
        """Mostrar notificación del sistema Windows"""
        try:
            if os.name == 'nt':  # Windows
                # Usar plyer para notificaciones multiplataforma
                try:
                    from plyer import notification
                    notification.notify(
                        title="Descarga Completada - Audio Hub",
                        message=f"{title}\n{file_size}",
                        app_name="Audio Hub",
                        timeout=5  # 5 segundos
                    )
                except ImportError:
                    # Fallback usando toast notifications de Windows 10/11
                    try:
                        from win10toast import ToastNotifier
                        toaster = ToastNotifier()
                        toaster.show_toast(
                            "Audio Hub - Descarga Completada",
                            f"{title}\n{file_size}",
                            duration=5,
                            threaded=True
                        )
                    except ImportError:
                        # Último fallback: usar subprocess para mostrar notificación
                        subprocess.run([
                            'powershell', '-Command',
                            f'''Add-Type -AssemblyName System.Windows.Forms;
                            $balloon = New-Object System.Windows.Forms.NotifyIcon;
                            $balloon.Icon = [System.Drawing.SystemIcons]::Information;
                            $balloon.BalloonTipIcon = [System.Windows.Forms.ToolTipIcon]::Info;
                            $balloon.BalloonTipText = "{title}\n{file_size}";
                            $balloon.BalloonTipTitle = "Audio Hub - Descarga Completada";
                            $balloon.Visible = $true;
                            $balloon.ShowBalloonTip(5000);
                            Start-Sleep -Seconds 5;
                            $balloon.Dispose()'''
                        ], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                        
        except Exception as e:
            print(f"Error al mostrar notificación del sistema: {e}")
    def _play_notification_sound(self) -> None:
        """Reproducir sonido de notificación"""
        # Verificar si el sonido está habilitado en configuraciones
        settings = QSettings("AudioHub", "AudioHubApp")
        play_sound = settings.value("playSoundAlerts", True, type=bool)
        
        if not play_sound:
            return
            
        try:
            # Sonido del sistema de Windows
            if os.name == 'nt':
                import winsound
                winsound.MessageBeep(winsound.MB_ICONINFORMATION)
        except Exception:
            # Si falla el sonido, no es crítico
            pass
            pass
    def _show_visual_alert(self, title: str, file_size: str, path: str, channel: str = "", duration: str = "", format_info: str = "", thumbnail_pixmap: Optional[QPixmap] = None) -> None:
        """Mostrar alerta visual en la aplicación con acciones"""
        # Verificar configuración de alertas visuales (opcional)
        settings = QSettings("AudioHub", "AudioHubApp")
        show_visual_alerts = settings.value("showVisualAlerts", True, type=bool)
        
        if not show_visual_alerts:
            return
        
        # Crear mensaje box no-modal para no interrumpir el flujo
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Descarga Completada")
        
        # Usar thumbnail como ícono si está disponible
        try:
            if thumbnail_pixmap and not thumbnail_pixmap.isNull():
                scaled = thumbnail_pixmap.scaled(96, 54, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                msg.setIconPixmap(scaled)
        except Exception:
            pass
        
        # Título estilizado
        primary = f"<b>¡Descarga completada!</b><br/><span style='color:#d1d5db'>{title}</span>"
        msg.setText(primary)
        
        # Info secundaria: formato y tamaño del archivo
        rows = []
        if format_info:
            rows.append(f"Formato: <b>{format_info}</b>")
        if file_size:
            rows.append(f"Tamaño: <b>{file_size}</b>")
        
        if rows:
            msg.setInformativeText(" • ".join(rows))  # Separar con puntos para una sola línea
        else:
            msg.setInformativeText("")
        
        # Estilo visual del mensaje (oscuro, bordes redondeados)
        msg.setStyleSheet(
            """
            QMessageBox {
                background-color: #111827; /* gray-900 */
            }
            QMessageBox QLabel {
                color: #e5e7eb; /* gray-200 */
                font-size: 13px;
            }
            QMessageBox QPushButton {
                background-color: #1f2937; /* gray-800 */
                color: #e5e7eb;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 6px 10px;
            }
            QMessageBox QPushButton:hover {
                background-color: #374151;
            }
            QMessageBox QPushButton:pressed {
                background-color: #4b5563;
            }
            """
        )
        
        # Botón de abrir carpeta a la izquierda y botón Cerrar a la derecha
        open_btn = msg.addButton("Abrir carpeta", QMessageBox.ButtonRole.ActionRole)
        msg.addButton("Cerrar", QMessageBox.ButtonRole.AcceptRole)

        def on_click(btn):
            if btn is open_btn:
                self._open_folder(path)
        
        msg.buttonClicked.connect(on_click)
        
        # Auto-cerrar después de 6 segundos si el usuario no interactúa
        QTimer.singleShot(6000, lambda: msg.close() if msg.isVisible() else None)
        msg.show()
    
    def _check_file_exists_and_handle_duplicate(self, url: str, output_dir: str, mode: str, no_playlist: bool, card_widget: DownloadItemWidget) -> bool:
        """Verifica si el archivo ya existe y maneja la situación de duplicados"""
        try:
            # Obtener el título del video para construir el nombre del archivo
            title = card_widget.data.title if hasattr(card_widget, 'data') else "video"
            
            # Determinar la extensión basada en el modo
            extension = self._get_extension_from_mode(mode)
            
            # Construir el nombre del archivo completo
            filename = f"{title}.{extension}"
            filepath = os.path.join(output_dir, filename)
            
            # Verificar si el archivo ya existe
            if os.path.exists(filepath):
                print(f"DEBUG: Archivo duplicado detectado: {filepath}")
                
                # Preguntar al usuario qué hacer
                choice = self._show_duplicate_file_dialog(filename)
                
                if choice == "overwrite":
                    print("DEBUG: Usuario eligió sobrescribir el archivo")
                    # Eliminar el archivo existente
                    try:
                        os.remove(filepath)
                        print(f"DEBUG: Archivo existente eliminado: {filepath}")
                    except Exception as e:
                        print(f"DEBUG: Error al eliminar archivo existente: {e}")
                        # Continuar con la descarga (yt-dlp manejará el conflicto)
                    
                    # Continuar con la descarga
                    self._check_available_formats_and_start(url, output_dir, mode, no_playlist, card_widget)
                    return True
                    
                elif choice == "rename":
                    print("DEBUG: Usuario eligió renombrar el archivo")
                    # Generar un nombre único
                    new_filename = self._generate_unique_filename(output_dir, title, extension)
                    new_filepath = os.path.join(output_dir, new_filename)
                    print(f"DEBUG: Nuevo nombre de archivo: {new_filename}")
                    
                    # Actualizar la card para mostrar el nuevo nombre
                    if hasattr(card_widget, 'data'):
                        card_widget.data.title = os.path.splitext(new_filename)[0]
                        card_widget.title.setText(os.path.splitext(new_filename)[0])
                    
                    # Continuar con la descarga usando el nuevo nombre
                    self._check_available_formats_and_start(url, output_dir, mode, no_playlist, card_widget)
                    return True
                    
                elif choice == "cancel":
                    print("DEBUG: Usuario canceló la descarga")
                    # Eliminar la card de la lista
                    self._remove_download_card(card_widget)
                    return False
                    
                else:
                    print("DEBUG: Opción no válida, cancelando descarga")
                    self._remove_download_card(card_widget)
                    return False
            else:
                # No hay archivo duplicado, continuar normalmente
                print(f"DEBUG: No hay archivo duplicado, continuando con descarga")
                self._check_available_formats_and_start(url, output_dir, mode, no_playlist, card_widget)
                return True
                
        except Exception as e:
            print(f"DEBUG: Error al verificar archivo duplicado: {e}")
            # En caso de error, continuar con la descarga
            self._check_available_formats_and_start(url, output_dir, mode, no_playlist, card_widget)
            return True
    
    def _get_extension_from_mode(self, mode: str) -> str:
        """Determina la extensión del archivo basada en el modo de descarga"""
        if mode.startswith("mp3_"):
            return "mp3"
        elif mode.startswith("m4a_"):
            return "m4a"
        elif mode.startswith("ogg_"):
            return "ogg"
        elif mode.startswith("wma_"):
            return "wma"
        elif mode.startswith("video_"):
            return "mp4"
        else:
            return "mp4"  # Por defecto
    
    def _show_duplicate_file_dialog(self, filename: str) -> str:
        """Muestra un diálogo para manejar archivos duplicados"""
        try:
            msg = QMessageBox(self)
            msg.setWindowTitle("Archivo Duplicado")
            msg.setText(f"El archivo '{filename}' ya existe en el directorio de descarga.")
            msg.setInformativeText("¿Qué deseas hacer?")
            msg.setIcon(QMessageBox.Icon.Question)
            
            # Botones personalizados
            overwrite_btn = msg.addButton("Sobrescribir", QMessageBox.ButtonRole.AcceptRole)
            rename_btn = msg.addButton("Renombrar", QMessageBox.ButtonRole.AcceptRole)
            cancel_btn = msg.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
            
            # Estilo del mensaje
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #111827;
                }
                QMessageBox QLabel {
                    color: #e5e7eb;
                    font-size: 13px;
                }
                QMessageBox QPushButton {
                    background-color: #1f2937;
                    color: #e5e7eb;
                    border: 1px solid #374151;
                    border-radius: 6px;
                    padding: 6px 10px;
                    min-width: 80px;
                }
                QMessageBox QPushButton:hover {
                    background-color: #374151;
                }
            """)
            
            # Mostrar el diálogo y obtener la respuesta
            msg.exec()
            
            clicked_button = msg.clickedButton()
            
            if clicked_button == overwrite_btn:
                return "overwrite"
            elif clicked_button == rename_btn:
                return "rename"
            elif clicked_button == cancel_btn:
                return "cancel"
            else:
                return "cancel"  # Por defecto
                
        except Exception as e:
            print(f"DEBUG: Error al mostrar diálogo de archivo duplicado: {e}")
            return "cancel"
    
    def _generate_unique_filename(self, out_dir: str, title: str, extension: str) -> str:
        """Genera un nombre de archivo único agregando un número"""
        base_name = title
        counter = 1
        
        while True:
            filename = f"{base_name} ({counter}).{extension}"
            filepath = os.path.join(out_dir, filename)
            
            if not os.path.exists(filepath):
                return filename
            
            counter += 1
            
            # Prevenir bucles infinitos
            if counter > 999:
                # Usar timestamp como fallback
                import time
                timestamp = int(time.time())
                return f"{base_name}_{timestamp}.{extension}"
    
    def _remove_download_card(self, card_widget: DownloadItemWidget) -> None:
        """Elimina una card de descarga de la lista"""
        try:
            # Encontrar el índice de la card en la lista
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                if self.list_widget.itemWidget(item) == card_widget:
                    # Eliminar el item de la lista
                    self.list_widget.takeItem(i)
                    print(f"DEBUG: Card de descarga eliminada del índice {i}")
                    break
        except Exception as e:
            print(f"DEBUG: Error al eliminar card de descarga: {e}")
    
    def _check_available_formats_and_start(self, url: str, output_dir: str, mode: str, no_playlist: bool, card_widget: DownloadItemWidget) -> None:
        """Verifica los formatos disponibles y ajusta la calidad automáticamente"""
        print(f"DEBUG: Verificando formatos disponibles para: {url}")
        
        # Solo verificar para formatos de video, no para audio
        if not mode.startswith("video_"):
            print(f"DEBUG: Formato de audio detectado, iniciando descarga directa")
            self._start_download_worker(url, output_dir, mode, no_playlist, card_widget)
            return
        
        # Opción para saltar la verificación de formatos si está habilitada
        settings = QSettings("AudioHub", "AudioHubApp")
        skip_format_check = settings.value("skipFormatCheck", False, type=bool)
        
        if skip_format_check:
            print(f"DEBUG: Verificación de formatos deshabilitada, iniciando descarga directa")
            self._start_download_worker(url, output_dir, mode, no_playlist, card_widget)
            return
        
        # Opción para verificación en segundo plano
        background_check = settings.value("backgroundFormatCheck", True, type=bool)
        
        if background_check:
            print(f"DEBUG: Verificación de formatos en segundo plano")
            # Iniciar descarga inmediatamente y verificar formatos en paralelo
            self._start_download_worker(url, output_dir, mode, no_playlist, card_widget)
            
            # Verificar formatos en segundo plano
            threading.Thread(target=self._background_format_check, args=(url, output_dir, mode, no_playlist, card_widget), daemon=True).start()
            return
        
        # Ejecutar yt-dlp --list-formats para obtener formatos disponibles con timeout reducido
        try:
            args = [
                "yt-dlp",
                "--list-formats",
                "--no-playlist" if no_playlist else "",
                url
            ]
            # Filtrar argumentos vacíos
            args = [arg for arg in args if arg]
            
            print(f"DEBUG: Comando para listar formatos: {' '.join(args)}")
            
            # Reducir timeout a 10 segundos para no trabar la aplicación
            result = subprocess.run(args, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                formats_output = result.stdout
                print(f"DEBUG: Formatos disponibles obtenidos exitosamente")
                
                # Analizar la salida para encontrar la resolución máxima disponible
                max_resolution = self._parse_max_resolution(formats_output, mode)
                
                if max_resolution:
                    print(f"DEBUG: Resolución máxima disponible: {max_resolution}")
                    
                    # Si la calidad seleccionada es mayor a la disponible, mostrar aviso
                    selected_res = self._extract_resolution_from_mode(mode)
                    if selected_res and max_resolution < selected_res:
                        # Ajustar el modo a la calidad máxima disponible
                        adjusted_mode = f"video_{max_resolution}"
                        print(f"DEBUG: Ajustando modo de {mode} a {adjusted_mode}")
                        
                        # Actualizar el texto del formato en la card
                        self._update_format_info_for_quality(card_widget, max_resolution)
                        
                        # Iniciar descarga con calidad ajustada
                        self._start_download_worker(url, output_dir, adjusted_mode, no_playlist, card_widget)
                    else:
                        # Calidad disponible, iniciar descarga normal
                        self._start_download_worker(url, output_dir, mode, no_playlist, card_widget)
                else:
                    print(f"DEBUG: No se pudo determinar resolución máxima, usando modo original")
                    self._start_download_worker(url, output_dir, mode, no_playlist, card_widget)
            else:
                print(f"DEBUG: Error al obtener formatos: {result.stderr}")
                # Fallback: iniciar descarga con modo original
                self._start_download_worker(url, output_dir, mode, no_playlist, card_widget)
                
        except subprocess.TimeoutExpired:
            print(f"DEBUG: Timeout al obtener formatos (10s), usando modo original")
            # Fallback: iniciar descarga con modo original sin bloquear
            self._start_download_worker(url, output_dir, mode, no_playlist, card_widget)
        except Exception as e:
            print(f"DEBUG: Error inesperado al verificar formatos: {e}")
            # Fallback: iniciar descarga con modo original
            self._start_download_worker(url, output_dir, mode, no_playlist, card_widget)
    
    def _background_format_check(self, url: str, output_dir: str, mode: str, no_playlist: bool, card_widget: DownloadItemWidget) -> None:
        """Verifica formatos en segundo plano sin bloquear la UI"""
        try:
            print(f"DEBUG: Verificación de formatos en segundo plano para: {url}")
            
            # Solo verificar para formatos de video
            if not mode.startswith("video_"):
                print(f"DEBUG: Formato de audio detectado, saltando verificación")
                return
            
            # Ejecutar yt-dlp --list-formats con timeout reducido
            args = [
                "yt-dlp",
                "--list-formats",
                "--no-playlist" if no_playlist else "",
                url
            ]
            args = [arg for arg in args if arg]
            
            result = subprocess.run(args, capture_output=True, text=True, timeout=8)
            
            if result.returncode == 0:
                formats_output = result.stdout
                max_resolution = self._parse_max_resolution(formats_output, mode)
                
                if max_resolution:
                    selected_res = self._extract_resolution_from_mode(mode)
                    if selected_res and max_resolution < selected_res:
                        print(f"DEBUG: Calidad ajustada en segundo plano: {selected_res}p → {max_resolution}p")
                        print(f"DEBUG: Card widget: {card_widget}")
                        print(f"DEBUG: Card tiene format_label: {hasattr(card_widget, 'format_label')}")
                        print(f"DEBUG: Card tiene quality_adjustment_label: {hasattr(card_widget, 'quality_adjustment_label')}")
                        
                        # Actualizar la UI en el hilo principal de forma inmediata
                        from PyQt6.QtCore import QTimer, QMetaObject
                        from PyQt6.QtCore import Qt
                        from PyQt6.QtCore import Q_ARG
                        
                        # Usar señales de Qt para ejecutar en el hilo principal de forma segura
                        # Emitir señal personalizada que se ejecute en el hilo principal
                        try:
                            # Crear una señal personalizada para actualizar la UI
                            from PyQt6.QtCore import pyqtSignal, QObject
                            
                            # Emitir señal que se ejecute en el hilo principal
                            self.quality_adjustment_detected.emit(card_widget, selected_res, max_resolution)
                            print(f"DEBUG: Señal de ajuste de calidad emitida")
                            
                        except Exception as e:
                            print(f"DEBUG: Error al emitir señal: {e}")
                            # Fallback: intentar actualizar directamente (puede fallar en hilo secundario)
                            try:
                                print(f"DEBUG: Intentando actualización directa como fallback")
                                self._update_format_info_for_quality(card_widget, max_resolution)
                            except Exception as fallback_error:
                                print(f"DEBUG: Fallback también falló: {fallback_error}")
                        
                        # Agregar una verificación inmediata para debug
                        print(f"DEBUG: Verificando que la card tenga los atributos necesarios:")
                        print(f"DEBUG: - format_label: {hasattr(card_widget, 'format_label')}")
                        print(f"DEBUG: - quality_adjustment_label: {hasattr(card_widget, 'quality_adjustment_label')}")
                        print(f"DEBUG: - data: {hasattr(card_widget, 'data')}")
                        if hasattr(card_widget, 'data'):
                            print(f"DEBUG: - format_info: {hasattr(card_widget.data, 'format_info')}")
                            if hasattr(card_widget.data, 'format_info'):
                                print(f"DEBUG: - valor actual: {card_widget.data.format_info}")
                        
        except subprocess.TimeoutExpired:
            print(f"DEBUG: Timeout en verificación en segundo plano")
        except Exception as e:
            print(f"DEBUG: Error en verificación en segundo plano: {e}")
    
    def _update_worker_mode(self, card_widget: DownloadItemWidget, max_resolution: int) -> None:
        """Actualiza el modo del worker si es posible para usar la calidad máxima disponible"""
        try:
            print(f"DEBUG: _update_worker_mode llamado con resolución: {max_resolution}")
            print(f"DEBUG: Card widget: {card_widget}")
            print(f"DEBUG: Card tiene worker: {hasattr(card_widget, 'worker')}")
            print(f"DEBUG: Worker existe: {card_widget.worker if hasattr(card_widget, 'worker') else None}")
            
            if hasattr(card_widget, 'worker') and card_widget.worker:
                # Crear nuevo modo con la resolución máxima disponible
                new_mode = f"video_{max_resolution}"
                print(f"DEBUG: Actualizando modo del worker a: {new_mode}")
                
                # Actualizar el modo del worker
                card_widget.worker._mode = new_mode
                
                # También actualizar el modo en los datos de la card
                if hasattr(card_widget, 'data') and hasattr(card_widget.data, 'format_info'):
                    # Extraer la resolución actual del formato
                    current_format = card_widget.data.format_info
                    if "•" in current_format:
                        parts = current_format.split("•")
                        if len(parts) >= 3:
                            # Reemplazar la resolución
                            parts[2] = f" {max_resolution}p"
                            new_format = "•".join(parts)
                            card_widget.data.format_info = new_format
                            print(f"DEBUG: Formato del worker actualizado: {new_format}")
                            
                            # Actualizar también el label de formato si existe
                            if hasattr(card_widget, 'format_label'):
                                card_widget.format_label.setText(new_format)
                                card_widget.format_label.repaint()
                                print(f"DEBUG: Label de formato actualizado desde worker: {new_format}")
                
        except Exception as e:
            print(f"DEBUG: Error al actualizar modo del worker: {e}")
    
    def _highlight_quality_change(self, card_widget: DownloadItemWidget, new_resolution: int) -> None:
        """Agrega un efecto visual temporal para destacar el cambio de calidad"""
        try:
            print(f"DEBUG: _highlight_quality_change llamado con resolución: {new_resolution}")
            print(f"DEBUG: Card widget: {card_widget}")
            print(f"DEBUG: Card tiene format_label: {hasattr(card_widget, 'format_label')}")
            
            # Cambiar temporalmente el color de fondo del label de formato
            if hasattr(card_widget, 'format_label'):
                original_style = card_widget.format_label.styleSheet()
                
                # Aplicar estilo destacado
                card_widget.format_label.setStyleSheet("""
                    QLabel {
                        background-color: rgba(34, 197, 94, 0.2);
                        border: 2px solid rgba(34, 197, 94, 0.6);
                        border-radius: 4px;
                        padding: 2px 6px;
                        color: #22c55e;
                        font-weight: bold;
                    }
                """)
                
                # Restaurar estilo original después de 2 segundos
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(2000, lambda: card_widget.format_label.setStyleSheet(original_style))
                
                print(f"DEBUG: Efecto visual aplicado para cambio de calidad a {new_resolution}p")
                
        except Exception as e:
            print(f"DEBUG: Error al aplicar efecto visual: {e}")
    
    def _handle_quality_adjustment(self, card_widget: DownloadItemWidget, selected_res: int, max_resolution: int) -> None:
        """Maneja el ajuste de calidad detectado en segundo plano desde el hilo principal"""
        try:
            print(f"DEBUG: _handle_quality_adjustment ejecutándose en hilo principal")
            print(f"DEBUG: Ajustando calidad de {selected_res}p a {max_resolution}p")
            
            # Actualizar el formato en la card
            self._update_format_info_for_quality(card_widget, max_resolution)
            
            
            
            # Actualizar el modo del worker
            self._update_worker_mode(card_widget, max_resolution)
            
            # Aplicar efecto visual
            self._highlight_quality_change(card_widget, max_resolution)
            
            print(f"DEBUG: Ajuste de calidad completado exitosamente")
            
        except Exception as e:
            print(f"DEBUG: Error en _handle_quality_adjustment: {e}")
    
    def _parse_max_resolution(self, formats_output: str, mode: str) -> Optional[int]:
        """Extrae la resolución máxima disponible del output de yt-dlp"""
        try:
            max_res = 0
            lines = formats_output.split('\n')
            
            for line in lines:
                # Buscar líneas que contengan resolución (ej: 1920x1080, 1080p, etc.)
                if 'x' in line and any(char.isdigit() for char in line):
                    # Extraer números de resolución
                    parts = line.split()
                    for part in parts:
                        if 'x' in part and part.count('x') == 1:
                            try:
                                width, height = part.split('x')
                                if width.isdigit() and height.isdigit():
                                    res = int(height)  # Usar altura como resolución
                                    if res > max_res:
                                        max_res = res
                            except ValueError:
                                continue
                        elif part.endswith('p') and part[:-1].isdigit():
                            # Formato como "1080p"
                            try:
                                res = int(part[:-1])
                                if res > max_res:
                                    max_res = res
                            except ValueError:
                                continue
            
            return max_res if max_res > 0 else None
            
        except Exception as e:
            print(f"DEBUG: Error al parsear resolución: {e}")
            return None
    
    def _extract_resolution_from_mode(self, mode: str) -> Optional[int]:
        """Extrae la resolución del modo de descarga"""
        try:
            if mode.startswith("video_"):
                res_str = mode.split("_")[1]
                if res_str.isdigit():
                    return int(res_str)
        except Exception:
            pass
        return None
    
    def _update_format_info_for_quality(self, card_widget: DownloadItemWidget, max_resolution: int) -> None:
        """Actualiza la información del formato en la card para mostrar la calidad real"""
        try:
            print(f"DEBUG: _update_format_info_for_quality llamado con resolución: {max_resolution}")
            print(f"DEBUG: Card widget: {card_widget}")
            print(f"DEBUG: Card tiene data: {hasattr(card_widget, 'data')}")
            print(f"DEBUG: Card tiene format_info: {hasattr(card_widget.data, 'format_info') if hasattr(card_widget, 'data') else False}")
            
            if hasattr(card_widget, 'data') and hasattr(card_widget.data, 'format_info'):
                # Actualizar el formato en los datos
                original_format = card_widget.data.format_info
                print(f"DEBUG: Formato original: {original_format}")
                
                # Crear nuevo formato con la resolución ajustada
                if "•" in original_format:
                    parts = original_format.split("•")
                    if len(parts) >= 3:
                        # Reemplazar la resolución con el texto de ajuste
                        parts[2] = f" Ajustado a máxima calidad ({max_resolution}p)"
                        new_format = "•".join(parts)
                        card_widget.data.format_info = new_format
                        
                        # Actualizar también el label de formato si existe
                        if hasattr(card_widget, 'format_label'):
                            card_widget.format_label.setText(new_format)
                            # Forzar la actualización inmediata de la UI
                            card_widget.format_label.repaint()
                            print(f"DEBUG: Label de formato actualizado en UI: {new_format}")
                        
                        print(f"DEBUG: Formato actualizado: {original_format} → {new_format}")
                        
                        # También actualizar el modo del worker si es posible
                        if hasattr(card_widget, 'worker') and card_widget.worker:
                            new_mode = f"video_{max_resolution}"
                            card_widget.worker._mode = new_mode
                            print(f"DEBUG: Modo del worker actualizado a: {new_mode}")
                        
                        # Forzar la actualización completa de la card
                        card_widget.update()
                        print(f"DEBUG: Card actualizada completamente")
                else:
                    # Si no hay separadores, crear un formato básico
                    new_format = f"Video • MP4 • Ajustado a máxima calidad ({max_resolution}p)"
                    card_widget.data.format_info = new_format
                    
                    # Actualizar también el label de formato si existe
                    if hasattr(card_widget, 'format_label'):
                        card_widget.format_label.setText(new_format)
                        # Forzar la actualización inmediata de la UI
                        card_widget.format_label.repaint()
                        print(f"DEBUG: Label de formato actualizado en UI: {new_format}")
                    
                    print(f"DEBUG: Formato creado: {new_format}")
                    
                    # También actualizar el modo del worker si es posible
                    if hasattr(card_widget, 'worker') and card_widget.worker:
                        new_mode = f"video_{max_resolution}"
                        card_widget.worker._mode = new_mode
                        print(f"DEBUG: Modo del worker actualizado a: {new_mode}")
                    
                    # Forzar la actualización completa de la card
                    card_widget.update()
                    print(f"DEBUG: Card actualizada completamente")
        except Exception as e:
            print(f"DEBUG: Error al actualizar formato: {e}")
            import traceback
            traceback.print_exc()
    
    def _check_and_update_actual_quality(self, card_widget: DownloadItemWidget, file_path: str, original_format: str) -> None:
        """Verifica la calidad real del archivo descargado y actualiza la card si es necesario"""
        try:
            if not file_path or not os.path.exists(file_path):
                print(f"DEBUG: No se puede verificar calidad - archivo no encontrado: {file_path}")
                return
            
            # Solo verificar para archivos de video
            if not original_format or not original_format.lower().startswith("video"):
                print(f"DEBUG: No es un archivo de video, saltando verificación de calidad")
                return
            
            print(f"DEBUG: Verificando calidad real del archivo: {file_path}")
            
            # Usar ffprobe para obtener información del archivo descargado
            try:
                import subprocess
                result = subprocess.run([
                    "ffprobe", "-v", "quiet", "-select_streams", "v:0", 
                    "-show_entries", "stream=width,height", "-of", "csv=p=0", file_path
                ], capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0 and result.stdout.strip():
                    dimensions = result.stdout.strip().split(',')
                    if len(dimensions) >= 2 and dimensions[0].isdigit() and dimensions[1].isdigit():
                        actual_height = int(dimensions[1])  # Usar altura como resolución
                        print(f"DEBUG: Resolución real del archivo: {actual_height}p")
                        
                        # Extraer resolución del formato original
                        original_res = self._extract_resolution_from_format(original_format)
                        if original_res and actual_height != original_res:
                            print(f"DEBUG: Calidad diferente detectada: {original_res}p → {actual_height}p")
                            
                            # Actualizar el formato en la card
                            self._update_format_info_for_quality(card_widget, actual_height)
                            
                            # Mostrar aviso de calidad ajustada
                            self._show_post_download_quality_adjustment(original_res, actual_height, card_widget)
                        else:
                            print(f"DEBUG: Calidad coincidente: {actual_height}p")
                        
                        # También verificar si el worker tiene un modo diferente
                        if hasattr(card_widget, 'worker') and card_widget.worker:
                            worker_mode = getattr(card_widget.worker, '_mode', '')
                            if worker_mode and worker_mode.startswith('video_'):
                                worker_res = self._extract_resolution_from_mode(worker_mode)
                                if worker_res and worker_res != actual_height:
                                    print(f"DEBUG: Worker tenía modo {worker_res}p, archivo descargado en {actual_height}p")
                                    # Actualizar el modo del worker para futuras referencias
                                    card_widget.worker._mode = f"video_{actual_height}"
                    else:
                        print(f"DEBUG: No se pudo extraer dimensiones del archivo")
                else:
                    print(f"DEBUG: Error al obtener información del archivo con ffprobe")
                    
            except subprocess.TimeoutExpired:
                print(f"DEBUG: Timeout al verificar calidad del archivo")
            except FileNotFoundError:
                print(f"DEBUG: ffprobe no encontrado, saltando verificación de calidad")
            except Exception as e:
                print(f"DEBUG: Error al verificar calidad: {e}")
                
        except Exception as e:
            print(f"DEBUG: Error inesperado al verificar calidad: {e}")
            import traceback
            traceback.print_exc()
    
    def _extract_resolution_from_format(self, format_info: str) -> Optional[int]:
        """Extrae la resolución del texto de formato"""
        try:
            if "•" in format_info:
                parts = format_info.split("•")
                for part in parts:
                    part = part.strip()
                    if part.endswith('p') and part[:-1].isdigit():
                        return int(part[:-1])
            else:
                # Buscar patrón como "1080p" en el texto
                import re
                match = re.search(r'(\d+)p', format_info)
                if match:
                    return int(match.group(1))
        except Exception:
            pass
        return None
    
    def _show_post_download_quality_adjustment(self, expected_res: int, actual_res: int, card_widget: DownloadItemWidget) -> None:
        """Muestra un aviso cuando la calidad descargada es diferente a la esperada"""
        try:
            # Mostrar aviso en el label específico
            if hasattr(card_widget, 'quality_adjustment_label'):
                card_widget.quality_adjustment_label.setText(f"⚠️ Descargado en {actual_res}p")
                card_widget.quality_adjustment_label.setVisible(True)
                print(f"DEBUG: Aviso post-descarga mostrado: {expected_res}p → {actual_res}p")
                
                # Hacer el aviso más visible con mejor espaciado
                card_widget.quality_adjustment_label.setStyleSheet("""
                    QLabel {
                        color: #f59e0b;
                        font-weight: bold;
                        background: rgba(245, 158, 11, 0.2);
                        border: 2px solid rgba(245, 158, 11, 0.6);
                        border-radius: 6px;
                        padding: 6px 10px;
                        font-size: 12px;
                        margin: 4px;
                        min-height: 24px;
                        max-height: 28px;
                    }
                """)
            
            # Mostrar mensaje informativo
            msg = QMessageBox(self)
            msg.setWindowTitle("Calidad Descargada")
            msg.setText(f"El archivo se descargó en {actual_res}p en lugar de {expected_res}p.")
            msg.setInformativeText("Esto puede deberse a que la calidad solicitada no estaba disponible para este video.")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            
            # Estilo del mensaje
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #111827;
                }
                QMessageBox QLabel {
                    color: #e5e7eb;
                    font-size: 13px;
                }
                QMessageBox QPushButton {
                    background-color: #1f2937;
                    color: #e5e7eb;
                    border: 1px solid #374151;
                    border-radius: 6px;
                    padding: 6px 10px;
                }
                QMessageBox QPushButton:hover {
                    background-color: #374151;
                }
            """)
            
            msg.show()
            
        except Exception as e:
            print(f"DEBUG: Error al mostrar aviso post-descarga: {e}")
    
    def _start_download_worker(self, url: str, output_dir: str, mode: str, no_playlist: bool, card_widget: DownloadItemWidget) -> None:
        """Inicia el worker de descarga con la configuración final"""
        print(f"DEBUG: Iniciando worker con modo final: {mode}")
        
        # Obtener el canal de la card
        channel = card_widget.data.channel if hasattr(card_widget, 'data') and hasattr(card_widget.data, 'channel') else ""
        
        worker = _DownloadWorker(url, output_dir, mode, no_playlist, channel)
        self._workers[url] = worker
        
        # Asociar el worker con el widget para poder cancelar
        card_widget.worker = worker
        card_widget.worker_url = url
        
        print("DEBUG: Conectando señales del worker...")
        
        # Conectar la señal de progreso tanto a la barra como a la etiqueta de porcentaje
        worker.progressChanged.connect(lambda value: self._update_progress(card_widget, value))
        worker.sizeTextChanged.connect(lambda text: self._update_size_text(card_widget, text))
        worker.downloadStatsChanged.connect(lambda text: self._update_download_stats(card_widget, text))
        worker.finished.connect(lambda title, path: self._on_finished(title, path, card_widget))
        worker.errorOccurred.connect(lambda msg: self._on_error(msg, card_widget))
        
        print("DEBUG: Iniciando worker...")
        worker.start()
        self.btn_download.setEnabled(False)

        # Obtener duración en segundo plano para la tarjeta (no reutilizar la de preview)
        threading.Thread(target=self._fetch_duration_for_card, args=(url, card_widget), daemon=True).start()
    
    def _update_progress(self, card_widget: DownloadItemWidget, value: int) -> None:
        """Actualiza el porcentaje y el estado"""
        try:
            # Verificar que el widget aún existe y no ha sido eliminado
            if not card_widget or not hasattr(card_widget, 'progress_label') or not card_widget.progress_label:
                return
                
            # Actualizar el porcentaje
            card_widget.progress_label.setText(f"{value}%")
            
            # Actualizar también la etiqueta de velocidad para mostrar el estado
            if value < 80:
                card_widget.speed.setText("Descargando...")
                card_widget.speed.setObjectName("")
            elif value < 95:
                card_widget.speed.setText("Convirtiendo...")
                card_widget.speed.setObjectName("")
            elif value < 100:
                card_widget.speed.setText("Finalizando...")
                card_widget.speed.setObjectName("")
            else:
                card_widget.speed.setText("Completado")
                card_widget.speed.setObjectName("CompletedLabel")  # Estilo verde para completado
            
            # Aplicar el estilo actualizado
            card_widget.speed.style().unpolish(card_widget.speed)
            card_widget.speed.style().polish(card_widget.speed)
        except RuntimeError:
            # El widget ya fue eliminado, ignorar la actualización
            pass
        except Exception:
            # Otro tipo de error, ignorar la actualización
            pass

    def _update_size_text(self, card_widget: DownloadItemWidget, text: str) -> None:
        """Actualizar el texto de tamaño total en la tarjeta."""
        try:
            # Verificar que el widget aún existe
            if not card_widget or not hasattr(card_widget, 'set_size_text'):
                return
            
            # Solo actualizar el tamaño si no está en estado "Completado"
            # Esto evita que se sobrescriba el tamaño final correcto
            if hasattr(card_widget, 'speed') and card_widget.speed.text() != "Completado":
                print(f"DEBUG: Actualizando tamaño desde worker: '{text}'")
                card_widget.set_size_text(text)
            else:
                print(f"DEBUG: No se actualiza tamaño porque la descarga está completada")
        except RuntimeError:
            # El widget ya fue eliminado, ignorar la actualización
            pass
        except Exception:
            pass

    def _update_download_stats(self, card_widget: DownloadItemWidget, text: str) -> None:
        """Actualizar el texto de estado con bytes descargados y velocidad."""
        try:
            # Verificar que el widget aún existe
            if not card_widget or not hasattr(card_widget, 'speed'):
                return
            card_widget.speed.setText(text)
        except RuntimeError:
            # El widget ya fue eliminado, ignorar la actualización
            pass
        except Exception:
            pass
    
    def _on_error(self, msg: str, card_widget: DownloadItemWidget) -> None:
        # Actualizar la interfaz para mostrar el error
        card_widget.title.setText(f"Error: {msg}")
        card_widget.progress_label.setText("0%")  # Solo actualizar el porcentaje
        card_widget.speed.setText("Error")
        card_widget.speed.setObjectName("ErrorLabel")
        
        # Aplicar el estilo actualizado
        card_widget.speed.style().unpolish(card_widget.speed)
        card_widget.speed.style().polish(card_widget.speed)
        
        # Mostrar mensaje de error en un cuadro de diálogo
        error_dialog = QMessageBox(self)
        error_dialog.setWindowTitle("Error de descarga")
        error_dialog.setText(f"Error al descargar el video:\n{msg}")
        error_dialog.setIcon(QMessageBox.Icon.Critical)
        error_dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        error_dialog.setDefaultButton(QMessageBox.StandardButton.Ok)
        error_dialog.show()
        
        # También reproducir sonido de error (respetando configuración de sonido)
        settings = QSettings("AudioHub", "AudioHubApp")
        play_sound = settings.value("playSoundAlerts", True, type=bool)
        
        if play_sound:
            try:
                if os.name == 'nt':
                    import winsound
                    winsound.MessageBeep(winsound.MB_ICONERROR)
            except Exception:
                pass
    
    # Helpers de acciones del sistema
    def _open_folder(self, path: str) -> None:
        try:
            if not path:
                return
            # Si llega un directorio, abrirlo. Si llega un archivo, abrir su carpeta
            dir_path = path
            if os.path.isfile(path):
                dir_path = os.path.dirname(path)
            if dir_path and os.path.isdir(dir_path):
                os.startfile(dir_path)  # type: ignore[attr-defined]
        except Exception:
            pass
    def _reveal_in_explorer(self, path: str) -> None:
        try:
            if not path:
                return
            if os.path.exists(path) and os.path.isfile(path):
                # Seleccionar el archivo en el Explorador de Windows
                subprocess.Popen(["explorer", "/select,", path])
            else:
                # Si no es archivo válido, abrir la carpeta si existe
                self._open_folder(path)
        except Exception:
            pass
    
    def _open_file(self, path: str) -> None:
        try:
            if path and os.path.exists(path) and os.path.isfile(path):
                os.startfile(path)  # type: ignore[attr-defined]
        except Exception:
            pass
    
    def _copy_to_clipboard(self, text: str) -> None:
        try:
            if not text:
                return
            QGuiApplication.clipboard().setText(text)
        except Exception:
            pass

    def refresh(self) -> None:
        # placeholder for future refresh hooks
        pass


class _DownloadWorker(QObject, threading.Thread):
    progressChanged = pyqtSignal(int)
    sizeTextChanged = pyqtSignal(str)
    downloadStatsChanged = pyqtSignal(str)
    finished = pyqtSignal(str, str)
    errorOccurred = pyqtSignal(str)

    def __init__(self, url: str, output_dir: str, mode: str = "video_best", no_playlist: bool = True, channel: str = "") -> None:
        QObject.__init__(self)
        threading.Thread.__init__(self, daemon=True)
        self._url = url
        self._output = output_dir
        self._mode = mode
        self._no_playlist = no_playlist
        self._channel = channel
        self._filesize: Optional[int] = None
        self._cancelled = False  # Flag para cancelación
        self._process: Optional[subprocess.Popen] = None  # Referencia al proceso
        self._download_started = False  # Flag para detectar si realmente empezó la descarga
        self._real_progress_detected = False  # Flag para detectar progreso real
        self._last_progress_value = 0  # Último valor de progreso real
        self._download_size_bytes = 0  # Tamaño real de la descarga

    def cancel(self) -> None:
        """Cancela la descarga actual"""
        self._cancelled = True
        if self._process and self._process.poll() is None:
            try:
                # Terminar el proceso de yt-dlp
                self._process.terminate()
                # Esperar un poco para que termine graciosamente
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                # Si no termina en 2 segundos, forzar terminación
                try:
                    self._process.kill()
                except Exception:
                    pass
            except Exception:
                pass
        
        # Limpiar archivos .part residuales
        self._cleanup_partial_files()
    
    def _cleanup_partial_files(self) -> None:
        """Limpia archivos .part y .ytdl residuales de la descarga cancelada"""
        try:
            import glob
            import os
            
            # Buscar archivos .part en el directorio de salida
            pattern = os.path.join(self._output, "*.part")
            part_files = glob.glob(pattern)
            
            # Buscar archivos .ytdl en el directorio de salida
            ytdl_pattern = os.path.join(self._output, "*.ytdl")
            ytdl_files = glob.glob(ytdl_pattern)
            
            # También buscar archivos .part y .ytdl con nombres más específicos (títulos de video)
            if hasattr(self, '_last_path') and self._last_path:
                # Si tenemos el último path conocido, buscar archivos relacionados
                base_name = os.path.splitext(self._last_path)[0]
                if base_name:
                    # Buscar archivos que empiecen con el nombre base
                    base_pattern = os.path.join(self._output, f"{os.path.basename(base_name)}*.part")
                    part_files.extend(glob.glob(base_pattern))
                    
                    base_ytdl_pattern = os.path.join(self._output, f"{os.path.basename(base_name)}*.ytdl")
                    ytdl_files.extend(glob.glob(base_ytdl_pattern))
            
            # Eliminar archivos .part encontrados
            for part_file in part_files:
                try:
                    if os.path.exists(part_file):
                        os.remove(part_file)
                        print(f"Archivo parcial eliminado: {part_file}")
                except Exception as e:
                    print(f"No se pudo eliminar {part_file}: {e}")
            
            # Eliminar archivos .ytdl encontrados
            for ytdl_file in ytdl_files:
                try:
                    if os.path.exists(ytdl_file):
                        os.remove(ytdl_file)
                        print(f"Archivo .ytdl eliminado: {ytdl_file}")
                except Exception as e:
                    print(f"No se pudo eliminar {ytdl_file}: {e}")
                    
        except Exception as e:
            print(f"Error al limpiar archivos residuales: {e}")

    def run(self) -> None:  # type: ignore[override]
        try:
            print(f"DEBUG WORKER: Iniciando worker para URL: {self._url}")
            print(f"DEBUG WORKER: Canal: {self._channel}")
            print(f"DEBUG WORKER: Modo: {self._mode}")
            print(f"DEBUG WORKER: Directorio de salida: {self._output}")
            
            # Verificar si ffmpeg está disponible para conversiones de audio
            if (self._mode.startswith("mp3_") or self._mode.startswith("m4a_") or 
                self._mode.startswith("ogg_") or self._mode.startswith("wma_")):
                try:
                    result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        print("DEBUG WORKER: ffmpeg está disponible")
                    else:
                        print("DEBUG WORKER: ffmpeg no está funcionando correctamente")
                except Exception as e:
                    print(f"DEBUG WORKER: Error verificando ffmpeg: {e}")
                    print("DEBUG WORKER: La conversión de audio puede fallar")
            
            mode = self._mode
            if mode == "video_best":
                fmt = "bv*[ext=mp4]+ba[ext=m4a]/bv*+ba/b[ext=mp4]/b"  # Preferir MP4
            elif mode.startswith("video_"):
                res = mode.split("_")[1]
                # Formato más flexible con fallbacks - usar best como último recurso
                fmt = f"bestvideo[height<={res}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={res}]+bestaudio/best[height<={res}][ext=mp4]/best[height<={res}]/best[ext=mp4]/best"
                print(f"DEBUG WORKER: Usando formato flexible para resolución {res}: {fmt}")
            elif mode.startswith("mp3_"):
                fmt = "bestaudio/best"
            elif mode == "m4a_best":
                fmt = "bestaudio[ext=m4a]/bestaudio/best"
            elif mode == "ogg_best":
                fmt = "bestaudio/best"
            elif mode == "wma_best":
                fmt = "bestaudio/best"
            else:
                fmt = "b[ext=mp4]/b"  # Preferir MP4 por defecto

            output_template = os.path.join(self._output, "%(title)s.%(ext)s")
            args = [
                "yt-dlp",
                "-f", fmt,
                "--prefer-ffmpeg",  # Usar ffmpeg para conversión
                "-o", output_template,
                "--newline",
                "--progress",
                "--no-overwrites",  # No sobrescribir archivos existentes
                "--restrict-filenames",  # Restringir nombres de archivo para evitar caracteres problemáticos
                self._url,
            ]
            if self._no_playlist:
                args += ["--no-playlist"]
            
            print(f"DEBUG WORKER: Comando yt-dlp: {' '.join(args)}")
            
            # Configuración específica para cada formato de audio
            if mode.startswith("mp3_"):
                bitrate = mode.split("_")[1] + "k"
                args += [
                    "--extract-audio",
                    "--audio-format", "mp3",
                    "--audio-quality", bitrate,
                    "--prefer-ffmpeg",  # Forzar uso de ffmpeg
                    "--postprocessor-args", "ffmpeg:-acodec libmp3lame",  # Usar codec MP3 específico
                ]
                print(f"DEBUG WORKER: Configuración MP3 - bitrate: {bitrate}")
            elif mode == "ogg_best":
                args += [
                    "--extract-audio",
                    "--audio-format", "vorbis",  # OGG usa codec Vorbis
                    "--audio-quality", "192k",   # Calidad estándar para OGG
                    "--prefer-ffmpeg",  # Forzar uso de ffmpeg
                    "--postprocessor-args", "ffmpeg:-acodec libvorbis",  # Codec Vorbis específico
                ]
                print(f"DEBUG WORKER: Configuración OGG - calidad: 192k")
            elif mode == "ogg_320":
                args += [
                    "--extract-audio",
                    "--audio-format", "vorbis",  # OGG usa codec Vorbis
                    "--audio-quality", "320k",   # Calidad alta para OGG
                    "--prefer-ffmpeg",  # Forzar uso de ffmpeg
                    "--postprocessor-args", "ffmpeg:-acodec libvorbis",  # Codec Vorbis específico
                ]
                print(f"DEBUG WORKER: Configuración OGG - calidad: 320k")
            elif mode == "wma_best":
                args += [
                    "--extract-audio",
                    "--audio-format", "wma",
                    "--audio-quality", "192k",   # Calidad estándar para WMA
                    "--prefer-ffmpeg",  # Forzar uso de ffmpeg
                    "--postprocessor-args", "ffmpeg:-acodec wmav2",  # Codec WMA específico
                ]
                print(f"DEBUG WORKER: Configuración WMA - calidad: 192k")
            elif mode == "wma_320":
                args += [
                    "--extract-audio",
                    "--audio-format", "wma",
                    "--audio-quality", "320k",   # Calidad alta para WMA
                    "--prefer-ffmpeg",  # Forzar uso de ffmpeg
                    "--postprocessor-args", "ffmpeg:-acodec wmav2",  # Codec WMA específico
                ]
                print(f"DEBUG WORKER: Configuración WMA - calidad: 320k")
            elif mode == "m4a_best":
                args += [
                    "--extract-audio",
                    "--audio-format", "m4a",
                    "--audio-quality", "192k",
                    "--prefer-ffmpeg",  # Forzar uso de ffmpeg
                    "--postprocessor-args", "ffmpeg:-acodec aac",  # Codec AAC específico
                ]
                print(f"DEBUG WORKER: Configuración M4A - calidad: 192k")
            elif mode == "m4a_320":
                args += [
                    "--extract-audio",
                    "--audio-format", "m4a",
                    "--audio-quality", "320k",
                    "--prefer-ffmpeg",  # Forzar uso de ffmpeg
                    "--postprocessor-args", "ffmpeg:-acodec aac",  # Codec AAC específico
                ]
                print(f"DEBUG WORKER: Configuración M4A - calidad: 320k")
            elif mode == "video_best" or mode.startswith("video_"):
                # Solo para videos, forzar formato MP4
                args += ["--merge-output-format", "mp4"]

            # Emitir progreso inicial
            self.progressChanged.emit(1)
            
            proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            self._process = proc  # Guardar referencia al proceso para poder cancelarlo
            
            last_path = None
            download_completed = False
            conversion_started = False
            last_progress_time = time.time()
            error_detected = False
            error_message = ""
            total_size_text = ""
            total_size_bytes: Optional[float] = None
            last_pct_val: Optional[float] = None
            
            for line in proc.stdout:  # type: ignore[union-attr]
                # Verificar si se canceló la descarga
                if self._cancelled:
                    try:
                        proc.terminate()
                        proc.wait(timeout=2)
                    except Exception:
                        pass
                    # Limpiar archivos .part antes de salir
                    self._cleanup_partial_files()
                    return  # Salir del método run
                
                line = line.strip()
                current_time = time.time()
                
                # Detectar mensajes de error comunes de yt-dlp
                if "ERROR:" in line or "Error:" in line:
                    error_detected = True
                    error_message = line
                    print(f"DEBUG WORKER ERROR: {line}")
                    # Registrar el error en el log
                    try:
                        with open("ytdlp_debug.log", "a", encoding="utf-8") as f:
                            f.write(f"[ERROR] {line}\n")
                    except:
                        pass
                
                # Errores específicos con mensajes más amigables
                if "No video formats found" in line or "requested format not available" in line:
                    raise Exception("No se encontraron formatos de video disponibles para esta URL")
                elif "Unsupported URL" in line or "is not a valid URL" in line:
                    raise Exception("La URL proporcionada no es válida o no está soportada")
                elif "Private video" in line or "Sign in to confirm your age" in line:
                    raise Exception("Este video es privado o requiere verificación de edad")
                elif "This video is unavailable" in line:
                    raise Exception("Este video no está disponible")
                elif "Video unavailable" in line:
                    raise Exception("Video no disponible. Puede haber sido eliminado o marcado como privado")
                elif "requested format not available" in line or "format not available" in line:
                    # No lanzar excepción inmediatamente, solo registrar la advertencia
                    print(f"WARNING: {line}")
                elif "has already been downloaded" in line and not download_completed:
                    # Si dice que ya está descargado pero no hemos detectado descarga, puede ser un error
                    print(f"WARNING: {line}")
                elif "WARNING:" in line and ("format not available" in line or "requested format" in line):
                    # Solo registrar advertencias, no lanzar excepción
                    print(f"WARNING: {line}")
                elif "Skipping" in line and "format not available" in line:
                    # Solo registrar que se está saltando un formato
                    print(f"INFO: {line}")
                
                # Detectar errores de archivos duplicados
                elif "already exists" in line or "file already exists" in line:
                    error_detected = True
                    error_message = "El archivo ya existe. Por favor, elimina el archivo existente o elige un nombre diferente."
                    print(f"DEBUG WORKER ERROR DUPLICADO: {line}")
                    # Registrar el error en el log
                    try:
                        with open("ytdlp_debug.log", "a", encoding="utf-8") as f:
                            f.write(f"[ERROR DUPLICADO] {line}\n")
                    except:
                        pass
                
                # Errores específicos de conversión de audio
                elif "ffmpeg" in line.lower() and ("error" in line.lower() or "failed" in line.lower()):
                    print(f"ERROR CONVERSIÓN AUDIO: {line}")
                    # No lanzar excepción inmediatamente, intentar continuar
                elif "conversion" in line.lower() and ("error" in line.lower() or "failed" in line.lower()):
                    print(f"ERROR CONVERSIÓN: {line}")
                    # No lanzar excepción inmediatamente, intentar continuar
                elif "codec" in line.lower() and ("error" in line.lower() or "failed" in line.lower() or "not found" in line.lower()):
                    print(f"ERROR CODEC: {line}")
                    # Error específico de codec, puede ser problema de ffmpeg
                elif "aac" in line.lower() and ("error" in line.lower() or "failed" in line.lower()):
                    print(f"ERROR CODEC AAC: {line}")
                    # Error específico del codec AAC para M4A
                elif "vorbis" in line.lower() and ("error" in line.lower() or "failed" in line.lower()):
                    print(f"ERROR CODEC VORBIS: {line}")
                    # Error específico del codec Vorbis para OGG
                elif "wma" in line.lower() and ("error" in line.lower() or "failed" in line.lower()):
                    print(f"ERROR CODEC WMA: {line}")
                    # Error específico del codec WMA
                
                # Emitir actualizaciones de progreso más frecuentes durante períodos sin salida
                if current_time - last_progress_time > 1.0 and download_completed and conversion_started:
                    # Incrementar gradualmente durante la conversión
                    current_progress = min(94, self._get_last_progress() + 1)
                    self.progressChanged.emit(current_progress)
                    last_progress_time = current_time
                
                if line.startswith("[download] Destination:"):
                    last_path = line.split("Destination:", 1)[1].strip()
                    self._download_started = True  # Marcar que realmente empezó la descarga
                    self.progressChanged.emit(5)  # Inicio de descarga
                
                # Detectar progreso de descarga y tamaño total
                if line.startswith("[download]") and "%" in line:
                    try:
                        # Ejemplo de línea: "[download]  12.3% of 50.00MiB at 2.31MiB/s ETA 00:40"
                        parts = line.split()
                        # Extraer porcentaje
                        pct_str = None
                        for token in parts:
                            if token.endswith('%'):
                                pct_str = token.rstrip('%')
                                break
                        if pct_str is not None:
                            last_pct_val = float(pct_str)
                            pct_int = int(last_pct_val)
                            adjusted_pct = int(pct_int * 0.75)
                            self.progressChanged.emit(max(5, min(75, adjusted_pct)))
                            last_progress_time = current_time
                            
                            # Detectar progreso real
                            if pct_int > self._last_progress_value:
                                self._real_progress_detected = True
                                self._last_progress_value = pct_int
                            
                            # Detectar si el progreso se está simulando (siempre el mismo valor)
                            if pct_int == self._last_progress_value and pct_int > 0:
                                # Si el progreso no cambia, podría ser una simulación
                                pass
                        
                        # Extraer tamaño total después de la palabra 'of'
                        if ' of ' in line:
                            after_of = line.split(' of ', 1)[1]
                            # after_of comienza con "50.00MiB ..."
                            size_token = after_of.split()[0]
                            human_text = self._humanize_yt_dlp_size(size_token)
                            if human_text and human_text != total_size_text:
                                total_size_text = human_text
                                # Solo emitir el tamaño durante la descarga activa, no al final
                                if not download_completed:
                                    self.sizeTextChanged.emit(total_size_text)
                            total_size_bytes = self._size_token_to_bytes(size_token)
                            if total_size_bytes:
                                self._download_size_bytes = total_size_bytes
                        # Extraer velocidad después de " at "
                        speed_text = ""
                        if ' at ' in line:
                            after_at = line.split(' at ', 1)[1]
                            speed_token = after_at.split()[0]  # p.ej. 2.31MiB/s
                            speed_text = self._humanize_speed(speed_token)
                        # Extraer ETA si aparece
                        eta_text = ""
                        if ' ETA ' in line:
                            try:
                                eta_part = line.split(' ETA ', 1)[1]
                                # token típico: 00:40 o 1:20:15; tomar primer token
                                eta_text = eta_part.split()[0]
                            except Exception:
                                eta_text = ""
                        # Construir texto de estado si tenemos datos suficientes
                        if total_size_text and last_pct_val is not None and total_size_bytes:
                            downloaded_bytes = (last_pct_val / 100.0) * float(total_size_bytes)
                            downloaded_human = self._humanize_bytes(downloaded_bytes)
                            status = f"Descargando… {downloaded_human} de {total_size_text}"
                            if speed_text:
                                status += f" — {speed_text}"
                            if eta_text:
                                eta_fmt = self._format_eta(eta_text)
                                if eta_fmt:
                                    status += f" — {eta_fmt} restantes"
                            self.downloadStatsChanged.emit(status)
                    except Exception:
                        pass
                
                # Detectar cuando termina la descarga y comienza la conversión
                if line.startswith("[download] 100%") or "Destination:" in line and download_completed:
                    download_completed = True
                    self.progressChanged.emit(75)  # Marcar 75% al terminar descarga
                    last_progress_time = current_time
                
                # Detectar inicio de conversión
                if "Extracting audio" in line or "Merging formats" in line:
                    download_completed = True
                    conversion_started = True
                    self.progressChanged.emit(80)  # Inicio de conversión
                    last_progress_time = current_time
                
                # Detectar progreso de conversión/postprocesamiento
                conversion_indicators = [
                    "Deleting original file", "Correcting container", "Fixing DASH", 
                    "Merging formats", "Converting", "Postprocessing", "Extracting audio",
                    "Destination:", "Writing metadata", "ffmpeg", "ETA", "at"
                ]
                
                for indicator in conversion_indicators:
                    if indicator in line and download_completed:
                        conversion_started = True
                        current_progress = min(94, self._get_last_progress() + 1)
                        self.progressChanged.emit(current_progress)
                        last_progress_time = current_time
                        break
                
                # Detectar finalización de conversión
                if download_completed and ("has already been downloaded" in line or
                                          "Post-process file" in line or
                                          "Finished downloading" in line):
                    self.progressChanged.emit(95)  # Casi terminado
                    last_progress_time = current_time
            
            # Esperar a que termine el proceso
            return_code = proc.wait()
            
            # Verificar si hubo errores durante el proceso
            if error_detected:
                raise Exception(error_message)
            
            # Verificar el código de retorno
            if return_code != 0:
                raise Exception(f"El proceso de descarga falló con código de error {return_code}")
            
            # Verificar que el archivo realmente se haya descargado
            if not last_path or not os.path.exists(last_path):
                # Si no hay path o el archivo no existe, verificar si hay archivos en el directorio
                import glob
                output_files = glob.glob(os.path.join(self._output, "*"))
                if not output_files:
                    raise Exception("Error: La descarga se completó pero no se encontró ningún archivo. La calidad solicitada puede no estar disponible.")
                else:
                    # Buscar el archivo más reciente que podría ser el descargado
                    latest_file = max(output_files, key=os.path.getctime)
                    if os.path.isfile(latest_file):
                        last_path = latest_file
                    else:
                        raise Exception("Error: La descarga se completó pero no se encontró ningún archivo válido. La calidad solicitada puede no estar disponible.")
            
            # Verificar que el archivo tenga un tamaño razonable (más de 1KB)
            if last_path and os.path.exists(last_path):
                file_size = os.path.getsize(last_path)
                if file_size < 1024:  # Menos de 1KB
                    raise Exception("Error: El archivo descargado es demasiado pequeño. La calidad solicitada puede no estar disponible para este video.")
                
                # Verificar si la descarga fue real o simulada
                if not self._download_started:
                    raise Exception("Error: La descarga no comenzó realmente. La calidad solicitada puede no estar disponible.")
                
                if not self._real_progress_detected:
                    raise Exception("Error: No se detectó progreso real de descarga. La calidad solicitada puede no estar disponible.")
                
                # Verificar que el tamaño del archivo sea razonable comparado con el tamaño esperado
                if self._download_size_bytes > 0 and file_size < (self._download_size_bytes * 0.1):  # Menos del 10% del tamaño esperado
                    print(f"WARNING: El archivo descargado es más pequeño de lo esperado, pero continuando...")
            
            # Si llegamos aquí, todo salió bien
            self.progressChanged.emit(100)  # Completado
            self.finished.emit(os.path.basename(last_path or self._url), last_path or self._output)
        except subprocess.SubprocessError as e:
            self.errorOccurred.emit(f"Error en el proceso de descarga: {str(e)}")
        except FileNotFoundError:
            self.errorOccurred.emit("No se encontró el programa yt-dlp. Asegúrate de que esté instalado correctamente.")
        except PermissionError:
            self.errorOccurred.emit("Error de permisos al acceder a los archivos. Verifica los permisos de la carpeta de destino.")
        except Exception as e:
            # Capturar el traceback para diagnóstico
            import traceback
            error_details = traceback.format_exc()
            # Registrar el error completo en el archivo de log
            try:
                with open("ytdlp_debug.log", "a", encoding="utf-8") as f:
                    f.write(f"\n[ERROR] {error_details}\n")
            except:
                pass
            # Enviar un mensaje de error más amigable al usuario
            self.errorOccurred.emit(f"Error inesperado: {str(e)}. Consulta el archivo de log para más detalles.")
    
    def _get_last_progress(self) -> int:
        """Obtiene el último valor de progreso emitido"""
        # Esta es una implementación simple que no almacena el último valor
        # En una implementación más completa, se podría almacenar el último valor emitido
        return 80  # Valor predeterminado durante la conversión

    @staticmethod
    def _humanize_yt_dlp_size(token: str) -> str:
        """Convierte un token de tamaño de yt-dlp (p.ej. '50.00MiB', '1.2GiB') a 'XX.X MB' o 'X.Y GB'."""
        try:
            # Separar número y unidad (KiB, MiB, GiB)
            import re as _re
            m = _re.match(r"([0-9]+(?:\.[0-9]+)?)([KMG]i?B)", token)
            if not m:
                return ""
            value = float(m.group(1))
            unit = m.group(2)
            # Convertir a texto amable (MB / GB)
            if unit.startswith('G'):
                return f"{value:.2f} GB"
            elif unit.startswith('M'):
                return f"{value:.2f} MB"
            elif unit.startswith('K'):
                # Mostrar en KB si es pequeño
                return f"{value:.0f} KB"
            else:
                return f"{value} B"
        except Exception:
            return ""

    @staticmethod
    def _size_token_to_bytes(token: str) -> Optional[float]:
        """Convierte tokens como '50.00MiB' a bytes (aprox, base 1024)."""
        try:
            import re as _re
            m = _re.match(r"([0-9]+(?:\.[0-9]+)?)([KMG]i?B)", token)
            if not m:
                return None
            value = float(m.group(1))
            unit = m.group(2)
            factor = 1.0
            if unit.startswith('K'):
                factor = 1024.0
            elif unit.startswith('M'):
                factor = 1024.0 ** 2
            elif unit.startswith('G'):
                factor = 1024.0 ** 3
            return value * factor
        except Exception:
            return None

    @staticmethod
    def _humanize_bytes(nbytes: float) -> str:
        try:
            if nbytes >= 1024**3:
                return f"{nbytes / (1024**3):.2f} GB"
            if nbytes >= 1024**2:
                return f"{nbytes / (1024**2):.2f} MB"
            if nbytes >= 1024:
                return f"{nbytes / 1024:.0f} KB"
            return f"{int(nbytes)} B"
        except Exception:
            return ""

    @staticmethod
    def _humanize_speed(token: str) -> str:
        """Normaliza tokens como '2.31MiB/s' a '2.31 MB/s'."""
        try:
            if token.lower().endswith('/s'):
                base = token[:-2]  # quitar '/s'
                # Reutilizar conversión de tamaño pero solo para unidad y número
                text = _DownloadWorker._humanize_yt_dlp_size(base)
                if text:
                    return text + "/s"
            return token
        except Exception:
            return token

    @staticmethod
    def _format_eta(eta_token: str) -> str:
        """Devuelve ETA en formato mm:ss o hh:mm:ss (según corresponda), sin prefijo."""
        try:
            parts = eta_token.split(":")
            # Si ya viene como mm:ss o hh:mm:ss lo dejamos igual
            if len(parts) == 2:
                mm, ss = parts
                # normalizar a dos dígitos
                return f"{int(mm):02d}:{int(ss):02d}"
            if len(parts) == 3:
                hh, mm, ss = parts
                return f"{int(hh)}:{int(mm):02d}:{int(ss):02d}"
            # Si viene en segundos, convertir
            secs = int(float(eta_token))
            if secs >= 3600:
                h = secs // 3600
                m = (secs % 3600) // 60
                s = secs % 60
                return f"{h}:{m:02d}:{s:02d}"
            else:
                m = secs // 60
                s = secs % 60
                return f"{m:02d}:{s:02d}"
        except Exception:
            return eta_token or ""


