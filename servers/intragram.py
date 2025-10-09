from typing import List, Dict, Optional
from fastmcp import FastMCP
import requests
import json

mcp = FastMCP("mcp-instagram", stateless_http=True)

@mcp.tool()
def listar_publicaciones_instagram_utp(from_date: str, to_date: str) -> List[Dict]:
    """Lista todos los registros de media entre dos fechas específicas de Instagram.

    Args:
        from_date: Fecha de inicio en formato 'YYYY-MM-DD'.
        to_date: Fecha de fin en formato 'YYYY-MM-DD'.
    """
    try:
        response = requests.get(
            "http://0.0.0.0:8001/instagram/media",
            params={"from_date": from_date, "to_date": to_date}
        )
        response.raise_for_status()
        
        # Verificar que la respuesta sea JSON válido
        try:
            data = response.json()
            if isinstance(data, dict) and 'data' in data:
                return {
                    "success": True,
                    "count": len(data['data']),
                    "publications": data['data']
                }
            else:
                return {
                    "success": True,
                    "count": len(data) if isinstance(data, list) else 1,
                    "publications": data if isinstance(data, list) else [data]
                }
        except json.JSONDecodeError as json_error:
            return {
                "success": False,
                "error": "Invalid JSON response",
                "count": 0,
                "publications": []
            }
            
    except requests.RequestException as req_error:
        print(f"Request error: {req_error}")
        return {"error": str(req_error)}

@mcp.tool()
def listar_comentarios_publicaciones_instagram_utp(from_date: str, to_date: str) -> List[Dict]:
    """Lista todos los registros de comentarios de publicaciones entre dos fechas específicas de Instagram.

    Args:
        from_date: Fecha de inicio en formato 'YYYY-MM-DD'.
        to_date: Fecha de fin en formato 'YYYY-MM-DD'.
    """
    try:
        response = requests.get(
            "http://0.0.0.0:8001/instagram/media/comments",
            params={"from_date": from_date, "to_date": to_date}
        )
        response.raise_for_status()
        
        # Verificar que la respuesta sea JSON válido
        try:
            data = response.json()
            if isinstance(data, dict) and 'data' in data:
                return {
                    "success": True,
                    "publications": data['data']
                }
            else:
                return {
                    "success": True,
                    "publications": data if isinstance(data, list) else [data]
                }
        except json.JSONDecodeError as json_error:
            return {
                "success": False,
                "error": "Invalid JSON response",
                "publications": []
            }
            
    except requests.RequestException as req_error:
        print(f"Request error: {req_error}")
        return {"error": str(req_error)}


@mcp.tool()
def obtener_leads_crm_facebook(from_date: str, to_date: str) -> Dict:
    """Obtiene los leads generados en CRM entre dos fechas específicas para análisis, estos leads pertenecen a Facebook tanto por web, por zapier y por whatsapp.
    Args:
        from_date: Fecha de inicio en formato 'YYYY-MM-DD'.
        to_date: Fecha de fin en formato 'YYYY-MM-DD'.
    """
    try:
        response = requests.get(
            f"http://0.0.0.0:8001/meta/leads",
            params={"from_date": from_date, "to_date": to_date}
        )

        response.raise_for_status()
        res = response.json()
        data = [
            lead for lead in res["data"]
            if lead.get("utm_campaign") and lead.get("utm_content")
        ]

        summary = preprocess_lead_data(data)
        
        return {
            "success": True,
            "date_range": f"{from_date} a {to_date}",
            "summary": summary,
            "total_leads": len(data),
            "instructions": """
            ANALIZA ESTE RESUMEN DEL FUNNEL DE LEADS:
            
            FLUJO COMPLETO: Generados → Válidos → Pago Generado → Matriculados/Inscritos
            MÉTRICAS CLAVE:
            - Eficiencia por campaña (utm_campaign)
            - Conversión entre etapas del funnel
            - Tendencias temporales
            """
        }
    except requests.RequestException as req_error:
        print(f"Request error: {req_error}")
        return {"error": str(req_error)}
    
