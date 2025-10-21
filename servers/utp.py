import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Optional
from fastmcp import FastMCP
from external_data.google.bigquery import execute_query, schema_campaign_info
import requests
import json
from typing import Annotated
from bs4 import BeautifulSoup

mcp = FastMCP("mcp-utp", stateless_http=True)

@mcp.tool(
    name="solicitar_urls_informacion_utp",
    description="""
        Proporciona la URLs de la Pagina de UTP que servira para obtener informacion.
        Notas a tener en cuenta:
        - Solo ejecutar esta herramienta si el usuario pide informacion sobre la UTP.
        - Debes buscar en la lista de urls proporcionada y devolver solo la URL que mejor se adapte a la consulta del usuario.
        - Si no encuentras una URL adecuada, debes indicarle que no se encontro informacion.
        - En base a la consulta del usuario, debes devolver solo una URL que la usaras en la herramienta 'obtener_informacion_carreras_utp'.
    """,
    tags=["utp", "urls"],
    output_schema={
        "type": "object", 
        "properties": {
            "success": {"type": "boolean"},
            "urls_utp": {"type": "array"}
        }
    }
)
def solicitar_urls_informacion_utp(
) -> Dict:
    try:
        response = requests.get("https://utp.edu.pe/sitemap.xml")
        soup = BeautifulSoup(response.text, 'html.parser')

        # Encontrar todos los elementos <loc> y extraer su texto
        loc_values = [loc.get_text(strip=True) for loc in soup.find_all('loc')]

        utp_urls = {
            "url_modalidades": {
                "description": """
                    URLs de las modalidades de estudio de la UTP.

                    /cgt - Carreras para Gente que Trabaja (semipresencial).
                    /carreras-a-distancia - Carreras Virtuales a Distancia.
                    https://www.utp.edu.pe/ - Modalidad Presencial y a la vez el Home de UTP el cual muestra informacion general como carreras, modalidades, sedes, facultades, entre otros pero solo a rasgos generales no se debe usar para obtener informacion detallada.
                """,
                "urls": []
            },
            "url_carreras_pregrado": {
                "description": "URLs de las carreras de pregrado de la UTP.",
                "urls": []
            },
            "url_carreras_cgt_semipresencial": {
                "description": "URLs de las carreras de CGT semipresencial de la UTP.",
                "urls": []
            },
            "url_carreras_virtual_a_distancia": {
                "description": "URLs de las carreras virtuales a distancia de la UTP.",
                "urls": []
            },
            "url_facultades": {
                "description": "URLs de las facultades de la UTP.",
                "urls": []
            },
            "url_campus_o_sedes_utp": {
                "description": "URLs de los campus o sedes de la UTP.",
                "urls": []
            }
        }

        for url in loc_values:
            if "/pregrado/facultad" in url:
                utp_urls["url_carreras_pregrado"]["urls"].append(url)
            elif "/cgt/facultad" in url or "/carreras-para-gente-que-trabaja/facultad" in url:
                utp_urls["url_carreras_cgt_semipresencial"]["urls"].append(url)
            elif "/carreras-a-distancia/facultad" in url:
                utp_urls["url_carreras_virtual_a_distancia"]["urls"].append(url)
            elif "https://www.utp.edu.pe/" == url or "https://www.utp.edu.pe/cgt" == url or "https://www.utp.edu.pe/carreras-a-distancia" == url:
                utp_urls["url_modalidades"]["urls"].append(url)
            elif ".pe/facultad" in url or ".pe/arquitectura" in url:
                utp_urls["url_facultades"]["urls"].append(url)
            elif "https://www.utp.edu.pe/pregrado" == url or "https://www.utp.edu.pe/pregrado/ab-testing" == url:
                pass
            else:
                utp_urls["url_campus_o_sedes_utp"]["urls"].append(url)

        return {
            "success": True,
            "message": "URLs UTP obtenidas correctamente.",
            "urls": utp_urls
        }
    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}

