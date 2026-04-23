# Generador de Reporte de Prensa

Herramienta desarrollada durante el **Servicio Social en el Banco de México**. Automatiza el flujo completo de análisis de prensa internacional: desde la lectura de PDFs hasta la generación de un reporte institucional en Word, utilizando la **API de Anthropic (Claude)** para la generación de resúmenes.

> 🔒 La aplicación tiene acceso restringido mediante contraseña.

---

## Estructura del proyecto

```
prensa_pro/
├── app_streamlit.py         # Interfaz web y orquestación del flujo completo
├── main.py                  # Prototipo inicial: análisis de PDF por consola
├── gen_reporte.py           # Generación del Word (versión standalone)
├── summary_claude.py        # Módulo de resúmenes vía API de Anthropic
├── resumenes_aprobados.json # Archivo temporal generado en ejecución
├── logo_bx.png              # Logo institucional para el encabezado del Word
├── banner_bx.png            # Banner de la interfaz web
├── Logobm.svg.png           # Marca de agua del fondo de la app
├── requirements.txt
└── README.md
```

---

## Flujo de datos

```
PDF (subido por el usuario)
        │
        ▼
[app_streamlit.py]
        │
        ├──► detectar_titulos()            → Extrae títulos por fuente/tamaño con PyMuPDF
        │         └──► obtener_titulos_portada()  → Enriquece con títulos completos del índice
        │
        ├──► extraer_noticias_completas()  → Delimita páginas por noticia y extrae texto
        │
        ├──► separar_titulo_y_medio()      → Separa "Título, Medio" en campos distintos
        │
        ├──► resumir_con_claude()          → Detecta idioma → genera prompt → llama a la API
        │
        └──► generar_reporte_word_en_memoria() → Word en RAM → descarga directa
```

---

## Descripción técnica por módulo

### `summary_claude.py` — Integración con la API de Anthropic

- **`detectar_idioma(texto)`** — Heurística léxica que compara marcadores frecuentes en español e inglés para determinar el idioma del texto sin dependencias externas.
- **`_generar_prompt(texto, idioma_forzado)`** — Prompt bilingüe con reglas estrictas: un solo párrafo, sin prefacios, 110–120 palabras, enfocado en hechos.
- **`resumir_con_claude(texto, titulo)`** — Lógica de dos intentos: si el resumen devuelto no está en el idioma esperado, reintenta forzando el idioma correcto.

La autenticación carga `ANTHROPIC_API_KEY` desde `.env` en local o desde `st.secrets` en Streamlit Cloud.

---

### `app_streamlit.py` — Interfaz web

- **Control de acceso** con `hmac.compare_digest()` (comparación en tiempo constante).
- **`detectar_titulos()`** — Analiza spans de PyMuPDF buscando texto en negrita con tamaño ≥ 12pt y longitud ≥ 25 caracteres. Enriquece los títulos detectados con el nombre del medio (FT, WSJ, Bloomberg, etc.) tomándolo de la página de índice del PDF.
- **`generar_reporte_word_en_memoria()`** — Genera el Word completamente en RAM (`io.BytesIO`), sin escribir a disco. Si se proporciona una URL del PDF, los títulos se convierten en hipervínculos que apuntan a la página exacta de cada noticia.
- El estado entre pasos se persiste en `st.session_state`.

---

### `gen_reporte.py` — Formato institucional del Word

Aplica el formato del reporte: encabezado con logo y fecha, nombre de la gerencia, título principal en Arial 28.5pt, y resúmenes en Times New Roman 11pt con interlineado simple y texto justificado. Nombra el archivo automáticamente como `"reporte de prensa DD de mes.docx"`.

---

## Tecnologías utilizadas

| Librería | Uso |
|---|---|
| `streamlit` | Interfaz web |
| `PyMuPDF (fitz)` | Extracción de texto y análisis tipográfico del PDF |
| `python-docx` | Generación del Word con formato institucional |
| `httpx` | Llamadas HTTP a la API de Anthropic |
| `python-dotenv` | Variables de entorno en local |

---

La aplicación está desplegada en Streamlit Cloud y el acceso está restringido mediante contraseña
---

## Autor 👾

**JOSE-GR** — [@JOSE-GR](https://github.com/JOSE-GR)