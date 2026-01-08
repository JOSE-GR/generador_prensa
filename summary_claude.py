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
def detectar_idioma(texto: str) -> str:
    """
    Heurística simple ES vs EN (sin librerías extra).
    IMPORTANTE: evaluar solo una muestra corta para evitar "contaminación" del PDF.
    """
    t = (texto or "").strip().lower()
    muestra = (" " + t[:600] + " ")  # usar solo los primeros ~600 chars

    marcadores_es = [" el ", " la ", " de ", " que ", " y ", " en ", " los ", " las ", " por ", " para ", " del ", " al "]
    marcadores_en = [" the ", " and ", " of ", " to ", " in ", " for ", " with ", " on ", " from ", " by "]

    score_es = sum(muestra.count(m) for m in marcadores_es) + sum(1 for ch in muestra if ch in "áéíóúñ¿¡")
    score_en = sum(muestra.count(m) for m in marcadores_en)

    # Si hay señales fuertes de inglés, forzar EN
    if score_en > score_es:
        return "en"
    # Caso contrario, ES por defecto
    return "es"


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

    # Si el modelo devolvió más de un párrafo, nos quedamos con el primero
    r = r.split("\n\n")[0].strip()

    return r


def resumir_con_claude(texto: str, titulo: str = "") -> str:
    """
    Resume manteniendo el idioma original (sin traducir).
    Regla práctica:
    - Detectamos idioma con el título (si existe), si no, con el inicio del texto.
    """
    base_idioma = (titulo or texto or "")
    idioma = detectar_idioma(base_idioma)

    prompt = (
        "Eres un asistente que redacta resúmenes para un reporte interno de prensa.\n\n"
        "Reglas obligatorias:\n"
        "1) Escribe el resumen en el MISMO idioma del artículo. No traduzcas.\n"
        "2) Devuelve SOLO un párrafo (sin título, sin viñetas, sin encabezados).\n"
        "3) No incluyas prefacios ni frases meta como: \"Here's a summary\", \"Here is\", \"Resumen:\", "
        "\"A continuación\", \"In conclusion\", etc.\n"
        "4) Extensión objetivo: 110–120 palabras.\n"
        "5) Enfócate en hechos: qué pasó, quién, dónde, cuándo, cifras clave y contexto mínimo.\n\n"
        f"Idioma a usar: {'Español' if idioma=='es' else 'Inglés'}.\n"
        f"TÍTULO: {titulo}\n"
        "ARTÍCULO:\n"
        f"{texto}"
    )

    body = {
        "model": MODEL,
        "max_tokens": 300,
        "temperature": 0.3,
        "messages": [{"role": "user", "content": prompt}],
    }

    resp = httpx.post(API_URL, headers=HEADERS, json=body, timeout=60)

    if resp.status_code == 200:
        data = resp.json()
        resumen = data["content"][0]["text"].strip()
        return limpiar_prefacio(resumen)

    if resp.status_code == 401:
        raise Exception("401 autenticación: la x-api-key es inválida o no se envió (revisa Secrets/.env).")
    if resp.status_code == 403:
        raise Exception(
            f"403 acceso denegado al modelo '{MODEL}'. Prueba con 'claude-3-haiku-20240307' "
            "o configura ANTHROPIC_MODEL a un modelo disponible para tu cuenta."
        )

    raise Exception(f"Error al llamar a la API: {resp.status_code} - {resp.text}")