from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import json
import os

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)


PRODUCERS: dict[str, dict[str, Any]] = {}
FORM_STATE: dict[str, dict[str, Any]] = {}
ALERTS: list[dict[str, Any]] = []
MESSAGES: list[dict[str, Any]] = []

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
MML_PROVIDER = os.getenv("MML_PROVIDER", "mock")

PROMPTS = {
    "formulario": (
        "Eres un asistente agrónomo por WhatsApp. Pregunta natural y breve. "
        "Extrae datos para completar el formulario. "
        "Devuelve SOLO JSON válido con las claves: "
        "role, respuesta_chat, acciones{actualizar_formulario,alerta,log}, "
        "estado{formulario_completo,confianza}."
    ),
    "consulta": (
        "Responde usando SOLO la información del contexto. "
        "Si falta información, pide una sola aclaración. "
        "Devuelve SOLO JSON válido con las claves: "
        "role, respuesta_chat, acciones{actualizar_formulario,alerta,log}, "
        "estado{formulario_completo,confianza}."
    ),
    "intervencion": (
        "Analiza persistencia o riesgo con el historial. "
        "Si amerita, genera alerta. "
        "Devuelve SOLO JSON válido con las claves: "
        "role, respuesta_chat, acciones{actualizar_formulario,alerta,log}, "
        "estado{formulario_completo,confianza}."
    ),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_or_create_producer(phone: str) -> dict[str, Any]:
    if phone not in PRODUCERS:
        PRODUCERS[phone] = {
            "id": len(PRODUCERS) + 1,
            "phone": phone,
            "zone": None,
            "preferred_language": "es",
            "main_crops": [],
        }
    return PRODUCERS[phone]


def get_form_state(phone: str) -> dict[str, Any]:
    if phone not in FORM_STATE:
        FORM_STATE[phone] = {
            "cultivo": None,
            "sintoma": None,
            "inicio_problema": None,
            "foto_recibida": False,
        }
    return FORM_STATE[phone]


def recent_chat(phone: str, limit: int = 6) -> list[str]:
    rows = [m for m in MESSAGES if m["phone"] == phone]
    rows = rows[-limit:]
    return [f'{row["from"]}: {row["text"]}' for row in rows]


def build_context(role: str, phone: str, last_user_message: str) -> dict[str, Any]:
    producer = get_or_create_producer(phone)
    form_state = get_form_state(phone)
    context: dict[str, Any] = {
        "role": role,
        "producer": producer,
        "form_state": form_state,
        "recent_chat": recent_chat(phone),
        "weekly_summary": None,
        "last_user_message": last_user_message,
    }

    if role == "consulta":
        context["weekly_summary"] = "7d: sin datos suficientes registrados."
    if role == "intervencion":
        context["recent_chat"] = []
        context["weekly_summary"] = "7d: sin datos suficientes registrados."

    return context


def mock_mml_response(role: str) -> dict[str, Any]:
    if role == "consulta":
        return {
            "role": "consulta",
            "respuesta_chat": (
                "Con la información actual registrada, puedo ayudarte si me confirmas "
                "qué cultivo estás trabajando."
            ),
            "acciones": {"actualizar_formulario": {}, "alerta": None, "log": "Mock consulta"},
            "estado": {"formulario_completo": True, "confianza": 0.4},
        }
    if role == "intervencion":
        return {
            "role": "intervencion",
            "respuesta_chat": (
                "Detecto que necesitas apoyo técnico. Coordinaré una revisión para tu "
                "cultivo."
            ),
            "acciones": {
                "actualizar_formulario": {},
                "alerta": {
                    "nivel": "medio",
                    "motivo": "Revision requerida",
                    "accion_recomendada": "Contacto tecnico",
                },
                "log": "Mock intervencion",
            },
            "estado": {"formulario_completo": True, "confianza": 0.6},
        }
    return {
        "role": "formulario",
        "respuesta_chat": "¿Qué cultivo estás trabajando?",
        "acciones": {
            "actualizar_formulario": {"cultivo": None},
            "alerta": None,
            "log": "Mock formulario",
        },
        "estado": {"formulario_completo": False, "confianza": 0.35},
    }


def call_groq(role: str, context: dict[str, Any]) -> dict[str, Any]:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return mock_mml_response(role)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": PROMPTS[role]},
            {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
        "max_tokens": 300,
    }
    response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return mock_mml_response(role)


def run_mml(role: str, context: dict[str, Any]) -> dict[str, Any]:
    if MML_PROVIDER == "groq":
        return call_groq(role, context)
    return mock_mml_response(role)


def apply_model_actions(phone: str, model_output: dict[str, Any]) -> dict[str, Any]:
    actions = model_output.get("acciones", {})
    updates = actions.get("actualizar_formulario", {})
    if updates:
        form = get_form_state(phone)
        for key, value in updates.items():
            if value is not None:
                form[key] = value
    alert = actions.get("alerta")
    if alert:
        ALERTS.append({"phone": phone, "alert": alert, "time": utc_now()})
    return model_output


@app.get("/health")
def health() -> Any:
    return jsonify({"status": "ok", "time": utc_now()})


@app.post("/agent")
def agent() -> Any:
    payload = request.get_json(force=True)
    role = payload.get("role", "formulario")
    phone = payload.get("phone")
    message = payload.get("message", "")

    if role not in PROMPTS:
        return jsonify({"error": "role invalido"}), 400

    if not phone:
        return jsonify({"error": "phone requerido"}), 400

    MESSAGES.append({"phone": phone, "from": "user", "text": message, "time": utc_now()})

    context = build_context(role, phone, message)
    model_output = run_mml(role, context)
    model_output = apply_model_actions(phone, model_output)

    MESSAGES.append(
        {
            "phone": phone,
            "from": "assistant",
            "text": model_output["respuesta_chat"],
            "time": utc_now(),
        }
    )

    return jsonify({"context": context, "model_output": model_output})


@app.post("/form/update")
def update_form() -> Any:
    payload = request.get_json(force=True)
    phone = payload.get("phone")
    updates = payload.get("updates", {})

    if not phone:
        return jsonify({"error": "phone requerido"}), 400

    form = get_form_state(phone)
    for key, value in updates.items():
        if value is not None:
            form[key] = value

    return jsonify({"status": "ok", "form_state": form})


@app.post("/alert")
def create_alert() -> Any:
    payload = request.get_json(force=True)
    phone = payload.get("phone")
    alert = payload.get("alert")

    if not phone or not alert:
        return jsonify({"error": "phone y alert requeridos"}), 400

    record = {"phone": phone, "alert": alert, "time": utc_now()}
    ALERTS.append(record)
    return jsonify({"status": "ok", "alert": record})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
