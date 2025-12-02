
import fitz #importar módelulo de PDF
print ("el lector de pdf está instalado y funcionando")






def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    return full_text



# Cargar y extraer texto del PDF
pdf_path = "nov4.pdf"  # Cambia esto por el nombre de tu archivo PDF
texto = extract_text_from_pdf(pdf_path)
print(texto)  # Aquí ves el texto extraído

pdf_path = "nov4.pdf"  # Cambia esto si tu archivo se llama diferente

texto = extract_text_from_pdf(pdf_path)  # Usamos la función que definiste en Celda 21,10

print(texto[:1000])  # Mostramos los primeros 1000 caracteres del texto






pdf_path = "nov4.pdf"
doc = fitz.open(pdf_path)

page = doc.load_page(2)  # página 3
texto_dict = page.get_text("dict")
blocks = texto_dict["blocks"]

print(f"Spans detectados en página 3:\n")

for block in blocks:
    if block['type'] != 0:
        continue
    for line in block['lines']:
        for span in line['spans']:
            texto = span['text'].strip()
            if texto:
                print(f"Texto: '{texto}'")
                print(f"Fuente: {span['font']}")
                print(f"Tamaño: {span['size']}")
                print(f"Número de caracteres: {len(texto)}")
                print("---")


def detectar_titulos(pdf_path):
    import fitz

    doc = fitz.open(pdf_path)
    titulos = []
    textos_excluidos = {"Uso General", "Información"}

    # Empieza en la página 2 (índice 1) porque la 1 es la portada
    for page_num in range(1, doc.page_count):
        page = doc.load_page(page_num)
        texto_dict = page.get_text("dict")
        blocks = texto_dict["blocks"]

        titulo_encontrado = False

        for block in blocks:
            if block["type"] != 0:  # solo texto
                continue

            buffer_lineas = []
            estilo_actual = None  # (font_name, size_redondeado)

            for line in block["lines"]:
                spans = line.get("spans", [])
                if not spans:
                    continue

                # Texto completo de la línea (todos los spans)
                line_text = "".join(span["text"] for span in spans).strip()
                if not line_text:
                    continue

                span0 = spans[0]
                font = span0["font"]
                size = span0["size"]
                es_negrita = "bold" in font.lower()

                # ¿Esta línea forma parte del título?
                if es_negrita and size >= 12:
                    estilo_linea = (font, int(round(size)))

                    if estilo_actual is None:
                        # Empezamos a acumular un posible título
                        estilo_actual = estilo_linea
                        buffer_lineas.append(line_text)
                    elif estilo_linea == estilo_actual:
                        # Misma fuente/tamaño → sigue siendo el mismo título
                        buffer_lineas.append(line_text)
                    else:
                        # Cambió de estilo → cerrar título si ya había algo
                        if buffer_lineas:
                            titulo = " ".join(buffer_lineas).strip()
                            if (
                                len(titulo) >= 25
                                and titulo not in textos_excluidos
                            ):
                                titulos.append((titulo, page_num + 1))
                                titulo_encontrado = True
                                break
                        # Reiniciar acumulador con esta nueva línea
                        estilo_actual = estilo_linea
                        buffer_lineas = [line_text]
                else:
                    # Línea que ya no es del título → cerrar, si había uno
                    if buffer_lineas:
                        titulo = " ".join(buffer_lineas).strip()
                        if (
                            len(titulo) >= 25
                            and titulo not in textos_excluidos
                        ):
                            titulos.append((titulo, page_num + 1))
                            titulo_encontrado = True
                            break
                        buffer_lineas = []
                        estilo_actual = None

            # Por si el título llega hasta la última línea del bloque
            if not titulo_encontrado and buffer_lineas:
                titulo = " ".join(buffer_lineas).strip()
                if (
                    len(titulo) >= 25
                    and titulo not in textos_excluidos
                ):
                    titulos.append((titulo, page_num + 1))
                    titulo_encontrado = True

            if titulo_encontrado:
                break  # ya tenemos el título de esta página

    return titulos


titulos_detectados = detectar_titulos(pdf_path)

for idx, (titulo, pagina) in enumerate(titulos_detectados, 1):
    print(f"{idx}. {titulo} - Página {pagina}")


def extraer_noticias_completas(pdf_path, titulos_detectados):
    doc = fitz.open(pdf_path)
    noticias = []

    for i, (titulo, pagina_inicio) in enumerate(titulos_detectados):
        # Calcular la página final de esta noticia
        if i + 1 < len(titulos_detectados):
            pagina_siguiente = titulos_detectados[i + 1][1]
            pagina_fin = pagina_siguiente - 1
        else:
            pagina_fin = doc.page_count  # última noticia llega hasta el final

        # Extraer texto de todas las páginas correspondientes
        texto = ""
        for num in range(pagina_inicio - 1, pagina_fin):
            page = doc.load_page(num)
            texto += page.get_text()

        noticias.append({
            "titulo": titulo,
            "pagina_inicio": pagina_inicio,
            "pagina_fin": pagina_fin,
            "paginas": list(range(pagina_inicio, pagina_fin + 1)),
            "texto": texto.strip()
        })

    return noticias

noticias = extraer_noticias_completas(pdf_path, titulos_detectados)

for i, noticia in enumerate(noticias, 1):
    print(f"Noticia {i}")
    print(f"Título: {noticia['titulo']}")
    print(f"Páginas: {noticia['paginas']}")
    print(f"Texto (primeros 300 caracteres):\n{noticia['texto'][:300]}")
    print("-" * 80)

#elección de las noticias a resumir 
selección = input ("Escribe los números de las noticias que quieres resumir (separados por comas): ")
indices = [int(n.strip()) - 1 for n in selección.split(",") if n.strip().isdigit()]

#Obtener los textos de las noticias seleccionadas
noticias_seleccionadas = [noticias[i] for i in indices if 0 <= i < len(noticias)]


from summary_claude import resumir_con_claude

import json

resumenes_para_word = []

print("\n=== Resúmenes generados ===\n")
for i, noticia in enumerate(noticias_seleccionadas, 1):
    print(f"▶ Resumiendo noticia {i}: {noticia['titulo']}")
    resumen = resumir_con_claude(noticia["texto"])
    print(f"\n📝 Resumen {i}:\n{resumen}")
    print("-" * 80)

    resumenes_para_word.append({
        "titulo": noticia["titulo"],
        "resumen": resumen
    })

# Guardar los resúmenes en un archivo temporal
with open("resumenes_aprobados.json", "w", encoding="utf-8") as f:
    json.dump(resumenes_para_word, f, ensure_ascii=False, indent=2)

print("Resúmenes guardados en 'resumenes_aprobados.json'")


