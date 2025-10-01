from fastapi import FastAPI
import uvicorn
import requests
from fastapi import Query
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from fastapi.routing import APIRouter

app = FastAPI()
router = APIRouter()

load_dotenv()

@router.get("/leads")
def get_leads(
    from_date: str = Query(None, alias="from_date"),
    to_date: str = Query(None, alias="to_date")
):
    url = "https://graph.facebook.com/v23.0/17841406708354281/media"

    # Construir los parámetros de la solicitud
    params = {
        "fields": "id,caption,comments_count,alt_text,like_count,timestamp",#,comments{text,username,id},timestamp",
        "limit": 100,
        "access_token": access_token
    }
    # Agregar filtros de fecha si están presentes
    if from_date:
        params["since"] = from_date
    if to_date:
        if from_date == to_date:
            to_date_dt = datetime.strptime(to_date, "%Y-%m-%d")
            to_date_dt += timedelta(days=1)
            to_date = to_date_dt.strftime("%Y-%m-%d")
        params["until"] = to_date


    response = tokensLead()
    if response.status_code != 200:
        return {"success": False, "error": response.json()}
    return {"success": True, "data": response.json()}