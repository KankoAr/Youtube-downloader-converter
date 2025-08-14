# PowerShell script para automatizar el proceso de release
# Ejecutar como administrador si es necesario

param(
    [Parameter(Mandatory=$true)]
    [string]$Version,
    
    [Parameter(Mandatory=$false)]
    [string]$Message = "Release $Version"
)

Write-Host "🚀 Iniciando proceso de release para versión $Version" -ForegroundColor Green

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "main.py")) {
    Write-Error "❌ No se encontró main.py. Ejecuta este script desde el directorio raíz del proyecto."
    exit 1
}

# Verificar que git está disponible
try {
    git --version | Out-Null
} catch {
    Write-Error "❌ Git no está disponible. Instala Git y asegúrate de que esté en el PATH."
    exit 1
}

# Verificar que Python está disponible
try {
    python --version | Out-Null
} catch {
    Write-Error "❌ Python no está disponible. Instala Python y asegúrate de que esté en el PATH."
    exit 1
}

# Limpiar builds anteriores
Write-Host "🧹 Limpiando builds anteriores..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "__pycache__") { Remove-Item -Recurse -Force "__pycache__" }

# Instalar dependencias si es necesario
Write-Host "📦 Instalando dependencias..." -ForegroundColor Yellow
pip install -r requirements.txt
pip install pyinstaller

# Build del ejecutable
Write-Host "🔨 Compilando ejecutable..." -ForegroundColor Yellow
pyinstaller --clean YouTube_Downloader.spec

if (-not (Test-Path "dist\YouTube_Downloader.exe")) {
    Write-Error "❌ La compilación falló. Revisa los errores arriba."
    exit 1
}

Write-Host "✅ Ejecutable compilado exitosamente!" -ForegroundColor Green

# Verificar estado de git
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "📝 Cambios detectados en git:" -ForegroundColor Yellow
    Write-Host $gitStatus
    
    # Agregar todos los cambios
    git add .
    git commit -m "Build for release $Version"
    Write-Host "✅ Cambios committeados" -ForegroundColor Green
}

# Crear tag
Write-Host "🏷️ Creando tag v$Version..." -ForegroundColor Yellow
git tag -a "v$Version" -m "Release $Version"
Write-Host "✅ Tag v$Version creado" -ForegroundColor Green

# Push a GitHub
Write-Host "🚀 Enviando a GitHub..." -ForegroundColor Yellow
git push origin main
git push origin "v$Version"
Write-Host "✅ Código enviado a GitHub" -ForegroundColor Green

# Información final
Write-Host ""
Write-Host "🎉 Release $Version completado exitosamente!" -ForegroundColor Green
Write-Host ""
Write-Host "📁 El ejecutable está en: dist\YouTube_Downloader.exe" -ForegroundColor Cyan
Write-Host "🌐 GitHub Actions se ejecutará automáticamente para crear la release" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 Próximos pasos:" -ForegroundColor Yellow
Write-Host "1. Ve a https://github.com/TU_USUARIO/youtube-downloader-pyqt6/releases" -ForegroundColor White
Write-Host "2. Verifica que la release se creó automáticamente" -ForegroundColor White
Write-Host "3. El ejecutable estará disponible para descarga" -ForegroundColor White
Write-Host ""
Write-Host "💡 Para crear una nueva release, ejecuta: .\release.ps1 -Version X.Y.Z" -ForegroundColor Cyan
