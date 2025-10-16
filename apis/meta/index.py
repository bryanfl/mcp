from fastapi import FastAPI
from fastapi import Query
from dotenv import load_dotenv
# from google.cloud import bigquery
from datetime import datetime, timedelta
from fastapi.routing import APIRouter
from crm.leads import tokenLeads
import requests
import uvicorn
import os
import json 

app = FastAPI()
router = APIRouter()

load_dotenv()
access_token = os.getenv("ACCESS_TOKEN_META")
ad_account_id = "act_268788766904418"

@router.get("/leads")
def get_leads(
    from_date: str = Query(None, alias="from_date"),
    to_date: str = Query(None, alias="to_date"),
    campaigns_name: list[str] = Query(None, alias="campaigns_name")
):
    if not from_date or not to_date:
        return {"success": False, "error": "from_date and to_date are required parameters."}

    if campaigns_name:
        campaigns_name = json.loads(campaigns_name[0])

    if to_date:
        if from_date == to_date:
            to_date_dt = datetime.strptime(to_date, "%Y-%m-%d")
            to_date_dt += timedelta(days=1)
            to_date = to_date_dt.strftime("%Y-%m-%d")
        to_date = to_date

    response = tokenLeads(from_date, to_date, campaigns_name)
    # if response.status_code != 200:
        #return {"success": False, "error": response.json()}
    return {"success": True, "data": response}

@router.get("/ads")
def get_ads(
    from_date: str = Query(None, alias="from_date"),
    to_date: str = Query(None, alias="to_date"),
    campaigns_name: list[str] = Query(None, alias="campaigns_name")
):
    if not from_date or not to_date:
        return {"success": False, "error": "from_date and to_date are required parameters."}

    if campaigns_name is None or len(campaigns_name) == 0:
        return {"success": False, "error": "At least one campaign name must be provided."}

    if campaigns_name:
        campaigns_name = json.loads(campaigns_name[0])

    if to_date:
        if from_date == to_date:
            to_date_dt = datetime.strptime(to_date, "%Y-%m-%d")
            to_date_dt += timedelta(days=1)
            to_date = to_date_dt.strftime("%Y-%m-%d")
        to_date = to_date

    url = f"https://graph.facebook.com/v23.0/{ad_account_id}/campaigns"

    # OBTENER IDS
    params = {
        "fields": "id,name,status",
        "limit": 1000,  # Solicita un límite mayor
        "access_token": access_token
    }

    if from_date:
        params["since"] = from_date
    if to_date:
        if from_date == to_date:
            to_date_dt = datetime.strptime(to_date, "%Y-%m-%d")
            to_date_dt += timedelta(days=1)
            to_date = to_date_dt.strftime("%Y-%m-%d")
        params["until"] = to_date
    
    response = requests.get(url, params=params)
    data = response.json()['data']

    # Filtrar campañas por nombre
    campaigns_id = [campaign["id"] for campaign in data if campaign['name'] in campaigns_name]

    # OBTENER METRICAS DE CONJUNTOS
    params_metrics = {
        # "fields": "id,name,adsets{id,name,insights}",
        "fields": "id,name,adsets{id,name}",
        "limit": 100,
        "access_token": access_token,
        "filtering": json.dumps([
            {
                "field": "campaign.id", 
                "operator": "IN", 
                "value": campaigns_id
            },
        ]),
    }

    response = requests.get(url, params=params_metrics)
    res = response.json()

    for campaign in res["data"]:
        for adset in campaign.get("adsets", {}).get("data", []):
            adset_id = adset["id"]
            insights_url = f"https://graph.facebook.com/v23.0/{adset_id}/insights"
            insights_params = {
                "fields": "impressions,clicks,spend,cpc,ctr,reach,frequency",
                "access_token": access_token,
                "time_range[since]": params["since"],  # Separate parameter
                "time_range[until]": params["until"]   # Separate parameter
            }
            insights_response = requests.get(insights_url, params=insights_params)
            insights_data = insights_response.json().get("data", [])
            adset["insights"] = insights_data if insights_data else []


    return {"success": True, "data": res}

# @router.get("/ads-bg")
# def get_ads(
#     from_date: str = Query(None, alias="from_date"),
#     to_date: str = Query(None, alias="to_date"),
#     campaigns_name: list[str] = Query(None, alias="campaigns_name")
# ):
#     if not from_date or not to_date:
#         return {"success": False, "error": "from_date and to_date are required parameters."}

#     if campaigns_name is None or len(campaigns_name) == 0:
#         return {"success": False, "error": "At least one campaign name must be provided."}

#     if campaigns_name:
#         campaigns_name = json.loads(campaigns_name[0])

#     QUERY = (
#         f'SELECT * FROM `api-audiencias-309221.raw_windsor_ads.Raw_windsor_ads_2years` WHERE date BETWEEN "{from_date}" AND "{to_date}" ORDER BY date ASC')
    
#     res_bg = client.query(QUERY)
#     res = res_bg.result().to_dataframe().to_dict(orient='records')

#     return {"success": True, "data": res}
