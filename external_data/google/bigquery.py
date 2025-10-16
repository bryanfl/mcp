from google.cloud import bigquery
import os

current_directory = os.path.dirname(os.path.abspath(__file__))
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = f"{current_directory}/settings_bigquery.json"
client = bigquery.Client()

schema_campaign_info = {
    "project": "api-audiencias-309221",
    "dataset": "raw_windsor_ads",
    "table": "campañas_unificadas",
    "description": "Sirve para dar informacion sobre campañas de Tiktok, Bing y Google y Meta ADS, la informacion es de los ultimos 2 años y ayuda a tener un mejor analisis historico.",
    "fields": [
        {"name": "date", "type": "DATE", "mode": "NULLABLE"},
        {"name": "source", "type": "STRING", "mode": "NULLABLE", "allowed_values": ["tiktok", "google", "bing", "meta_ads"]},
        {"name": "campaign", "type": "STRING", "mode": "NULLABLE"},
        {"name": "ad_group_name", "type": "STRING", "mode": "NULLABLE"},
        {"name": "ad_name", "type": "STRING", "mode": "NULLABLE"},
        {"name": "Identificador del anuncio", "type": "STRING", "mode": "NULLABLE"},
        {"name": "Spend", "type": "FLOAT", "mode": "NULLABLE"},
        {"name": "datasource", "type": "STRING", "mode": "NULLABLE"},
        {"name": "impressions", "type": "BIGNUMERIC", "mode": "NULLABLE"},
        {"name": "clicks", "type": "BIGNUMERIC", "mode": "NULLABLE"},
        # {"name": "rn", "type": "INTEGER", "mode": "NULLABLE"}
    ]
}


def execute_query(query):
    print( f"Ejecutando consulta:\n{query}\n" )
    QUERY = query

    res_bg = client.query(QUERY)
    res = res_bg.result().to_dataframe().to_dict(orient='records')
    return res

def list_tables_and_schemas(project_id, dataset_id):
    client = bigquery.Client(project=project_id)
    
    # Listar todas las tablas del dataset
    tables = client.list_tables(dataset_id)
    
    schemas_info = {}
    
    for table in tables:
        print(f"📊 TABLA: {table.table_id}")
        
        # Obtener tabla completa con esquema
        table_ref = client.dataset(dataset_id).table(table.table_id)
        table_obj = client.get_table(table_ref)
        
        # Extraer información del esquema
        schema_info = []
        for field in table_obj.schema:
            field_info = {
                'name': field.name,
                'type': field.field_type,
                'mode': field.mode,  # NULLABLE, REQUIRED, REPEATED
                'description': field.description or 'Sin descripción'
            }
            schema_info.append(field_info)
        
        schemas_info[table.table_id] = schema_info
        
        # Mostrar esquema
        for field in schema_info:
            print(f"  └─ {field['name']} ({field['type']}) - {field['mode']}")
        print()
    
    return schemas_info