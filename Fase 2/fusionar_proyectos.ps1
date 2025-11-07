# === 1) Rutas origen (ajústalas si hace falta) ===
$desktopSrc = "C:\Users\vicen\OneDrive\Escritorio\app\app_escritorio"
$webSrc     = "C:\Users\vicen\OneDrive\Documentos\GitHub\MentesBeta\Fase 2\incidex\incidex"

# === 2) Destinos ===
$root = "C:\Users\vicen\OneDrive\Documentos\GitHub\MentesBeta\Fase 2\incidex"
$desktopDst = Join-Path $root "desktop"
$webDst     = Join-Path $root "web"
$sharedDst  = Join-Path $root "shared_assets"

# === 3) Crear carpetas destino ===
New-Item -ItemType Directory -Force -Path $desktopDst | Out-Null
New-Item -ItemType Directory -Force -Path $webDst     | Out-Null
New-Item -ItemType Directory -Force -Path $sharedDst  | Out-Null

# === 4) Copiar proyecto ESCRITORIO (sin .venv ni __pycache__) ===
robocopy $desktopSrc $desktopDst /E /XD ".venv" "__pycache__" "node_modules" "mysql_data" | Out-Null

# === 5) Copiar proyecto WEB (sin .venv ni __pycache__) ===
robocopy $webSrc $webDst /E /XD ".venv" "__pycache__" "node_modules" | Out-Null

# === 6) Mover logos compartidos ===
$logos = @("logo.png","HOME.png")
foreach ($lg in $logos) {
    $found = Get-ChildItem -Path $desktopSrc,$webSrc -Recurse -Filter $lg -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) { Copy-Item $found.FullName (Join-Path $sharedDst $lg) -Force }
}

# === 7) .gitignore raíz útil ===
$gitignore = @"
# Python
__pycache__/
*.pyc
*.pyo
*.pyd

# Virtualenvs
.venv*/
venv*/

# Entornos
.env
.env.*

# Logs y temporales
*.log
*.pid
*.sock

# Node
node_modules/

# OS
.DS_Store
Thumbs.db

# Docker y datos
mysql_data/
var/uploads/
"@
Set-Content -Path (Join-Path $root ".gitignore") -Value $gitignore -Encoding UTF8

# === 8) README raíz breve ===
$readme = @"
# Incidex (monorepo)

- **desktop/**: App de escritorio (PySide6).
- **web/**: App web (Flask).
- **shared_assets/**: Imágenes/recursos compartidos.

## Entornos
Crea entornos aislados:
- `python -m venv desktop/.venv-desktop`
- `python -m venv web/.venv-web`

## Instalación rápida
### Desktop
`cd desktop && .\.venv-desktop\Scripts\activate && pip install -r requirements.txt && python app.py`

### Web
`cd web && .\.venv-web\Scripts\activate && pip install -r requirements.txt && python .\src\presentation\web\app.py`
"@
Set-Content -Path (Join-Path $root "README.md") -Value $readme -Encoding UTF8

# === 9) Mensaje final ===
Write-Host ("Estructura unificada creada correctamente dentro de: " + $root) -ForegroundColor Green

