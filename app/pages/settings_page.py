from __future__ import annotations

import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFormLayout, QLineEdit, QPushButton, QFileDialog, QCheckBox
from PyQt6.QtCore import QSettings, Qt


class SettingsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("SettingsPage")
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Configuración")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignVCenter)
        form.setVerticalSpacing(12)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form.setHorizontalSpacing(16)
        
        self.default_dir = QLineEdit()
        self.default_dir.setText(self._load_download_dir())
        btn = QPushButton("Cambiar…")
        btn.clicked.connect(self._choose_dir)
        row = QWidget()
        from PyQt6.QtWidgets import QHBoxLayout
        r = QHBoxLayout(row)
        r.addWidget(self.default_dir, 1)
        r.addWidget(btn)
        
        # Crear etiqueta con alineación específica para "Carpeta por defecto"
        carpeta_label = QLabel("Carpeta por defecto")
        carpeta_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        carpeta_label.setFixedHeight(42)  # Match input height for perfect alignment
        form.addRow(carpeta_label, row)

        # Checkbox: descargar solo 1 video (sin playlist)
        self.chk_single = QCheckBox("Descargar solo 1 video (ignorar playlist)")
        self.chk_single.setChecked(self._load_no_playlist())
        self.chk_single.toggled.connect(self._on_toggle_single)
        
        # Crear contenedor para checkbox que coincida con el ancho del campo de arriba
        checkbox_row = QHBoxLayout()
        checkbox_row.addWidget(self.chk_single)
        checkbox_row.addStretch()  # Espacio flexible para igualar el ancho
        checkbox_wrapper = QWidget()
        checkbox_wrapper.setLayout(checkbox_row)
        
        # Crear etiqueta con alineación específica para "Modo descarga"
        modo_label = QLabel("Modo descarga")
        modo_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        modo_label.setFixedHeight(42)  # Match input height for perfect alignment
        form.addRow(modo_label, checkbox_wrapper)
        
        # ===== CONFIGURACIONES DE ALERTAS =====
        # Checkbox: mostrar alertas visuales
        self.chk_visual_alerts = QCheckBox("Mostrar alertas visuales cuando termine la descarga")
        self.chk_visual_alerts.setChecked(self._load_visual_alerts())
        self.chk_visual_alerts.toggled.connect(self._on_toggle_visual_alerts)
        
        visual_alerts_row = QHBoxLayout()
        visual_alerts_row.addWidget(self.chk_visual_alerts)
        visual_alerts_row.addStretch()
        visual_alerts_wrapper = QWidget()
        visual_alerts_wrapper.setLayout(visual_alerts_row)
        
        alertas_label = QLabel("Notificaciones")
        alertas_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        alertas_label.setFixedHeight(42)
        form.addRow(alertas_label, visual_alerts_wrapper)
        
        # Checkbox: reproducir sonido de notificación
        self.chk_sound_alerts = QCheckBox("Reproducir sonido de notificación")
        self.chk_sound_alerts.setChecked(self._load_sound_alerts())
        self.chk_sound_alerts.toggled.connect(self._on_toggle_sound_alerts)
        
        sound_alerts_row = QHBoxLayout()
        sound_alerts_row.addWidget(self.chk_sound_alerts)
        sound_alerts_row.addStretch()
        sound_alerts_wrapper = QWidget()
        sound_alerts_wrapper.setLayout(sound_alerts_row)
        
        sonido_label = QLabel("Sonido")
        sonido_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        sonido_label.setFixedHeight(42)
        form.addRow(sonido_label, sound_alerts_wrapper)
        
        # ===== CONFIGURACIÓN DE DESCARGA =====
        # Checkbox: saltar verificación de formatos
        self.chk_skip_format_check = QCheckBox("Saltar verificación de formatos (descarga más rápida)")
        self.chk_skip_format_check.setChecked(self._load_skip_format_check())
        self.chk_skip_format_check.toggled.connect(self._on_toggle_skip_format_check)
        
        # Checkbox: verificación en segundo plano
        self.chk_background_check = QCheckBox("Verificación de formatos en segundo plano")
        self.chk_background_check.setChecked(self._load_background_format_check())
        self.chk_background_check.toggled.connect(self._on_toggle_background_format_check)
        
        format_check_row = QHBoxLayout()
        format_check_row.addWidget(self.chk_skip_format_check)
        format_check_row.addStretch()
        format_check_wrapper = QWidget()
        format_check_wrapper.setLayout(format_check_row)
        
        format_check_label = QLabel("Optimización")
        format_check_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        format_check_label.setFixedHeight(42)
        form.addRow(format_check_label, format_check_wrapper)
        
        # Segunda fila para verificación en segundo plano
        background_check_row = QHBoxLayout()
        background_check_row.addWidget(self.chk_background_check)
        background_check_row.addStretch()
        background_check_wrapper = QWidget()
        background_check_wrapper.setLayout(background_check_row)
        
        background_check_label = QLabel("Verificación")
        background_check_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        background_check_label.setFixedHeight(42)
        form.addRow(background_check_label, background_check_wrapper)
        
        layout.addLayout(form)

        layout.addStretch(1)

    def _choose_dir(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta", self.default_dir.text())
        if d:
            self.default_dir.setText(d)
            self._save_download_dir(d)

    # Settings helpers
    def _settings(self) -> QSettings:
        return QSettings("AudioHub", "AudioHubApp")

    def _load_download_dir(self) -> str:
        s = self._settings()
        val = s.value("downloadDir", type=str)
        if not val:
            val = os.path.join(os.path.expanduser("~"), "Downloads")
        return val

    def _save_download_dir(self, path: str) -> None:
        s = self._settings()
        s.setValue("downloadDir", path)
        s.sync()

    def _load_no_playlist(self) -> bool:
        s = self._settings()
        val = s.value("noPlaylist", True)
        # QSettings puede devolver str("true"/"false"). Normalizamos a bool.
        if isinstance(val, str):
            return val.lower() in ("1", "true", "yes", "on")
        if isinstance(val, (int, bool)):
            return bool(val)
        return True

    def _save_no_playlist(self, enabled: bool) -> None:
        s = self._settings()
        s.setValue("noPlaylist", enabled)
        s.sync()

    def _on_toggle_single(self, checked: bool) -> None:
        self._save_no_playlist(checked)
    
    # ===== MÉTODOS PARA CONFIGURACIÓN DE ALERTAS =====
    def _load_visual_alerts(self) -> bool:
        s = self._settings()
        val = s.value("showVisualAlerts", True)
        if isinstance(val, str):
            return val.lower() in ("1", "true", "yes", "on")
        if isinstance(val, (int, bool)):
            return bool(val)
        return True
    
    def _save_visual_alerts(self, enabled: bool) -> None:
        s = self._settings()
        s.setValue("showVisualAlerts", enabled)
        s.sync()
    
    def _on_toggle_visual_alerts(self, checked: bool) -> None:
        self._save_visual_alerts(checked)
    
    def _load_sound_alerts(self) -> bool:
        s = self._settings()
        val = s.value("playSoundAlerts", True)
        if isinstance(val, str):
            return val.lower() in ("1", "true", "yes", "on")
        if isinstance(val, (int, bool)):
            return bool(val)
        return True
    
    def _save_sound_alerts(self, enabled: bool) -> None:
        s = self._settings()
        s.setValue("playSoundAlerts", enabled)
        s.sync()
    
    def _on_toggle_sound_alerts(self, checked: bool) -> None:
        self._save_sound_alerts(checked)
    
    # ===== MÉTODOS PARA CONFIGURACIÓN DE DESCARGA =====
    def _load_skip_format_check(self) -> bool:
        s = self._settings()
        val = s.value("skipFormatCheck", False)
        if isinstance(val, str):
            return val.lower() in ("1", "true", "yes", "on")
        if isinstance(val, (int, bool)):
            return bool(val)
        return False
    
    def _save_skip_format_check(self, enabled: bool) -> None:
        s = self._settings()
        s.setValue("skipFormatCheck", enabled)
        s.sync()
    
    def _on_toggle_skip_format_check(self, checked: bool) -> None:
        self._save_skip_format_check(checked)
    
    def _load_background_format_check(self) -> bool:
        s = self._settings()
        val = s.value("backgroundFormatCheck", True)
        if isinstance(val, str):
            return val.lower() in ("1", "true", "yes", "on")
        if isinstance(val, (int, bool)):
            return bool(val)
        return True
    
    def _save_background_format_check(self, enabled: bool) -> None:
        s = self._settings()
        s.setValue("backgroundFormatCheck", enabled)
        s.sync()
    
    def _on_toggle_background_format_check(self, checked: bool) -> None:
        self._save_background_format_check(checked)


