import os
import json
import logging

import google.generativeai as genai

log = logging.getLogger(__name__)

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise RuntimeError("Falta variable de entorno GEMINI_API_KEY para Gemini")

genai.configure(api_key=API_KEY)

_MODEL_NAME = "gemini-2.5-flash"


def suggest_ticket_metadata(*, title: str, description: str,
                            categories: list[dict],
                            priorities: list[dict],
                            departments: list[dict]) -> dict | None:
    """
    Llama a Gemini y pide que escoja category_id, priority_id y department_id.
    Devuelve un dict con esos campos y un campo 'reason' (texto).
    """
    options = {
        "categories": [{"id": c["id"], "name": c["name"]} for c in categories],
        "priorities": [{"id": p["id"], "name": p["name"]} for p in priorities],
        "departments": [{"id": d["id"], "name": d["name"]} for d in departments],
    }

    system_prompt = """
Eres un asistente para un sistema de tickets de soporte.

Tu tarea:
- Elegir la mejor CATEGORÍA, PRIORIDAD y DEPARTAMENTO para un ticket nuevo,
  usando SOLO los IDs que te doy en las listas.

Reglas:
- No inventes IDs ni nombres.
- Si tienes dudas, elige lo más razonable.
- Responde EXCLUSIVAMENTE con JSON válido, SIN texto extra.

Formato de respuesta:

{
  "category_id": <int>,
  "priority_id": <int>,
  "department_id": <int>,
  "reason": "breve explicación en español"
}
""".strip()

    user_prompt = f"""
Título: {title}

Descripción:
{description}

Opciones disponibles (JSON):
{json.dumps(options, ensure_ascii=False)}
""".strip()

    try:
        model = genai.GenerativeModel(_MODEL_NAME)
        resp = model.generate_content(
            [system_prompt, user_prompt],
            generation_config={"temperature": 0.3},
        )
        text = (resp.text or "").strip()
        text = text.strip("` \n")
        if text.lower().startswith("json"):
            text = text[4:].strip()
        return json.loads(text)
    except Exception as e:
        log.exception("Error llamando a Gemini: %s", e)
        return None
