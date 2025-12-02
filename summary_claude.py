import os
import httpx
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st

# Cargar .env de forma robusta (funciona en Codespaces, CLI, etc.)
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# Cargar API key desde .env (local) o desde secrets de Streamlit Cloud
API_KEY = (
    os.getenv("ANTHROPIC_API_KEY")           # local, usando archivo .env
    or st.secrets.get("ANTHROPIC_API_KEY")   # en despliegue (Streamlit Cloud)
)

if not API_KEY:
    raise RuntimeError(
        "No se encontró ANTHROPIC_API_KEY ni en .env ni en st.secrets. "
        "Define la API en tu archivo .env (local) o en los Secrets de Streamlit Cloud."
    )


API_URL = "https://api.anthropic.com/v1/messages"

# Permite sobreescribir por variable de entorno; usa Haiku por defecto (Opus suele requerir acceso especial)
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-haiku-20241022")

HEADERS = {
    "x-api-key": API_KEY,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json",
}

def resumir_con_claude(texto: str) -> str:
    prompt = (
        "Write a neutral, concise summary in English of the following press article "
        "in about 100 to 130 words. "
        "Do NOT include phrases like 'Here is a summary' or 'In conclusion'; "
        "start directly with the content of the summary.\n\n"
        f"{texto}"
    )
    ...

    body = {
        "model": MODEL,
        "max_tokens": 300,
        "temperature": 0.3,
        "messages": [{"role": "user", "content": prompt}],
    }

    resp = httpx.post(API_URL, headers=HEADERS, json=body, timeout=60)

    if resp.status_code == 200:
        data = resp.json()
        # Formato del endpoint /v1/messages
        return data["content"][0]["text"].strip()

    # Mensajes de error más claros para 401/403
    if resp.status_code == 401:
        raise Exception("401 autenticación: la x-api-key es inválida o no se envió (revisa .env y load_dotenv).")
    if resp.status_code == 403:
        raise Exception(
            f"403 acceso denegado al modelo '{MODEL}'. Prueba con 'claude-3-haiku-20240307' "
            "o configura ANTHROPIC_MODEL a un modelo disponible para tu cuenta."
        )

    # Otros casos
    raise Exception(f"Error al llamar a la API: {resp.status_code} - {resp.text}")
