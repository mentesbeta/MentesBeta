# Incidex (monorepo)

- **desktop/**: App de escritorio (PySide6).
- **web/**: App web (Flask).
- **shared_assets/**: ImÃ¡genes/recursos compartidos.

## Entornos
Crea entornos aislados:
- python -m venv desktop/.venv-desktop
- python -m venv web/.venv-web

## InstalaciÃ³n rÃ¡pida
### Desktop
cd desktop && .\.venv-desktop\Scripts\activate && pip install -r requirements.txt && python app.py

### Web
cd web && .\.venv-web\Scripts\activate && pip install -r requirements.txt && python .\src\presentation\web\app.py
