import requests
from bs4 import BeautifulSoup

def clean_html(html):
    soup = BeautifulSoup(html, 'html.parser')

    # Lista de etiquetas a eliminar completamente
    etiquetas_a_eliminar = ['script', 'style', 'meta', 'svg', 'path', 'circle', 'rect', 
                           'nav', 'footer', 'button', 'footer', 'noscript']
    
    for etiqueta in soup.find_all(etiquetas_a_eliminar):
        etiqueta.decompose()
    
    # Para las etiquetas que queremos mantener pero limpiar sus atributos
    etiquetas_a_limpiar = ['', 'span', 'section', 'main', 'picture', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                          'a', 'ul', 'ol', 'li', 'table', 'tr', 'td', 'th', 'img', 'source', 'header']
    
    for etiqueta in soup.find_all(etiquetas_a_limpiar):
        # Mantener solo algunos atributos esenciales
        atributos_permitidos = ['href', 'src', 'alt', 'data-src']  # puedes ajustar esta lista
        atributos_actuales = list(etiqueta.attrs.keys())
        
        for atributo in atributos_actuales:
            if atributo not in atributos_permitidos:
                del etiqueta[atributo]
    
    return soup.prettify()

response = requests.get("https://utp.edu.pe/")
print(clean_html(response.text))