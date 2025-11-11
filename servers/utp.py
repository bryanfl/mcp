import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import Dict
from fastmcp import FastMCP
from external_data.google.bigquery import execute_query, schema_campaign_info
from external_data.utp.convalidaciones import get_convalidaciones
import requests
from typing import Annotated, Literal
from bs4 import BeautifulSoup
from boilerpy3 import extractors
from fuzzywuzzy import fuzz, process
import pandas as pd

mcp = FastMCP("mcp-utp", stateless_http=True)

df_convalidaciones = get_convalidaciones()
print(df_convalidaciones.head())
# @mcp.tool(
#     name="solicitar_urls_informacion_utp",
#     description="""
#         Proporciona la URLs de la Pagina de UTP que servira para obtener informacion.
#         Notas a tener en cuenta:
#         - Solo ejecutar esta herramienta si el usuario pide informacion sobre la UTP.
#         - Debes buscar en la lista de urls proporcionada y devolver solo la URL que mejor se adapte a la consulta del usuario.
#         - Si no encuentras una URL adecuada, debes indicarle que no se encontro informacion.
#         - En base a la consulta del usuario, debes devolver solo una URL que la usaras en la herramienta 'obtener_informacion_carreras_utp'.
#         - Terminandoo de ejecutar esta herramienta, debes usar la herramienta 'obtener_informacion_sobre_utp' para obtener la informacion que el usuario solicito.
#     """,
#     tags=["utp", "urls"],
#     output_schema={
#         "type": "object", 
#         "properties": {
#             "success": {"type": "boolean"},
#             "urls_utp": {"type": "array"}
#         }
#     }
# )
# def solicitar_urls_informacion_utp(
# ) -> Dict:
#     try:
#         response = requests.get("https://utp.edu.pe/sitemap.xml")
#         soup = BeautifulSoup(response.text, 'html.parser')

#         # Encontrar todos los elementos <loc> y extraer su texto
#         loc_values = [loc.get_text(strip=True) for loc in soup.find_all('loc')]

#         utp_urls = {
#             "url_modalidades": {
#                 "description": """
#                     URLs de las modalidades de estudio de la UTP.

#                     /cgt - Carreras para Gente que Trabaja (semipresencial).
#                     /carreras-a-distancia - Carreras Virtuales a Distancia.
#                     https://www.utp.edu.pe/ - Modalidad Presencial y a la vez el Home de UTP el cual muestra informacion general como carreras, modalidades, sedes, facultades, entre otros pero solo a rasgos generales no se debe usar para obtener informacion detallada.
#                 """,
#                 "urls": []
#             },
#             "url_carreras_pregrado": {
#                 "description": "URLs de las carreras de pregrado de la UTP.",
#                 "urls": []
#             },
#             "url_carreras_cgt_semipresencial": {
#                 "description": "URLs de las carreras de CGT semipresencial de la UTP.",
#                 "urls": []
#             },
#             "url_carreras_virtual_a_distancia": {
#                 "description": "URLs de las carreras virtuales a distancia de la UTP.",
#                 "urls": []
#             },
#             "url_facultades": {
#                 "description": "URLs de las facultades de la UTP.",
#                 "urls": []
#             },
#             "url_campus_o_sedes_utp": {
#                 "description": "URLs de los campus o sedes de la UTP.",
#                 "urls": []
#             }
#         }

#         for url in loc_values:
#             if "/pregrado/facultad" in url:
#                 utp_urls["url_carreras_pregrado"]["urls"].append(url)
#             elif "/cgt/facultad" in url or "/carreras-para-gente-que-trabaja/facultad" in url:
#                 utp_urls["url_carreras_cgt_semipresencial"]["urls"].append(url)
#             elif "/carreras-a-distancia/facultad" in url:
#                 utp_urls["url_carreras_virtual_a_distancia"]["urls"].append(url)
#             elif "https://www.utp.edu.pe/" == url or "https://www.utp.edu.pe/cgt" == url or "https://www.utp.edu.pe/carreras-a-distancia" == url:
#                 utp_urls["url_modalidades"]["urls"].append(url)
#             elif ".pe/facultad" in url or ".pe/arquitectura" in url:
#                 utp_urls["url_facultades"]["urls"].append(url)
#             elif "https://www.utp.edu.pe/pregrado" == url or "https://www.utp.edu.pe/pregrado/ab-testing" == url or "https://www.utp.edu.pe/virtual" == url:
#                 pass
#             else:
#                 utp_urls["url_campus_o_sedes_utp"]["urls"].append(url)

#         return {
#             "success": True,
#             "message": "URLs UTP obtenidas correctamente.",
#             "urls": utp_urls
#         }
#     except Exception as e:
#         print(f"Error: {e}")
#         return {"error": str(e)}

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

        La informacion devuelta estara en formato JSON para facilitar su lectura. Asi que debes asegurarte de procesar bien la informacion y darle en un formato claro al usuario.
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

