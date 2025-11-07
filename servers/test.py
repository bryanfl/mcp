import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import trafilatura
from typing import List, Dict, Optional
from fastmcp import FastMCP
from external_data.google.bigquery import execute_query, schema_campaign_info
import requests
import json
from typing import Annotated
from bs4 import BeautifulSoup
import re
from boilerpy3 import extractors

def obtener_informacion_sobre_utp(
    url_carrera: Annotated[str, f"URL de la UTP a consultar"],
) -> Dict:
    try:
        response = requests.get(
            f"{url_carrera}",
        )

        response.raise_for_status()
        
        html = limpiar_html_boilerpy(response.text)

        return html
    except requests.RequestException as req_error:
        print(f"Request error: {req_error}")
        return {"error": str(req_error)}

def limpiar_html_boilerpy(html: str):
    extractor = extractors.KeepEverythingExtractor()
    html = clean_html_text(html)
    texto = extractor.get_content(html)

    # 🔹 Analizar estructura con BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    imagenes = []

    for img in soup.find_all("img"):
        # Detectar si la imagen es un placeholder (base64)
        src = img.get("data-src") or img.get("src")
        if not src:
            continue

        if src.startswith("data:image"):
            # Buscar <source> hermano dentro del mismo <picture>
            picture = img.find_parent("picture")
            if picture:
                source = picture.find("source")
                if source and source.get("data-srcset"):
                    src = source["data-srcset"]

        alt = img.get("alt", "").strip() or None

        # Buscar <section> o <div> con id más cercano
        seccion = None
        for parent in img.parents:
            if parent.name in ["section"]:
                sec_id = parent.get("id")
                if sec_id:
                    seccion = sec_id
                    break

        imagenes.append({
            "alt": alt,
            "src": f"https://utp.edu.pe{src.strip()}",
            "seccion": seccion or "sin_seccion"
        })

    return {
        "texto": texto,
        "imagenes": imagenes
    }

def clean_html_text(html, url=None):
    soup = BeautifulSoup(html, 'html.parser')

    # Lista de etiquetas a eliminar completamente
    etiquetas_a_eliminar = ['script', 'style', 'meta', 'svg', 'path', 'circle', 'rect', 
                           'nav', 'button', 'noscript', 'form']
    
    if url != "https://www.utp.edu.pe/":
        etiquetas_a_eliminar.extend(['header', 'footer'])

    for etiqueta in soup.find_all(etiquetas_a_eliminar):
        etiqueta.decompose()
    
    # Para las etiquetas que queremos mantener pero limpiar sus atributos
    etiquetas_a_limpiar = ['div', 'span', 'section', 'main', 'picture', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'ul', 'ol', 'li', 'table', 'tr', 'td', 'th', 'img', 'header']
    
    # 🔥 Eliminar cualquier <div> cuyo id comience con "form"
    candidates = []

    for div in soup.find_all('div', id=True):
        if div['id'].lower().startswith('form'):
            candidates.append(div)

    for div in candidates:
        div.decompose()
    
    for etiqueta in soup.find_all(etiquetas_a_limpiar):
        # Mantener solo algunos atributos esenciales
        atributos_permitidos = ['href', 'src', 'alt', 'data-src', "id", "srcset"]  # puedes ajustar esta lista
        atributos_actuales = list(etiqueta.attrs.keys())
        
        for atributo in atributos_actuales:
            if atributo not in atributos_permitidos:
                del etiqueta[atributo]
    
    return soup.prettify()

def clean_html(html, url=None):
    soup = BeautifulSoup(html, 'html.parser')

    # Lista de etiquetas a eliminar completamente
    etiquetas_a_eliminar = ['script', 'style', 'meta', 'svg', 'path', 'circle', 'rect', 
                           'nav', 'button', 'noscript', 'form']
    
    if url != "https://www.utp.edu.pe/":
        etiquetas_a_eliminar.extend(['header', 'footer'])

    for etiqueta in soup.find_all(etiquetas_a_eliminar):
        etiqueta.decompose()
    
    # Para las etiquetas que queremos mantener pero limpiar sus atributos
    etiquetas_a_limpiar = ['div', 'span', 'section', 'main', 'picture', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'a', 'ul', 'ol', 'li', 'table', 'tr', 'td', 'th', 'img', 'source', 'header']
    
    # 🔥 Eliminar cualquier <div> cuyo id comience con "form"
    candidates = []

    for div in soup.find_all('div', id=True):
        if div['id'].lower().startswith('form'):
            candidates.append(div)

    for div in candidates:
        div.decompose()
    
    for etiqueta in soup.find_all(etiquetas_a_limpiar):
        # Mantener solo algunos atributos esenciales
        atributos_permitidos = ['href', 'src', 'alt', 'data-src', "id"]  # puedes ajustar esta lista
        atributos_actuales = list(etiqueta.attrs.keys())
        
        for atributo in atributos_actuales:
            if atributo not in atributos_permitidos:
                del etiqueta[atributo]
    
    return soup.prettify()

print(obtener_informacion_sobre_utp("https://www.utp.edu.pe"))
# print(obtener_informacion_sobre_utp("https://www.utp.edu.pe/pregrado/facultad-de-ingenieria/ingenieria-de-sistemas-e-informatica"))