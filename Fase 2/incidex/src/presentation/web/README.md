# Módulo Web de Incidex

Este módulo contiene las vistas, plantillas y controladores asociados a la aplicación web de Incidex.
Arquitectura basada en Blueprints de Flask:
- `public`: páginas públicas
- `auth`: autenticación
- `tickets`: gestión de incidencias

Arrancar el servidor FLASK_APP (desde ka raiz del proyecto ej: Fase 2\incidex)
Remove-Item Env:FLASK_APP -ErrorAction SilentlyContinue (si esta creada la variable de entorno)
$env:FLASK_APP = "src.presentation.web.app:app"

cd Fase 2\incidex
flask run