@mcp.tool()
def obtener_informacion_campaign_facebook(from_date: str, to_date: str, campaigns_name: list[str]) -> Dict:
    """Obtiene la información de las campañas de Facebook entre dos fechas específicas y enviando el nombre de las campañas.
    Esto tambien dara la información de los conjuntos de anuncios y sus métricas.
    Args:
        from_date: Fecha de inicio en formato 'YYYY-MM-DD'.
        to_date: Fecha de fin en formato 'YYYY-MM-DD'.
        campaigns_name: Lista de nombres de campañas a filtrar.
    """
    try:
        response = requests.get(
            f"http://0.0.0.0:8001/meta/ads",
            params={"from_date": from_date, "to_date": to_date, "campaigns_name": json.dumps(campaigns_name)}
        )

        response.raise_for_status()
        res = response.json()

        return {
            "success": True,
            "campaigns": res["data"],
        }
    except requests.RequestException as req_error:
        print(f"Request error: {req_error}")
        return {"error": str(req_error)}


def preprocess_lead_data(data):
    """Resume y estructura los datos para mejor análisis"""
    if not data:
        return {"error": "No data available"}
    
    # Resumen por etapas del funnel
    funnel_summary = {
        "generados": len(data),
        "validos": sum(1 for lead in data if lead["status_crm"] in ['valido', 'pago_generado', 'matriculado', 'inscrito']),
        "pago_generado": sum(1 for lead in data if lead["status_crm"] in ['pago_generado', 'matriculado', 'inscrito']),
        "inscritos": sum(1 for lead in data if lead["status_crm"] in ['inscrito']),
    }
    
    # Agrupado por campaña y utm_content
    campaigns = {}
    for lead in data:
        campaign = lead.get('utm_campaign', 'sin_campaña')
        content = lead.get('utm_content', 'sin_content')
        if campaign not in campaigns:
            campaigns[campaign] = {"contenido": {}}
        if content not in campaigns[campaign]["contenido"]:
            campaigns[campaign]["contenido"][content] = {
                "generados": 0,
                "validos": 0,
                "pago_generado": 0,
                "inscritos": 0
            }
        campaigns[campaign]["contenido"][content]["generados"] += 1
        if lead["status_crm"] in ['valido', 'pago_generado', 'matriculado', 'inscrito']:
            campaigns[campaign]["contenido"][content]["validos"] += 1
        if lead["status_crm"] in ['pago_generado', 'matriculado', 'inscrito']:
            campaigns[campaign]["contenido"][content]["pago_generado"] += 1
        if lead["status_crm"] in ['inscrito']:
            campaigns[campaign]["contenido"][content]["inscritos"] += 1

    print("campaigns", campaigns)
    
    return {
        "funnel_summary": funnel_summary,
        "conversion_rates": {
            "valido_to_generado": f"{(funnel_summary['validos']/funnel_summary['generados'])*100:.1f}%",
            "pago_to_valido": f"{(funnel_summary['pago_generado']/funnel_summary['validos'])*100:.1f}%" if funnel_summary['validos'] > 0 else "0%"
        },
        "campañas": campaigns,
        "date_range_insights": f"Análisis de {len(data)} leads entre fechas"
    }
# @mcp.tool(name="search")
# def search(query: str) -> List[Dict]:
#     """
#     Acción 'search' requerida por ChatGPT.
#     Debe recibir un parámetro obligatorio `query` de tipo string.
#     """
#     # Devuelve resultados estáticos de ejemplo
#     return [
#         {
#             "id": "1",
#             "title": "Publicación de prueba 1",
#             "url": "https://instagram.com/post/1",
#             "snippet": "Este es un caption de ejemplo para la publicación 1.",
#         },
#         {
#             "id": "2",
#             "title": "Publicación de prueba 2",
#             "url": "https://instagram.com/post/2",
#             "snippet": "Otro caption de ejemplo para la publicación 2.",
#         }
#     ]

# @mcp.tool(name="fetch")
# def fetch(id: str) -> Dict:
#     """
#     Acción 'fetch' requerida por ChatGPT.
#     Debe aceptar un parámetro `id` (string) y devolver el contenido completo.
#     """
#     if id == "1":
#         return {
#             "id": "1",
#             "content": {
#                 "caption": "Este es el detalle completo de la publicación 1.",
#                 "likes": 123,
#                 "comments": ["Buen post", "Excelente contenido"]
#             }
#         }
#     elif id == "2":
#         return {
#             "id": "2",
#             "content": {
#                 "caption": "Este es el detalle completo de la publicación 2.",
#                 "likes": 45,
#                 "comments": ["Me gusta", "Muy bueno"]
#             }
#         }
#     else:
#         return {"error": "ID no encontrado en los datos estáticos."}
    
if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8002, path="/mcp")