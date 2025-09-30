import chainlit as cl
from mcp import ClientSession
import asyncio
import ollama
from agent import get_agent

mcp_sessions = {}
available_tools = {}

# Inicializar SLM
SLM_MODEL = "llama3.2:1b"  # Modelo pequeño y rápido

async def stream_agent_response(agent, query: str, msg: cl.Message):
    """Streaming para agentes de LlamaIndex"""
    full_response = ""
    
    try:
        # from llama_index.core.workflow import Context
        # ctx = Context(agent)
        
        # Usar el método run que sí existe en ReActAgent
        handler = agent.run(query)
        
        
        async for ev in handler.stream_events():
            try:
                if hasattr(ev, "delta"):
                    full_response += ev.delta + " "
                    await msg.stream_token(ev.delta + " ")
                elif hasattr(ev, "text"):
                    full_response += ev.text + " "
                    await msg.stream_token(ev.text + " ")
                else:
                    print("El evento no tiene un atributo válido para streaming")
            except Exception as e:
                print(f"Error procesando el evento: {str(e)}")
            
    except Exception as e:
        await msg.stream_token(f"Error: {str(e)}")
    
    return full_response

@cl.on_chat_start
async def start():
    """Inicializar el chat y verificar SLM"""
    await cl.Message(
        content="🤖 **Bot MCP-UTP Instagram** iniciando...\n\n"
                "Verificando modelo de IA local..."
    ).send()
    
    try:
        # Verificar que el modelo esté disponible (sin forzar descarga)
        models = await asyncio.to_thread(ollama.list)
        
        for modelsData in models:
            for model in modelsData[1]:
                if model.model == SLM_MODEL:
                    model_exists = True
                    break
        
        if not model_exists:
            await cl.Message(
                content=f"📥 Descargando modelo {SLM_MODEL}... Esto puede tomar unos minutos."
            ).send()
            await asyncio.to_thread(ollama.pull, SLM_MODEL)
        
        await cl.Message(
            content=f"✅ Modelo **{SLM_MODEL}** listo!\n\n"
                   f"Puedo ayudarte con:\n"
                   f"• 📊 Consultar publicaciones de Instagram UTP\n"
                   f"• 💬 Ver comentarios de publicaciones\n"
                   f"• 📈 Obtener estadísticas\n\n"
                   f"¡Escribe tu pregunta!"
        ).send()
    except Exception as e:
        await cl.Message(
            content=f"⚠️ Error con modelo IA: {str(e)}\n"
                   f"Funcionando en modo básico..."
        ).send()

@cl.on_message
async def main(message: cl.Message):
    """Manejador principal usando LlamaIndex ReActAgent"""
    msg = cl.Message(content="")
    await msg.send()
    
    try:
        # 1. Obtener sesiones y herramientas MCP
        # mcp_sessions = cl.user_session.get("mcp_sessions", {})
        # mcp_tools = cl.user_session.get("mcp_tools", {})
        
        # 2. Crear o obtener agente (cachear en sesión)
        agent = cl.user_session.get("agent")
        if not agent:
            agent = await get_agent()
            cl.user_session.set("agent", agent)
        
        await stream_agent_response(agent, message.content, msg)
        await msg.update()
        
    except Exception as e:
        msg.content = f"⚠️ Error: {str(e)}"
        await msg.update()

@cl.on_mcp_connect
async def on_mcp_connect(connection, session: ClientSession):
    """Manejador para conexiones MCP - ACTUALIZADO"""
    try:
        # 1. Listar herramientas disponibles
        result = await session.list_tools()
        
        # 2. Procesar herramientas
        tools = [{
            "name": t.name,
            "description": t.description,
            "input_schema": t.inputSchema,
        } for t in result.tools]
        
        # 3. Almacenar herramientas Y sesiones en la sesión de usuario
        mcp_tools = cl.user_session.get("mcp_tools", {})
        mcp_tools[connection.name] = tools
        cl.user_session.set("mcp_tools", mcp_tools)
        
        mcp_sessions = cl.user_session.get("mcp_sessions", {})
        mcp_sessions[connection.name] = session
        cl.user_session.set("mcp_sessions", mcp_sessions)
        
        # 4. Invalidar agente para que se recree con nuevas herramientas
        cl.user_session.set("agent", None)
        
        # Mensaje de confirmación
        tools_list = "\n".join([f"• `{tool['name']}`" for tool in tools])
        await cl.Message(
            content=f"✅ **Conectado a MCP:** {connection.name}\n\n"
                   f"🔧 **Herramientas disponibles:**\n{tools_list}"
        ).send()
        
    except Exception as e:
        await cl.Message(
            content=f"⚠️ Error conectando a {connection.name}: {str(e)}"
        ).send()

@cl.on_mcp_disconnect
async def on_mcp_disconnect(name: str, session: ClientSession):
    """Called when an MCP connection is terminated"""
    if name in mcp_sessions:
        del mcp_sessions[name]
    if name in available_tools:
        del available_tools[name]
    
    await cl.Message(
        content=f"❌ Desconectado del servidor MCP: **{name}**",
    ).send()