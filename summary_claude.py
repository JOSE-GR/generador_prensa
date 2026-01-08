import os
import httpx
import re
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

# -----------------------------
# Detección de idioma (ES vs EN)
# -----------------------------
def detectar_idioma(texto: str) -> str:
    """
    Heurística simple pero más robusta: compara señales ES vs EN.
    Devuelve: 'es' o 'en'
    """
    t = (texto or "").lower()

    # Señales ES
    marcadores_es = [
        " el ", " la ", " de ", " que ", " y ", " en ", " los ", " las ",
        " por ", " para ", " del ", " al ", " una ", " un ", " se ", " con ",
        " como ", " más ", " menos ", " también "
    ]
    score_es = sum(t.count(m) for m in marcadores_es) + sum(1 for ch in t if ch in "áéíóúñ¿¡")

    # Señales EN
    marcadores_en = [
        " the ", " and ", " of ", " to ", " in ", " for ", " on ", " with ",
        " as ", " by ", " from ", " that ", " this ", " it ", " at ", " were ",
        " has ", " have ", " said ", " will ", " would "
    ]
    score_en = sum(t.count(m) for m in marcadores_en)

    # Decisión por diferencia (evita falsos positivos por ruido)
    if score_en >= score_es + 3:
        return "en"
    if score_es >= score_en + 3:
        return "es"

    # Empate: fallback por caracteres (acentos suelen decidir)
    return "es" if any(ch in t for ch in "áéíóúñ¿¡") else "en"


def limpiar_prefacio(resumen: str) -> str:
    """
    Quita prefacios tipo 'Here's a summary...' y deja solo el primer párrafo.
    """
    r = (resumen or "").strip()

    # Prefacios comunes EN
    r = re.sub(r"^(here(?:'|’)s|here is)\b.*?:\s*", "", r, flags=re.IGNORECASE)
    r = re.sub(r"^.*summary.*words.*?:\s*", "", r, flags=re.IGNORECASE)

    # Prefacios comunes ES
    r = re.sub(r"^(resumen|aquí (?:va|tienes) un resumen|a continuación)\b.*?:\s*", "", r, flags=re.IGNORECASE)

    # Quedarnos con el primer párrafo
    r = r.split("\n\n")[0].strip()
    return r


def _generar_prompt(texto: str, idioma_forzado: str | None = None) -> str:
    """
    Prompt neutro (ES/EN) para minimizar sesgo de idioma.
    Si idioma_forzado se pasa, obliga explícitamente 'es' o 'en'.
    """
    if idioma_forzado == "en":
        lang_line = "Write the summary in English. Do NOT translate into Spanish."
    elif idioma_forzado == "es":
        lang_line = "Escribe el resumen en Español. No traduzcas al inglés."
    else:
        lang_line = "Write the summary in the SAME language as the input text. Do NOT translate."

    prompt = (
        "You are an assistant that writes summaries for an internal press report.\n"
        "Eres un asistente que redacta resúmenes para un reporte interno de prensa.\n\n"
        "Mandatory rules / Reglas obligatorias:\n"
        f"1) {lang_line}\n"
        "2) Return ONLY one paragraph (no title, no bullets, no headings).\n"
        "   Devuelve SOLO un párrafo (sin título, sin viñetas, sin encabezados).\n"
        "3) Do NOT include meta phrases like: \"Here's a summary\", \"Here is\", \"Resumen:\", "
        "\"A continuación\", \"In conclusion\", etc.\n"
        "4) Target length: 110–120 words.\n"
        "5) Focus on facts: what happened, who, where, when, key figures, minimal context.\n\n"
        "TEXT / TEXTO:\n"
        f"{texto}"
    )
    return prompt


def resumir_con_claude(texto: str) -> str:
    """
    1) Detecta idioma probable del texto (es/en).
    2) Pide resumen en el mismo idioma (sin sesgo fuerte).
    3) Si el resultado sale en idioma distinto, reintenta 1 vez forzando el idioma correcto.
    """
    idioma_texto = detectar_idioma(texto)

    # 1er intento (no forzado, solo "mismo idioma")
    prompt = _generar_prompt(texto, idioma_forzado=None)

    body = {
        "model": MODEL,
        "max_tokens": 300,
        "temperature": 0.3,
        "messages": [{"role": "user", "content": prompt}],
    }

    resp = httpx.post(API_URL, headers=HEADERS, json=body, timeout=60)

    if resp.status_code == 200:
        data = resp.json()
        resumen = limpiar_prefacio(data["content"][0]["text"].strip())

        # Validación: ¿salió en el idioma correcto?
        idioma_resumen = detectar_idioma(resumen)
        if idioma_resumen != idioma_texto:
            # Reintento forzando el idioma del texto
            prompt2 = _generar_prompt(texto, idioma_forzado=idioma_texto)
            body["messages"] = [{"role": "user", "content": prompt2}]
            resp2 = httpx.post(API_URL, headers=HEADERS, json=body, timeout=60)

            if resp2.status_code == 200:
                data2 = resp2.json()
                resumen2 = limpiar_prefacio(data2["content"][0]["text"].strip())
                return resumen2

        return resumen

    if resp.status_code == 401:
        raise Exception("401 autenticación: la x-api-key es inválida o no se envió (revisa Secrets/.env).")
    if resp.status_code == 403:
        raise Exception(
            f"403 acceso denegado al modelo '{MODEL}'. Prueba con 'claude-3-haiku-20240307' "
            "o configura ANTHROPIC_MODEL a un modelo disponible para tu cuenta."
        )

    raise Exception(f"Error al llamar a la API: {resp.status_code} - {resp.text}")