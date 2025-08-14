# 🔔 Sistema de Alertas de Descarga

## Nuevas Funcionalidades

### ¿Qué hay de nuevo?

Tu aplicación **Audio Hub** ahora incluye un sistema completo de notificaciones que te alertará cuando termine de descargar un video. Las alertas incluyen:

1. **🔔 Notificaciones del Sistema** - Aparecen en tu área de notificaciones de Windows
2. **🔊 Sonido de Notificación** - Reproduce un sonido del sistema cuando termina la descarga
3. **💬 Alerta Visual** - Muestra un mensaje emergente en la aplicación (se cierra automáticamente)

### Tipos de Notificaciones

#### 1. Notificación del Sistema Windows
- Aparece en la bandeja de notificaciones de Windows 10/11
- Muestra el título del video y el tamaño del archivo
- Dura 5 segundos
- Funciona con diferentes librerías de respaldo para máxima compatibilidad

#### 2. Sonido de Notificación
- Reproduce el sonido estándar de "información" de Windows
- También reproduce sonidos de error si hay problemas en la descarga

#### 3. Alerta Visual
- Aparece como un cuadro de diálogo no-modal
- Se auto-cierra después de 3 segundos
- No bloquea el uso de la aplicación

## ⚙️ Configuración

### Dónde Configurar las Alertas

1. Ve a la pestaña **"Configuración"** en tu aplicación
2. Encontrarás dos nuevas opciones:
   - ✅ **"Mostrar alertas visuales cuando termine la descarga"**
   - ✅ **"Reproducir sonido de notificación"**

### Configuraciones Disponibles

- **Alertas Visuales**: ON/OFF - Controla si aparece el mensaje emergente en la app
- **Sonido**: ON/OFF - Controla si reproduce sonidos de notificación
- **Notificaciones del Sistema**: Siempre activas (no se pueden desactivar)

## 📦 Instalación Opcional para Mejores Notificaciones

Para obtener notificaciones del sistema más avanzadas, puedes instalar librerías opcionales:

```bash
pip install -r notifications_requirements.txt
```

### Qué incluye:

- **plyer**: Notificaciones multiplataforma mejoradas
- **win10toast**: Notificaciones nativas de Windows 10/11 con mejores íconos

### Si NO instalas las librerías opcionales:
- Las notificaciones seguirán funcionando usando PowerShell como respaldo
- Puede que tarden un poco más en aparecer
- No afecta la funcionalidad principal

## 🎯 Cómo Funciona

1. **Durante la descarga**: Ves el progreso normal
2. **Al completarse**: 
   - 🔔 Aparece notificación en Windows
   - 🔊 Suena alerta (si está habilitada)
   - 💬 Se muestra mensaje en la app (si está habilitado)
3. **En caso de error**:
   - 🔊 Suena alerta de error (si está habilitada)

## 🛠️ Detalles Técnicos

### Jerarquía de Notificaciones del Sistema
1. **Intenta usar `plyer`** (si está instalado)
2. **Fallback a `win10toast`** (si está instalado)
3. **Último recurso: PowerShell** (siempre disponible en Windows)

### Configuraciones Guardadas
Todas las preferencias se guardan automáticamente en:
- `showVisualAlerts`: Controla alertas visuales
- `playSoundAlerts`: Controla sonidos de notificación

## ❓ Preguntas Frecuentes

**P: ¿Puedo desactivar todas las alertas?**
R: Puedes desactivar las visuales y sonidos, pero las notificaciones del sistema siempre aparecerán.

**P: ¿Funcionará sin instalar las librerías opcionales?**
R: Sí, usa PowerShell como respaldo y funciona perfectamente.

**P: ¿Las alertas bloquean la aplicación?**
R: No, todas las alertas son no-bloqueantes y la app sigue funcionando normalmente.

**P: ¿Qué pasa si minimizo la aplicación?**
R: Las notificaciones del sistema seguirán apareciendo aunque la app esté minimizada.

---

¡Disfruta de tus descargas con alertas inteligentes! 🎉
