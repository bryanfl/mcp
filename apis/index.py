from fastapi import FastAPI
from dotenv import load_dotenv
# from meta import router as meta_router
from instagram.index import router as instagram_router
from meta.index import router as meta_router
import uvicorn
import os

app = FastAPI()

load_dotenv()
access_token = os.getenv("ACCESS_TOKEN_META")

app.include_router(instagram_router, prefix="/instagram")
app.include_router(meta_router, prefix="/meta")

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)