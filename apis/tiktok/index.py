from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
import requests
import urllib.parse
import uvicorn

app = FastAPI(title="TikTok OAuth Callback Server")

# Tus credenciales
CLIENT_KEY = "awn5ixe84twk1m36"
CLIENT_SECRET = "p51JBh9Ys4EVGc9Pvzqu5BmNzi5BcY4N"
REDIRECT_URI = "https://www.utp.edu.pe"

@app.get("/")
async def root():
    """Página principal con la URL de autorización"""
    auth_url = generate_tiktok_auth_url(CLIENT_KEY, REDIRECT_URI)
    decoded_url = urllib.parse.unquote(auth_url)

    return {
        "message": "TikTok OAuth Server",
        "authorization_url": decoded_url,
        "instructions": "Visita la authorization_url para autorizar la aplicación"
    }

@app.get("/callback")
async def handle_callback(
    code: str = Query(None, description="Authorization code from TikTok"),
    state: str = Query(None, description="State parameter"),
    error: str = Query(None, description="Error from TikTok")
):
    """Maneja el callback de TikTok OAuth"""
    
    if error:
        raise HTTPException(status_code=400, detail=f"Error en autorización: {error}")
    
    if not code:
        raise HTTPException(status_code=400, detail="No se recibió código de autorización")
    
    # Intercambiar código por access token
    token_response = await get_tiktok_oauth_token(CLIENT_KEY, CLIENT_SECRET, code, REDIRECT_URI)
    
    if token_response and 'access_token' in token_response:
        access_token = token_response['access_token']
        
        # Opcional: obtener info del usuario
        user_info = await get_user_info(access_token)
        
        # Aquí puedes guardar el token en base de datos, archivo, etc.
        print(f"✅ Token obtenido: {access_token}")
        
        return JSONResponse({
            "message": "✅ Autorización exitosa!",
            "access_token": access_token,
            "token_info": token_response,
            "user_info": user_info
        })
    else:
        raise HTTPException(status_code=400, detail=f"Error obteniendo token: {token_response}")

async def get_tiktok_oauth_token(client_key: str, client_secret: str, code: str, redirect_uri: str):
    """Intercambia el código de autorización por un access token"""
    url = "https://open.tiktokapis.com/v2/oauth/token/"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "client_key": client_key,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }

    try:
        response = requests.post(url, headers=headers, data=data)
        return response.json()
    except Exception as e:
        print(f"Error obteniendo token: {e}")
        return None

async def get_user_info(access_token: str):
    """Obtiene información del usuario autenticado"""
    url = "https://open.tiktokapis.com/v2/user/info/?fields=open_id,union_id,avatar_url,display_name"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    try:
        response = requests.get(url, headers=headers)
        return response.json()
    except Exception as e:
        print(f"Error obteniendo info del usuario: {e}")
        return None

@app.get("/user-videos/{access_token}")
async def get_user_videos(access_token: str):
    """Obtiene videos del usuario autenticado"""
    url = "https://open.tiktokapis.com/v2/video/list/?fields=id,create_time,cover_image_url,share_url,video_description,duration,height,width,title,like_count,comment_count,share_count,view_count"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    data = {
        "max_count": 20
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo videos: {e}")

def generate_tiktok_auth_url(client_key: str, redirect_uri: str, scope: str = "user.info.basic,video.list"):
    """Genera la URL para autorización de TikTok"""
    base_url = "https://www.tiktok.com/v2/auth/authorize/"
    params = {
        "client_key": client_key,
        "response_type": "code",
        "scope": scope,
        "redirect_uri": redirect_uri,
        "state": "your_state_parameter"
    }
    
    query_string = urllib.parse.urlencode(params)
    return f"{base_url}?{query_string}"

if __name__ == "__main__":
    print("🚀 Iniciando servidor FastAPI...")
    print("📱 Ve a http://localhost:8000 para obtener la URL de autorización")
    print("🔗 O visita directamente:")
    auth_url = generate_tiktok_auth_url(CLIENT_KEY, REDIRECT_URI)
    print(f"   {auth_url}")
    
    uvicorn.run(
        app,  # Cambiar "mcp:app" por solo app
        host="0.0.0.0",
        port=8000,
        reload=False,  # Cambiar a False para evitar el warning
        log_level="info"
    )