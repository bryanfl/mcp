import chainlit as cl
from mcp import ClientSession
from google import genai
from google.genai import types
from utils.mcp_actions import handle_tool_calls, execute_mcp_tool, convert_to_gemini_format, convert_message_to_gemini_format
from bots.utp_informativo import system_prompt_utp_informativo
from bots.utp_ads import system_prompt_utp_ads

mcp_sessions = {}
available_tools = {}
client = genai.Client(api_key='AIzaSyCLR14IKR7zrvX6BaGMFNn4KNNtNqEX-IU')
SLM_MODEL = "gemini-2.5-flash-lite"

@cl.set_chat_profiles
async def chat_profile():
    return [
        cl.ChatProfile(
            name="UTP ADS",
            markdown_description="Realiza tus consultas sobre campañas en UTP",
            icon="https://www.utp.edu.pe/sites/default/files/favicon_utp_1.png",
        ),
        cl.ChatProfile(
            name="UTP Informativo",
            markdown_description="Realiza tus consultas sobre la UTP en general",
            icon="https://www.utp.edu.pe/sites/default/files/favicon_utp_1.png",
        )
    ]

@cl.password_auth_callback
def auth_callback(username: str, password: str):
    # Fetch the user matching username from your database
    # and compare the hashed password with the value stored in the database
    if (username, password) == ("admin", "utp2025-chat"):
        return cl.User(
            identifier="admin", metadata={"role": "admin", "provider": "credentials"}
        )
    else:
        return None

@cl.on_chat_start
async def on_chat_start():
    chat_profile = cl.user_session.get("chat_profile", [])
    print("chat_profile", chat_profile)
    if chat_profile == "UTP Informativo":
        print("Setting UTP Informativo system prompt")
        cl.user_session.set("system_prompt", system_prompt_utp_informativo)
    elif chat_profile == "UTP ADS":
        cl.user_session.set("system_prompt", system_prompt_utp_ads)
    else:
        cl.user_session.set("system_prompt", "")

@cl.on_message
async def main(message: cl.Message):
    """Deja que el modelo decida cuándo usar herramientas"""
    msg = cl.Message(content="")
    await msg.send()
    
    try:
        chat_history = cl.user_session.get("chat_history", [])
        chat_profile = cl.user_session.get("chat_profile")

        # 1. Preparar herramientas si existen
        mcp_tools = cl.user_session.get("mcp_tools", {})
        
        # 🔥 Usar el chat_profile correcto
        if chat_profile in mcp_tools:
            print("Usando herramientas MCP para el perfil:", chat_profile)
            tools = convert_to_gemini_format(mcp_tools[chat_profile])
        else:
            tools = []  # Sin herramientas si no hay conexión MCP

        config = types.GenerateContentConfig(
            tools=tools if tools else None,  # 🔥 No pasar tools si está vacío
            # max_output_tokens=1024,
            temperature= 0.5 if chat_profile == "UTP Informativo" else 1.5,
            top_p=0.95,
            top_k=40,
            system_instruction=cl.user_session.get("system_prompt", "")
        )

        messages = [] # convert_message_to_gemini_format("model", system_prompt)
        tool_calls_detected = []

        # Agregar historial de conversación (últimos 6 mensajes para no exceder tokens)
        for history_msg in chat_history[-6:]:
            messages.append(history_msg)
        
        full_response = ""

        messages.append(convert_message_to_gemini_format("user", message.content))

        stream = await client.aio.models.generate_content_stream(
            model=SLM_MODEL,
            contents=messages,
            config=config
        )

        async for chunk in stream:
            # 🔥 DETECTAR function calls en el stream
            if chunk.candidates:
                for candidate in chunk.candidates:
                    if candidate.content and candidate.content.parts:
                        for part in candidate.content.parts:
                            # Si hay una llamada a función
                            if hasattr(part, 'function_call') and part.function_call:
                                tool_calls_detected.append(part.function_call)
                                print(f"🔧 Function call detectado: {part.function_call.name}")
            
            # Extraer texto si existe
            if chunk.text:
                full_response += chunk.text
                await msg.stream_token(chunk.text)
        
         # ACTUALIZAR HISTORIAL de conversación
        chat_history.append(convert_message_to_gemini_format("user", message.content))
        chat_history.append(convert_message_to_gemini_format("model", full_response))

        # Manejar tool calls si el modelo decidió usarlas
        print(f"Tool calls: {tool_calls_detected}")

        if tool_calls_detected:
            await handle_tool_calls(
                client,
                msg, 
                tool_calls_detected, 
                messages, 
                mcp_tools, 
                message.content
            )
        else:
            # Mantener sólo los últimos 10 intercambios (20 mensajes)
            if len(chat_history) > 20:
                chat_history = chat_history[-20:]
            
            cl.user_session.set("chat_history", chat_history)

            msg.content = full_response
            await msg.update()
        
    except Exception as e:
        msg.content = f"⚠️ Error: {str(e)}"
        await msg.update()

@cl.step(type="tool")
async def call_tool(mcp_name: str, tool_name: str, tool_args: dict):
    """Ejecuta una herramienta MCP específica"""
    try:
        # Obtener la sesión MCP
        mcp_sessions_dict = cl.user_session.get("mcp_sessions", {})
        mcp_session = mcp_sessions_dict.get(mcp_name)
        
        if not mcp_session:
            return f"Error: No se encontró la sesión MCP {mcp_name}"
        
        # Llamar a la herramienta
        result = await mcp_session.call_tool(tool_name, tool_args)
        # print("Tool result:", result)
        return str(result.content)
        
    except Exception as e:
        return f"Error ejecutando {tool_name}: {str(e)}"

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
        # await cl.Message(
        #     content=f"✅ **Conectado a MCP:** {connection.name}\n\n"
        #            f"🔧 **Herramientas disponibles:**\n{tools_list}"
        # ).send()
        
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