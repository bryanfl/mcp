import requests
from bs4 import BeautifulSoup
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
    elif "https://www.utp.edu.pe/pregrado" == url or "https://www.utp.edu.pe/pregrado/ab-testing" == url or "https://www.utp.edu.pe/virtual" == url:
        pass
    else:
        utp_urls["url_campus_o_sedes_utp"]["urls"].append(url)

print(utp_urls)