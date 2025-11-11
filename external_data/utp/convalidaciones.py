import requests
import pandas as pd
import io

def get_convalidaciones():
    sheetID = '1krcHkx-bidnW1AV29dHqqa6641zFzkXl'
    gid = "985347916"
    url = f"https://docs.google.com/spreadsheets/d/{sheetID}/gviz/tq?tqx=out:csv&gid={gid}"

    response = requests.get(url)
    if response.status_code == 200:
        # 🔥 CREAR DATAFRAME DIRECTAMENTE DESDE CSV
        df = pd.read_csv(io.StringIO(response.text))
        
        return df
    else:
        return None

# print(data)