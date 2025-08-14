from __future__ import annotations

import os
import subprocess
import json
import re
from dataclasses import dataclass
from typing import Optional, Dict, Any
from PyQt6.QtCore import QThread, pyqtSignal

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QComboBox,
    QMessageBox,
    QDialog,
    QFrame,
    QGridLayout,
)


class SuccessDialog(QDialog):
    """Custom success dialog that matches the app's design."""
    
    def __init__(self, parent=None, message="", file_path=""):
        super().__init__(parent)
        
        self.setFixedSize(400, 200)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self._build(message, file_path)
    
    def _build(self, message: str, file_path: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Set dialog background to match app theme
        self.setStyleSheet("""
            QDialog {
                background: #1a1a1a;
            }
        """)
        
        # Success icon and title
        title_layout = QHBoxLayout()
        success_icon = QLabel("✓")
        success_icon.setStyleSheet("""
            QLabel {
                color: #10b981;
                font-size: 32px;
                font-weight: bold;
                background: rgba(16, 185, 129, 0.1);
                border-radius: 20px;
                padding: 8px;
                min-width: 40px;
                max-width: 40px;
                min-height: 40px;
                max-height: 40px;
            }
        """)
        success_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel("Conversión Completada")
        title.setStyleSheet("""
            QLabel {
                color: #e8e8ef;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        
        title_layout.addWidget(success_icon)
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # Message
        msg_label = QLabel(message)
        msg_label.setStyleSheet("""
            QLabel {
                color: #c9c9d6;
                font-size: 14px;
            }
        """)
        msg_label.setWordWrap(True)
        layout.addWidget(msg_label)
        
        # File path info
        if file_path:
            path_label = QLabel(f"Archivo guardado en:\n{file_path}")
            path_label.setStyleSheet("""
                QLabel {
                    color: #a855f7;
                    font-size: 12px;
                    font-family: monospace;
                    background: rgba(168, 85, 247, 0.1);
                    border-radius: 8px;
                    padding: 8px;
                }
            """)
            path_label.setWordWrap(True)
            layout.addWidget(path_label)
        
        layout.addStretch()
        
        # OK button
        ok_button = QPushButton("Aceptar")
        ok_button.setStyleSheet("""
            QPushButton {
                background: #a855f7;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #b06df8;
            }
        """)
        ok_button.clicked.connect(self.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        layout.addLayout(button_layout)


class ConversionWorker(QThread):
    """Worker thread for audio conversion to avoid blocking the UI."""
    
    conversion_finished = pyqtSignal(bool, str)  # success, message
    progress_updated = pyqtSignal(int)  # progress percentage
    
    def __init__(self, input_path: str, output_path: str, format_name: str, bitrate: str):
        super().__init__()
        self.input_path = input_path
        self.output_path = output_path
        self.format_name = format_name
        self.bitrate = bitrate
    
    def run(self):
        try:
            # Extract bitrate number from "320 kbps" format
            bitrate_num = int(self.bitrate.split()[0])
            
            # Build ffmpeg command (simpler approach without progress monitoring)
            cmd = [
                "ffmpeg",
                "-hide_banner",
                "-nostats",
                "-loglevel", "error",
                "-i", self.input_path,
                "-vn",  # No video
                "-ar", "44100",  # Sample rate
                "-ac", "2",  # Stereo
            ]
            
            # Add format-specific options
            if self.format_name == "MP3":
                cmd.extend(["-c:a", "mp3", "-b:a", f"{bitrate_num}k"])
            elif self.format_name == "M4A":
                cmd.extend(["-c:a", "aac", "-b:a", f"{bitrate_num}k"])
            elif self.format_name == "WAV":
                cmd.extend(["-c:a", "pcm_s16le"])
            elif self.format_name == "FLAC":
                cmd.extend(["-c:a", "flac"])
            elif self.format_name == "OGG":
                cmd.extend(["-c:a", "libvorbis", "-b:a", f"{bitrate_num}k"])
            elif self.format_name == "WMA":
                cmd.extend(["-c:a", "wmav2", "-b:a", f"{bitrate_num}k"])
            
            cmd.append(self.output_path)
            
            # Run conversion with simple progress simulation
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            
            # Simulate progress for better UX
            import time
            progress = 0
            
            # Start with immediate progress
            self.progress_updated.emit(10)
            progress = 10
            
            while process.poll() is None:
                time.sleep(0.1)  # Slightly slower for stability
                if progress < 90:  # Allow progress to go higher
                    progress += 2
                    self.progress_updated.emit(progress)
                else:
                    # Once we reach 90%, just pulse between 90-95 to show activity
                    if progress >= 95:
                        progress = 90
                    else:
                        progress += 1
                    self.progress_updated.emit(progress)
            
            # Wait for process to complete
            return_code = process.wait()
            
            # Always send 100% when process completes
            self.progress_updated.emit(100)
            
            if return_code == 0:
                self.conversion_finished.emit(True, "Conversión completada")
            else:
                stderr_output = process.stderr.read()
                self.conversion_finished.emit(False, f"Error en la conversión: {stderr_output}")
                
        except subprocess.TimeoutExpired:
            self.conversion_finished.emit(False, "Timeout: La conversión tardó demasiado")
        except Exception as e:
            self.conversion_finished.emit(False, f"Error: {str(e)}")


class MediaInfoExtractor:
    """Extracts media information using ffmpeg."""
    
    @staticmethod
    def get_media_info(file_path: str) -> Dict[str, Any]:
        """Get media file information using ffmpeg."""
        try:
            # Run ffprobe to get file information in JSON format
            cmd = [
                "ffprobe", 
                "-v", "quiet", 
                "-print_format", "json", 
                "-show_format", 
                "-show_streams", 
                file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            
            # Extract relevant information
            info = {
                "title": "Desconocido",
                "extension": os.path.splitext(file_path)[1][1:].upper(),
                "bitrate": "Desconocido",
                "sample_rate": "Desconocido",
                "duration": "Desconocido"
            }
            
            # Get format information
            if "format" in data:
                # Title from metadata or filename
                if "tags" in data["format"] and "title" in data["format"]["tags"]:
                    info["title"] = data["format"]["tags"]["title"]
                else:
                    # Use filename as title if no metadata title exists
                    info["title"] = os.path.splitext(os.path.basename(file_path))[0]
                
                # Bitrate
                if "bit_rate" in data["format"]:
                    bitrate_kbps = int(int(data["format"]["bit_rate"]) / 1000)
                    info["bitrate"] = f"{bitrate_kbps} kbps"
                
                # Duration
                if "duration" in data["format"]:
                    duration_seconds = float(data["format"]["duration"])
                    minutes = int(duration_seconds // 60)
                    seconds = int(duration_seconds % 60)
                    info["duration"] = f"{minutes}:{seconds:02d}"
            
            # Get audio stream information
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "audio":
                    # Sample rate
                    if "sample_rate" in stream:
                        info["sample_rate"] = f"{stream['sample_rate']} Hz"
                    
                    # If bitrate wasn't in format, try to get it from stream
                    if info["bitrate"] == "Desconocido" and "bit_rate" in stream:
                        bitrate_kbps = int(int(stream["bit_rate"]) / 1000)
                        info["bitrate"] = f"{bitrate_kbps} kbps"
                    
                    break  # Only use the first audio stream
            
            return info
            
        except Exception as e:
            print(f"Error extracting media info: {str(e)}")
            return {
                "title": os.path.splitext(os.path.basename(file_path))[0],
                "extension": os.path.splitext(file_path)[1][1:].upper(),
                "bitrate": "Desconocido",
                "sample_rate": "Desconocido",
                "duration": "Desconocido"
            }


class FileInfoPanel(QFrame):
    """Panel that displays file information in an elegant way."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FileInfoPanel")
        self.setVisible(False)  # Hidden by default
        self._build()
    
    def _build(self):
        # Set up the frame style
        self.setStyleSheet("""
            #FileInfoPanel {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 12px;
                padding: 16px;
                margin-top: 8px;
                margin-bottom: 16px;
                border: 1px solid rgba(168, 85, 247, 0.3);
            }
            .InfoLabel {
                color: #a0a0a0;
                font-size: 12px;
                padding: 6px 0;
                min-height: 28px;
            }
            .InfoValue {
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                padding: 6px 0;
                min-height: 28px;
            }
            #TitleValue {
                color: #a855f7;
                font-size: 16px;
                font-weight: bold;
                min-height: 32px;
                padding: 6px 0;
            }
        """)
        
        # Main layout for icon and text content
        main_h_layout = QHBoxLayout(self)
        main_h_layout.setContentsMargins(16, 16, 16, 16)
        main_h_layout.setSpacing(16) # Increased spacing between icon and text

        # Icon label
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(72, 72) # Initial size, will adjust
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("background: rgba(168, 85, 247, 0.1); border-radius: 8px;")
        main_h_layout.addWidget(self.icon_label)

        # Text content layout (title and metadata)
        text_content_layout = QVBoxLayout()
        text_content_layout.setContentsMargins(0, 0, 0, 0)
        text_content_layout.setSpacing(4) # Smaller spacing between title and metadata
        
        # Title section
        self.title_value = QLabel("")
        self.title_value.setObjectName("TitleValue")
        self.title_value.setWordWrap(True)
        self.title_value.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.title_value.setStyleSheet("line-height: 24px; padding: 4px 0;")
        text_content_layout.addWidget(self.title_value)
        
        # Metadata line
        self.metadata_label = QLabel("")
        self.metadata_label.setProperty("class", "InfoValue")
        self.metadata_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        text_content_layout.addWidget(self.metadata_label)

        main_h_layout.addLayout(text_content_layout, 1) # Text content takes remaining space

        # Load and set the icon
        self._load_icon("music-archive-svgrepo-com.svg")
    
    def _load_icon(self, icon_name: str):
        try:
            from PyQt6.QtSvg import QSvgRenderer
            from PyQt6.QtGui import QPixmap, QPainter
            from PyQt6.QtCore import Qt
            from ..utils import get_icon_path

            svg_path = get_icon_path(icon_name)
            if not os.path.exists(svg_path):
                return

            renderer = QSvgRenderer(svg_path)
            if not renderer.isValid():
                return

            icon_height = 72
            icon_width = int(icon_height * (renderer.defaultSize().width() / renderer.defaultSize().height()))
            if icon_width == 0:
                icon_width = icon_height

            pixmap = QPixmap(icon_width, icon_height)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            renderer.render(painter)
            painter.end()
            self.icon_label.setPixmap(pixmap)
            self.icon_label.setFixedSize(icon_width, icon_height)
        except Exception as e:
            print(f"Error loading icon: {e}")

    def update_info(self, info: Dict[str, Any]):
        """Update the panel with file information."""
        self.title_value.setText(info["title"])
        
        metadata_parts = []
        if info.get("extension") and info["extension"] != "Desconocido":
            metadata_parts.append(f"<b>{info['extension']}</b>")
        if info.get("bitrate") and info["bitrate"] != "Desconocido":
            metadata_parts.append(f"Bitrate: <b>{info['bitrate']}</b>")
        if info.get("sample_rate") and info["sample_rate"] != "Desconocido":
            metadata_parts.append(f"Sample Rate: <b>{info['sample_rate']}</b>")
        if info.get("duration") and info["duration"] != "Desconocido":
            metadata_parts.append(f"Duración: <b>{info['duration']}</b>")

        self.metadata_label.setText("  •  ".join(metadata_parts))
        
        self.setVisible(True)


class ConverterPage(QWidget):
    """Audio conversion page with simple controls.

    Saves output by default next to the source file, honoring user preference.
    """

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("ConverterPage")
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Conversor de Audio")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignVCenter)
        form.setVerticalSpacing(12)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form.setHorizontalSpacing(16)  # Espacio consistente entre etiquetas y campos

        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Selecciona un archivo de video/audio…")
        btn_browse = QPushButton("Examinar…")
        btn_browse.clicked.connect(self._choose_input)
        row = QHBoxLayout()
        row.addWidget(self.input_edit, 1)
        row.addWidget(btn_browse)
        wrapper = QWidget()
        wrapper.setLayout(row)
        
        # Crear etiqueta con alineación específica para "Archivo origen"
        origen_label = QLabel("Archivo origen")
        origen_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        origen_label.setFixedHeight(42)  # Match input height for perfect alignment
        form.addRow(origen_label, wrapper)
        
        # Add file info panel
        self.file_info_panel = FileInfoPanel()
        layout.addWidget(self.file_info_panel)

        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "MP3",
            "M4A",
            "WAV",
            "FLAC",
            "OGG",
            "WMA"
        ])
        self.format_combo.setCurrentText("MP3")
        self.format_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        
        # Crear contenedor para formato que coincida con el ancho del campo de origen
        format_row = QHBoxLayout()
        format_row.addWidget(self.format_combo)
        format_row.addStretch()  # Espacio flexible para igualar el ancho
        format_wrapper = QWidget()
        format_wrapper.setLayout(format_row)
        
        # Crear etiqueta con alineación específica para "Formato deseado"
        formato_label = QLabel("Formato deseado")
        formato_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        formato_label.setFixedHeight(42)  # Match input height for perfect alignment
        form.addRow(formato_label, format_wrapper)

        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems([
            "320 kbps",
            "256 kbps",
            "192 kbps",
            "160 kbps",
            "128 kbps",
            "96 kbps",
            "64 kbps"
        ])
        self.bitrate_combo.setCurrentText("320 kbps")
        self.bitrate_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        
        # Crear contenedor para bitrate que coincida con el ancho del campo de origen
        bitrate_row = QHBoxLayout()
        bitrate_row.addWidget(self.bitrate_combo)
        bitrate_row.addStretch()  # Espacio flexible para igualar el ancho
        bitrate_wrapper = QWidget()
        bitrate_wrapper.setLayout(bitrate_row)
        
        # Crear etiqueta con alineación específica para "Bitrate"
        bitrate_label = QLabel("Bitrate")
        bitrate_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        bitrate_label.setFixedHeight(42)  # Match input height for perfect alignment
        form.addRow(bitrate_label, bitrate_wrapper)

        layout.addLayout(form)

        self.btn_convert = QPushButton("Convertir")
        self.btn_convert.clicked.connect(self._convert)
        layout.addWidget(self.btn_convert)
        layout.addStretch(1)

    # Slots
    def _choose_input(self) -> None:
        # Get default directory from settings
        from PyQt6.QtCore import QSettings
        settings = QSettings("AudioHub", "AudioHubApp")
        default_dir = settings.value("downloadDir", type=str)
        if not default_dir or not os.path.exists(default_dir):
            default_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo", default_dir, "Multimedia (*.mp4 *.mkv *.mp3 *.wav *.m4a *.ogg *.wma)"
        )
        if not path:
            return
        self.input_edit.setText(path)
        
        # Extract and display file information
        try:
            # Check if ffprobe is available
            subprocess.run(["ffprobe", "-version"], capture_output=True, check=True)
            
            # Get file information
            file_info = MediaInfoExtractor.get_media_info(path)
            
            # Update the info panel
            self.file_info_panel.update_info(file_info)
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            # If ffprobe is not available, show basic info
            basic_info = {
                "title": os.path.splitext(os.path.basename(path))[0],
                "extension": os.path.splitext(path)[1][1:].upper(),
                "bitrate": "Desconocido (ffprobe no disponible)",
                "sample_rate": "Desconocido (ffprobe no disponible)",
                "duration": "Desconocido (ffprobe no disponible)"
            }
            self.file_info_panel.update_info(basic_info)

    def _on_format_changed(self, format_name: str) -> None:
        """Manejador para cuando cambia el formato seleccionado."""
        # No es necesario resetear el botón ya que no tiene estado "Convertido"
        pass

    def _convert(self) -> None:
        # Check if ffmpeg is available
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            QMessageBox.critical(
                self, 
                "Error", 
                "FFmpeg no está instalado o no está en el PATH.\n\n"
                "Para usar el conversor, necesitas instalar FFmpeg:\n"
                "• Windows: Descarga desde https://ffmpeg.org/download.html\n"
                "• macOS: brew install ffmpeg\n"
                "• Linux: sudo apt install ffmpeg"
            )
            return
        
        # Get input file path
        input_path = self.input_edit.text().strip()
        if not input_path or not os.path.exists(input_path):
            QMessageBox.warning(self, "Error", "Por favor selecciona un archivo válido")
            return
        
        # Get settings
        format_name = self.format_combo.currentText()
        bitrate = self.bitrate_combo.currentText()
        
        # Generate output path
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        self.output_path = os.path.join(os.path.dirname(input_path), f"{base_name}.{format_name.lower()}")
        
        # Check if output file already exists
        if os.path.exists(self.output_path):
            reply = QMessageBox.question(
                self, 
                "Archivo existente", 
                f"El archivo {os.path.basename(self.output_path)} ya existe. ¿Deseas sobrescribirlo?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
            else:
                # Delete existing file first
                try:
                    os.remove(self.output_path)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"No se pudo eliminar el archivo existente: {str(e)}")
                    return
        
        # Disable button and show progress
        self.btn_convert.setText("Convirtiendo...")
        self.btn_convert.setEnabled(False)
        
        # Start conversion in background thread
        self.conversion_worker = ConversionWorker(input_path, self.output_path, format_name, bitrate)
        self.conversion_worker.conversion_finished.connect(self._on_conversion_finished)
        self.conversion_worker.progress_updated.connect(self._on_progress_updated)
        self.conversion_worker.start()

    def _on_progress_updated(self, progress: int) -> None:
        """Handle progress updates during conversion"""
        if progress == 100:
            self.btn_convert.setText("Convirtiendo... Completado")
        else:
            self.btn_convert.setText(f"Convirtiendo... {progress}%")
    
    def _on_conversion_finished(self, success: bool, message: str) -> None:
        """Handle conversion completion"""
        # Always reset button state regardless of success or failure
        self.btn_convert.setText("Convertir")
        self.btn_convert.setEnabled(True)
        
        if success:
            # Use custom success dialog
            dialog = SuccessDialog(self, message, self.output_path)
            dialog.exec()
        else:
            QMessageBox.critical(self, "Error", message)
    
    def refresh(self) -> None:
        self.btn_convert.setText("Convertir")
        self.btn_convert.setEnabled(True)
        self.file_info_panel.setVisible(False)
        self.input_edit.clear()


