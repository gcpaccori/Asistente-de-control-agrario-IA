"""
Ejemplo de adaptador para integrar diferentes proveedores de LLM.
Este archivo muestra cómo conectar con Grok (xAI), OpenAI, y otros.
"""
from __future__ import annotations

import json
import os
from typing import Any

from flask import Flask, jsonify, request

app = Flask(__name__)

# Configuración desde variables de entorno
MML_PROVIDER = os.getenv("MML_PROVIDER", "xai")  # xai, openai, anthropic
XAI_API_KEY = os.getenv("XAI_API_KEY")
XAI_MODEL = os.getenv("XAI_MODEL", "grok-4-latest")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")


def call_xai_grok(system_prompt: str, context: dict[str, Any], max_tokens: int) -> str:
    """
    Llama a la API de Grok (xAI).
    Documentación: https://docs.x.ai/
    """
    import requests
    
    if not XAI_API_KEY:
        raise ValueError("XAI_API_KEY no está configurado")
    
    headers = {
        "Authorization": f"Bearer {XAI_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": XAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
        ],
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }
    
    response = requests.post(
        "https://api.x.ai/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    return content


def call_openai(system_prompt: str, context: dict[str, Any], max_tokens: int) -> str:
    """
    Llama a la API de OpenAI.
    Documentación: https://platform.openai.com/docs/api-reference
    """
    import requests
    
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY no está configurado")
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
        ],
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }
    
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    return content


def call_llm(system_prompt: str, context: dict[str, Any], max_tokens: int) -> str:
    """
    Llama al proveedor de LLM configurado.
    """
    if MML_PROVIDER == "xai":
        return call_xai_grok(system_prompt, context, max_tokens)
    elif MML_PROVIDER == "openai":
        return call_openai(system_prompt, context, max_tokens)
    else:
        raise ValueError(f"Proveedor no soportado: {MML_PROVIDER}")


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "provider": MML_PROVIDER}


@app.post("/chat")
def chat() -> dict[str, str]:
    """
    Endpoint compatible con el formato esperado por app.py.
    
    Request:
    {
        "system": "prompt del sistema",
        "context": {...},
        "max_tokens": 300
    }
    
    Response:
    {
        "content": "JSON string con la respuesta del modelo"
    }
    """
    try:
        payload = request.get_json(force=True)
        system_prompt = payload.get("system", "")
        context = payload.get("context", {})
        max_tokens = int(payload.get("max_tokens", 300))
        
        content = call_llm(system_prompt, context, max_tokens)
        
        return {"content": content}
    except Exception as e:
        return {"error": str(e)}, 500


if __name__ == "__main__":
    # Para desarrollo local
    port = int(os.getenv("PORT", "8001"))
    app.run(host="0.0.0.0", port=port, debug=True)
