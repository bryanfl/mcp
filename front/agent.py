from typing import Dict
from llama_index.llms.ollama import Ollama
from llama_index.core.agent.workflow import ReActAgent
import asyncio
from adapter import create_llamaindex_tools

SYSTEM_PROMPT = """
Eres un agente especializado en la Universidad Tecnológica del Perú (UTP).
Tienes acceso a herramientas de Instagram UTP a través del protocolo MCP.

HERRAMIENTAS DISPONIBLES:
- Herramientas de Instagram UTP para consultar publicaciones, comentarios y estadísticas

REGLAS:
- SIEMPRE responde en español al usuario
- Usa las herramientas cuando necesites información específica de Instagram UTP
- Sé natural y conversacional
- Si ya tienes la información, NO repitas el uso de herramientas
- Combina información de múltiples fuentes si es necesario

EJEMPLOS:
- "¿Qué publicaciones recientes tiene la UTP?" → Usar herramienta de publicaciones
- "Quiero ver comentarios" → Usar herramienta de comentarios
- "Estadísticas de engagement" → Usar herramienta de estadísticas
"""

async def get_agent():
    # 1. Convertir herramientas MCP a formato LlamaIndex
    tools = create_llamaindex_tools()
    
    # 2. Configurar LLM con Ollama
    llm = Ollama(
        base_url="http://localhost:11434", 
        model="llama3.2:1b",
        request_timeout=120.0,
        additional_kwargs={
            "num_gpu": 128,
            "num_thread": 4,
            "num_ctx": 4096,
            "num_batch": 512,
        }
    )

    # 3. Crear agente ReAct con herramientas
    agent = ReActAgent(
        llm=llm, 
        tools=tools, 
        system_prompt=SYSTEM_PROMPT, 
        verbose=True,  # Útil para debugging
    )

    return agent