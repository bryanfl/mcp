from typing import List, Dict
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
            "http://0.0.0.0:8000/media",
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
            "http://0.0.0.0:8000/media/comments",
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


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8002, path="/mcp")