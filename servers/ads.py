import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Optional
from fastmcp import FastMCP
from external_data.google.bigquery import execute_query, schema_campaign_info
import requests
import json
from typing import Annotated

mcp = FastMCP("mcp-ads", stateless_http=True)

@mcp.tool(
    name="obtener_informacion_leads_crm",
    description="""
        Obtiene los leads generados en CRM entre dos fechas específicas para análisis, estos leads pertenecen a las diferentes plataformas de redes sociales

        Notas a tener en cuenta:
        - Solo ejecutar esta herramienta si piden informacion de leads.
        - Si te mencionan alguna plataforma, google, tiktok, bing o facebook, esto vara el 'source'.
        - utm_campaign es igual a campaign.
        - utm_content es igual a ad_group_name.
    """,
    tags=["crm", "google", "bing", "tiktok", "facebook", "meta_ads", "leads"]
)
def obtener_informacion_campaigns_crm(
    from_date: Annotated[str, "Fecha de inicio en formato 'YYYY-MM-DD'."],
    to_date: Annotated[str, "Fecha de fin en formato 'YYYY-MM-DD'."],
    campaigns_name: Annotated[list[str], "Lista de nombres de campañas [obligatorio], si no recibe una campaña no debes ejecutar."],
) -> Dict:
    try:
        response = requests.get(
            f"http://0.0.0.0:8001/meta/leads",
            params={"from_date": from_date, "to_date": to_date, "campaigns_name": json.dumps(campaigns_name)}
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

    

@mcp.tool(
    name="obtener_informacion_campaign_ads",
    description="""
        Obtiene la información de las campañas de Google, Bing o Tiktok y Facebook.
        Ten en cuenta que esta información es solo para análisis y no incluye leads.
        No requieres de fechas para tu consultas, si el usuario las proporciona usalas, si no, consulta como lo veas conveniente.

        Notas a tener en cuenta:
        - Solo ejecutar esta herramienta si piden informacion de campañas.
        - Si te mencionan alguna plataforma, google, tiktok, bing o facebook, esto
        - Debes ejecutar el tool 'obtener_informacion_campaigns_crm' para obtener los leads generados en CRM y asi tener un analisis completo del funnel.
        - utm_campaign es igual a campaign.
        - utm_content es igual a ad_name.
    """,
    tags=["ads", "google", "bing", "tiktok", "facebook", "meta_ads", "bigquery"]
)
def obtener_informacion_campaign_ads(
    sql_query: Annotated[str, f"Consulta SQL para ejecutar en BigQuery, recuerda siempre dar un nombre a las columnas basados en el schema proporcionado {schema_campaign_info}"]
) -> Dict:

    try:
        res = execute_query(sql_query)

        return {
            "success": True,
            "result_query_executed": res,
        }
    except requests.RequestException as req_error:
        print(f"Request error: {req_error}")
        return {"error": str(req_error)}
    
## RESOURCE
@mcp.resource('resource://schema_tables_bigquery')
async def get_schema_tables_bigquery_resource() -> str:
    """Devuelve el esquema actualizado de las tablas de bigquery"""
    schema_info = {
        "dataset": "api-audiencias-309221.raw_windsor_ads",
        "tables": [
            {
                "name": "campañas_unificadas",
                "description": "Sirve para dar informacion sobre campañas de Tiktok, Bing y Google, la informacion es de los ultimos 2 años y ayuda a tener un mejor analisis historico.",
                "fields": [
                    {"name": "date", "type": "DATE", "mode": "NULLABLE"},
                    {"name": "source", "type": "STRING", "mode": "NULLABLE", "allowed_values": ["tiktok", "google", "bing", "facebook", "dv360"]},
                    {"name": "campaign", "type": "STRING", "mode": "NULLABLE"},
                    {"name": "ad_group_name", "type": "STRING", "mode": "NULLABLE"},
                    {"name": "ad_name", "type": "STRING", "mode": "NULLABLE"},
                    {"name": "Identificador del anuncio", "type": "STRING", "mode": "NULLABLE"},
                    {"name": "Spend", "type": "FLOAT", "mode": "NULLABLE"},
                    {"name": "datasource", "type": "STRING", "mode": "NULLABLE"},
                    {"name": "impressions", "type": "BIGNUMERIC", "mode": "NULLABLE"},
                    {"name": "clicks", "type": "BIGNUMERIC", "mode": "NULLABLE"},
                ]
            }
        ]
    }
    return json.dumps(schema_info, indent=4)

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

    return {
        "funnel_summary": funnel_summary,
        "conversion_rates": {
            "valido_to_generado": f"{(funnel_summary['validos']/funnel_summary['generados'])*100:.1f}%",
            "pago_to_valido": f"{(funnel_summary['pago_generado']/funnel_summary['validos'])*100:.1f}%" if funnel_summary['validos'] > 0 else "0%"
        },
        "campañas": campaigns,
        "date_range_insights": f"Análisis de {len(data)} leads entre fechas"
    }

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8101, path="/mcp")