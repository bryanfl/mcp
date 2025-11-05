from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from agent import chat
import uvicorn
from fastapi import Body
import time
app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

def chat_stream_generator(message: str):
    # Simular procesamiento en chunks
    responses = [
        "La UTP ofrece las siguientes modalidades de estudio:",
        "*   **Presencial:** Clases en *nuestros* campus.",
        "*   **Carreras para Gente que Trabaja (CGT):** Modalidad semipresencial con horarios flexibles.",
        "*   **Carreras Virtuales a Distancia:** Estudia 100% en línea desde donde te encuentres."
    ]
    
    for response in responses:
        yield response
        time.sleep(0.5)  # Para simular procesamiento

@app.post("/agent/chat")
async def agent_message(message: str = Body(..., embed=True), history: list = Body(default=[], embed=True)):
    return StreamingResponse(
        chat(message, history=history), 
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8103)