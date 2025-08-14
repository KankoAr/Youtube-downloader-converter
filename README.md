# YouTube Downloader - Audio Hub

Una aplicación de escritorio moderna para descargar y convertir videos de YouTube a diferentes formatos de audio.

## 🚀 Características

- **Descarga de Videos**: Descarga videos de YouTube en la mejor calidad disponible
- **Conversión de Audio**: Convierte videos a MP3, WAV, FLAC y otros formatos
- **Interfaz Moderna**: UI intuitiva construida con PyQt6
- **Gestión de Descargas**: Control total sobre tus descargas
- **Configuraciones Personalizables**: Ajusta la calidad, formato y ubicación de descarga

## 📥 Descarga

### Versión Pre-compilada (Recomendado)
Descarga la última versión desde [Releases](https://github.com/KankoAr/Youtube-downloader-converter/releases)

1. Ve a la sección de Releases
2. Descarga `YouTube_Downloader.exe` (Windows)
3. Ejecuta el archivo directamente - no requiere instalación

### Desde Código Fuente
```bash
# Clona el repositorio
git clone https://github.com/KankoAr/Youtube-downloader-converter.git
cd Youtube-downloader-converter

# Instala dependencias
pip install -r requirements.txt

# Ejecuta la aplicación
python main.py
```

## 🛠️ Requisitos del Sistema

- **Windows 10/11** (64-bit)
- **Python 3.8+** (solo para desarrollo)
- **FFmpeg** (incluido en el ejecutable)

## 📋 Dependencias

- PyQt6 >= 6.6
- pydub >= 0.25.1
- ffmpeg-python >= 0.2.0
- requests >= 2.31.0
- yt-dlp >= 2024.4.9
- plyer >= 2.1.0
- win10toast >= 0.9

## 🔨 Compilación

### Build Local
```bash
# Usa el script de build
python build.py

# O manualmente con PyInstaller
pyinstaller --clean YouTube_Downloader.spec
```

### Build Automático con GitHub Actions
El proyecto incluye un workflow de GitHub Actions que:
1. Se ejecuta automáticamente al crear un tag
2. Compila el ejecutable en Windows
3. Crea una release con el .exe incluido

## 📱 Uso

1. **Iniciar Aplicación**: Ejecuta `YouTube_Downloader.exe`
2. **Pegar URL**: Copia y pega la URL del video de YouTube
3. **Seleccionar Formato**: Elige el formato de audio deseado
4. **Descargar**: Haz clic en "Descargar" y espera a que termine
5. **Encontrar Archivo**: Los archivos se guardan en la carpeta de descargas

## 🎯 Funciones Principales

### Página de Descargas
- Descarga directa de videos de YouTube
- Selección de calidad de audio
- Barra de progreso en tiempo real
- Historial de descargas

### Página de Conversión
- Conversión entre formatos de audio
- Lote de archivos
- Configuración de calidad

### Configuraciones
- Ubicación de descarga personalizable
- Configuración de notificaciones
- Preferencias de formato

## 🚀 Roadmap

- [ ] Soporte para múltiples plataformas (macOS, Linux)
- [ ] Descarga de playlists completas
- [ ] Editor de metadatos de audio
- [ ] Integración con servicios de música
- [ ] Modo oscuro/claro

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## ⚠️ Disclaimer

Esta aplicación es para uso personal y educativo. Respeta los derechos de autor y términos de servicio de YouTube. El desarrollador no se hace responsable del uso indebido de esta herramienta.

## 🆘 Soporte

Si encuentras algún problema:
1. Revisa los [Issues](https://github.com/KankoAr/Youtube-downloader-converter/issues) existentes
2. Crea un nuevo issue con detalles del problema
3. Incluye tu versión de Windows y logs de error si es posible

---

**¡Disfruta descargando tu música favorita! 🎵**