@mcp.tool(
    name="convalidar_carrera_utp",
    description="""
        Busca dar inforamcion al usuario sobre las diferentes convalidaciones de carreras que tiene la UTP con diferentes institutos asi como tambien poder decir que cursos convalidara.
        
        Notas a tener en cuenta:
        - Solo ejecutar esta herramienta si pide informacion sobre convalidar con la UTP.
        - Si el usuario pregunta semipresencial, debes consultar si es 3 dias a la semana presencial (80-20) o 1 dia a la semana presencial (50-50).
        - Siempre mencionas los cursos convalidados en la respuesta.
        - Si no encuentras convalidaciones, debes indicarle que no se encontro informacion.
        
    """,
    tags=["convalidar", "utp"]
)
def convalidar_carrera_utp(
    instituto_origen: Annotated[str, "Nombre del instituto de origen donde estudio el usuario."],
    carrera_procedencia: Annotated[str, "Nombre de la carrera de procedencia que estudio el usuario."],
    carrera_utp: Annotated[str, "A que carrera de la UTP desea convalidar el usuario."],
    modalidad: Annotated[Literal["PRESENCIAL", "80-20", "50-50", "VIRTUAL"], "Modalidad en la que desea estudiar el usuario."],
    malla: Annotated[str, "Malla de la carrera de procedencia. las estructura siempre es 'MALLA <anio de la malla>'"] = "TABLA UNICA",
) -> Dict:
    try:
        # 🔥 BÚSQUEDA FUZZY PARA INSTITUTO
        institutos_disponibles = df_convalidaciones['INSTITUCIÓN DE ORIGEN'].dropna().unique().tolist()
        instituto_match = process.extractOne(
            instituto_origen, 
            institutos_disponibles,
            scorer=fuzz.partial_ratio,  # Permite coincidencias parciales
            score_cutoff=70  # Umbral mínimo de similitud (70%)
        )
        
        if not instituto_match:
            return {
                "success": False,
                "message": f"No se encontró el instituto '{instituto_origen}'. Institutos disponibles: {institutos_disponibles[:5]}..."
            }
        
        instituto_encontrado = instituto_match[0]
        
        # 🔥 BÚSQUEDA FUZZY PARA CARRERA DE PROCEDENCIA
        carreras_procedencia_disponibles = df_convalidaciones[
            df_convalidaciones['INSTITUCIÓN DE ORIGEN'] == instituto_encontrado
        ]['CARRERA DE PROCEDENCIA'].dropna().unique().tolist()
        
        carrera_procedencia_match = process.extractOne(
            carrera_procedencia,
            carreras_procedencia_disponibles,
            scorer=fuzz.partial_ratio,
            score_cutoff=60
        )
        
        if not carrera_procedencia_match:
            return {
                "success": False,
                "message": f"No se encontró la carrera '{carrera_procedencia}' en {instituto_encontrado}. Carreras disponibles: {carreras_procedencia_disponibles}"
            }
        
        carrera_procedencia_encontrada = carrera_procedencia_match[0]
        
        # 🔥 BÚSQUEDA FUZZY PARA CARRERA UTP
        carreras_utp_disponibles = df_convalidaciones['CARRERA CONVALIDADA EN UTP'].dropna().unique().tolist()
        carrera_utp_match = process.extractOne(
            carrera_utp,
            carreras_utp_disponibles,
            scorer=fuzz.partial_ratio,
            score_cutoff=60
        )
        
        if not carrera_utp_match:
            return {
                "success": False,
                "message": f"No se encontró la carrera UTP '{carrera_utp}'. Carreras UTP disponibles: {carreras_utp_disponibles[:5]}..."
            }
        
        carrera_utp_encontrada = carrera_utp_match[0]
        
        # 🔥 FILTRAR DATAFRAME CON VALORES ENCONTRADOS
        resultado = df_convalidaciones[
            (df_convalidaciones['INSTITUCIÓN DE ORIGEN'] == instituto_encontrado) &
            (df_convalidaciones['CARRERA DE PROCEDENCIA'] == carrera_procedencia_encontrada) &
            (df_convalidaciones['CARRERA CONVALIDADA EN UTP'] == carrera_utp_encontrada) &
            (df_convalidaciones['DISPONIBLE EN SUB GRADOS'] == modalidad) &
            (df_convalidaciones['MALLA'] == malla)
        ]
        
        if resultado.empty:
            # Intentar búsqueda más flexible sin malla
            resultado = df_convalidaciones[
                (df_convalidaciones['INSTITUCIÓN DE ORIGEN'] == instituto_encontrado) &
                (df_convalidaciones['CARRERA DE PROCEDENCIA'] == carrera_procedencia_encontrada) &
                (df_convalidaciones['CARRERA CONVALIDADA EN UTP'] == carrera_utp_encontrada) &
                (df_convalidaciones['DISPONIBLE EN SUB GRADOS'] == modalidad)
            ]
        
        if resultado.empty:
            return {
                "success": False,
                "message": f"No se encontraron convalidaciones para:\n- Instituto: {instituto_encontrado}\n- Carrera origen: {carrera_procedencia_encontrada}\n- Carrera UTP: {carrera_utp_encontrada}\n- Modalidad: {modalidad}"
            }
        
        # Convertir resultado a diccionario para mejor presentación
        convalidaciones = resultado.to_dict('records')

        print({
            "success": True,
            "instituto_encontrado": instituto_encontrado,
            "carrera_procedencia_encontrada": carrera_procedencia_encontrada,
            "carrera_utp_encontrada": carrera_utp_encontrada,
            "modalidad": modalidad,
            "total_convalidaciones": len(convalidaciones),
            "convalidaciones": convalidaciones
        })
        
        return {
            "success": True,
            "instituto_encontrado": instituto_encontrado,
            "carrera_procedencia_encontrada": carrera_procedencia_encontrada,
            "carrera_utp_encontrada": carrera_utp_encontrada,
            "modalidad": modalidad,
            "total_convalidaciones": len(convalidaciones),
            "convalidaciones": convalidaciones
        }
        
    except Exception as e:
        print(f"Error en convalidación: {e}")
        return {"error": str(e)}

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


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8102, path="/mcp")