@mcp.tool(
    name="obtener_informacion_sobre_utp",
    description="""
        Obtiene la informacion sobre la UTP (Universidad Tecnologica del Peru) que el usuario solicite.
        Notas a tener en cuenta:
        - Solo ejecutar esta herramienta si piden informacion de sobre la UTP.
        - Solo debes responder lo que el usuario pregunte sobre la carrera, no expliques todo se preciso.
        - Si no encuentras la carrera, debes indicarle que no se encontro informacion.
        - Si el usuario solo pregunto algo general, responde algo resumido sobre la carrera.
        - No inventes nada, solo responde con la informacion que encuentres en la pagina y que no sea muy extenso, solo lo consultado.
        - Antes de consultar esta herramienta debes ejecutar la herramiento ''solicitar_urls_informacion_utp'' para obtener la URL correcta a la que debes consultar.

        La informacion devuelta estara en formato HTML para facilitar su lectura. Asi que debes asegurarte de procesar bien la informacion y darle en un formato claro al usuario.
    """,
    tags=["carreras", "utp", "modalidades", "informacion_carrera", "facultades", "sedes", "campus"],
)
def obtener_informacion_sobre_utp(
    url_carrera: Annotated[str, f"URL de la UTP a consultar"],
) -> Dict:
    try:
        response = requests.get(
            f"{url_carrera}",
        )

        response.raise_for_status()

        return {
            "success": True,
            "html_format_response": f"{clean_html(response.text)}",
        }
    except requests.RequestException as req_error:
        print(f"Request error: {req_error}")
        return {"error": str(req_error)}
    
@mcp.tool(
    name="registrar_usuario_crm_utp",
    description="""
        Registra un nuevo usuario en el CRM de la UTP.
        Notas a tener en cuenta:
        - Solo ejecutar esta herramienta si piden registrar un nuevo usuario.
        - Debes asegurarte de que la informacion del usuario este completa y sea precisa.
        - Los campos requeridos son: nombre, apellido, email, telefono, dni.
        - Si el usuario no tiene la informacion completa, no debes ejecutar esta herramienta y debes indicarle que complete la informacion faltante uno por uno para que se le haga mas sencillo al usuario entender que informacion falta.
    """,
    tags=["usuarios", "utp", "registro"]
)
def registrar_usuario_crm_utp(
    nombre: Annotated[str, "Nombre del usuario. Debes validar que el nombre sea un valor valido en el lenguaje español."],
    apellido: Annotated[str, "Apellido del usuario. Debes validar que el apellido sea un valor valido en el lenguaje español."],
    email: Annotated[str, "Email del usuario. Debes validar que el email sea un valor valido con @."],
    telefono: Annotated[str, "Telefono del usuario. Debes validar que el telefono sea puros numeros de nueve digitos"],
    dni: Annotated[str, "DNI del usuario. Debes validar que el DNI sea puros numeros de ocho digitos."],
) -> Dict:
    try:
        # response = requests.post(
        #     "https://api.utp.edu.pe/crm/usuarios",
        #     json={
        #         "nombre": nombre,
        #         "apellido": apellido,
        #         "email": email,
        #         "telefono": telefono,
        #         "dni": dni
        #     }
        # )
        # response.raise_for_status()

        print({
                "nombre": nombre,
                "apellido": apellido,
                "email": email,
                "telefono": telefono,
                "dni": dni
            })

        return {
            "success": True,
            "message": "Usuario registrado exitosamente."
        }
    except requests.RequestException as req_error:
        print(f"Request error: {req_error}")
        return {"error": str(req_error)}

def clean_html(html, url=None):
    soup = BeautifulSoup(html, 'html.parser')

    # Lista de etiquetas a eliminar completamente
    etiquetas_a_eliminar = ['script', 'style', 'meta', 'svg', 'path', 'circle', 'rect', 
                           'nav', 'button', 'noscript']
    
    if url != "https://www.utp.edu.pe/":
        etiquetas_a_eliminar.extend(['header', 'footer'])

    for etiqueta in soup.find_all(etiquetas_a_eliminar):
        etiqueta.decompose()
    
    # Para las etiquetas que queremos mantener pero limpiar sus atributos
    etiquetas_a_limpiar = ['div', 'span', 'section', 'main', 'picture', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                          'a', 'ul', 'ol', 'li', 'table', 'tr', 'td', 'th', 'img', 'source', 'header']
    
    for etiqueta in soup.find_all(etiquetas_a_limpiar):
        # Mantener solo algunos atributos esenciales
        atributos_permitidos = ['href', 'src', 'alt', 'data-src']  # puedes ajustar esta lista
        atributos_actuales = list(etiqueta.attrs.keys())
        
        for atributo in atributos_actuales:
            if atributo not in atributos_permitidos:
                del etiqueta[atributo]
    
    return soup.prettify()

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8104, path="/mcp")