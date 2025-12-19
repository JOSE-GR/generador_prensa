Generador de Reporte de Prensa

Este repositorio contiene un generador automático de reportes de prensa desarrollado en Python, con una interfaz web en Streamlit, que permite procesar PDFs de prensa internacional, detectar noticias, generar resúmenes automáticos y exportar un reporte final en formato Word con formato institucional.

El proyecto está diseñado para facilitar y estandarizar el flujo de análisis de prensa, reduciendo tiempos manuales y errores de formato.


Arquitectura general del proyecto

El proyecto está organizado de forma modular, separando claramente la lógica de análisis, la generación de reportes y la interfaz de usuario.
prensa_pro/
│
├── app_streamlit.py        # Interfaz web (Streamlit) y control del flujo completo
├── main.py                 # Lógica central de análisis del PDF
├── gen_reporte.py          # Generación del reporte final en Word
├── summary_claude.py       # Generación de resúmenes vía API de Anthropic (Claude)


Tecnologías utilizadas
-Python
-Streamlit (interfaz web)
-PyMuPDF (fitz) – lectura y análisis de PDFs
-python-docx – generación de documentos Word
-Anthropic Claude API – generación de resúmenes
-GitHub – control de versiones
-Streamlit Cloud – despliegue de la aplicación


Uso de la aplicación
1.- Acceder a la aplicación web.
2.- Subir el PDF de prensa o pegar la URL.
3.- Indicar si el PDF incluye portada.
4.- Detectar las noticias.
5.- Seleccionar las notas a resumir.
6.- Generar los resúmenes.
7.- Descargar el reporte final en Word.


Despliegue

La aplicación está desplegada en Streamlit Cloud y se actualiza automáticamente cada vez que se realiza un push al repositorio.