import chainlit as cl
from mcp import ClientSession
import asyncio
import ollama
from agent import get_agent
from datetime import datetime

mcp_sessions = {}
available_tools = {}

# Inicializar SLM
SLM_MODEL = "qwen2.5:7b"  # Modelo pequeño y rápido

def get_month_name_spanish(month_number: int) -> str:
    """Devuelve el nombre del mes en español"""
    months = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]
    return months[month_number - 1] if 1 <= month_number <= 12 else "mes desconocido"

@cl.on_chat_start
async def on_chat_start():
    """Inicializar el chat y verificar SLM"""
    await cl.Message(
        content="🤖 **Bot MCP-UTP** iniciando...\n\n"
                #"Verificando modelo de IA local..."
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
        
        # await cl.Message(
        #     content=f"✅ Modelo **{SLM_MODEL}** listo!\n\n"
        #            f"Puedo ayudarte con:\n"
        #            f"• 📊 Consultar publicaciones de Instagram UTP\n"
        #            f"• 💬 Ver comentarios de publicaciones\n"
        #            f"• 📈 Obtener estadísticas\n\n"
        #            f"¡Escribe tu pregunta!"
        # ).send()
    except Exception as e:
        await cl.Message(
            content=f"⚠️ Error con modelo IA: {str(e)}\n"
                   f"Funcionando en modo básico..."
        ).send()

@cl.on_message
async def main(message: cl.Message):
    """Deja que el modelo decida cuándo usar herramientas"""
    msg = cl.Message(content="")
    await msg.send()
    
    try:
        chat_history = cl.user_session.get("chat_history", [])

        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.month
        current_day = current_date.day

        # 1. Preparar herramientas si existen
        mcp_tools = cl.user_session.get("mcp_tools", {})
        all_tools = []
        
        for tools in mcp_tools.values():
            for tool in tools:
                all_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool.get("input_schema", {})
                    }
                })
        
        # 2. PROMPT INTELIGENTE que guía al modelo
        system_prompt = f"""Eres un asistente especializado en Instagram UTP.

        CONTEXTO TEMPORAL ACTUAL:
        - Fecha de hoy: {current_day} de {get_month_name_spanish(current_month)} de {current_year}
        - Año actual: {current_year}
        - Mes actual: {get_month_name_spanish(current_month)}

        INSTRUCCIONES IMPORTANTES:
        - Siempre ten en cuenta la fecha actual antes de responder sobre fechas futuras
        - Si el usuario pregunta por fechas futuras, explícale amablemente que son futuras
        - Para fechas pasadas, usa las herramientas disponibles para obtener datos reales
        - Mantén el contexto de la conversación anterior y sé coherente en tus respuestas.
        - SIempre respondes en español.
        - Si no sabes la respuesta, di que no lo sabes.
        - Si el usuario pregunta por datos específicos (números, estadísticas, publicaciones, comentarios, etc.)
          entre fechas pasadas, usa las herramientas disponibles para obtener datos reales.
        - Si el usuario no especifica fechas, asume que se refiere al mes actual.
        - Si el usuario pregunta por datos del mes pasado, úsalo como rango de fechas.
        - Si el usuario pregunta por datos del año pasado, úsalo como rango de fechas.
        - Si el usuario pregunta por datos de una semana específica, úsalo como rango de fechas.
        - Si el usuario pregunta por datos de "hoy", úsalo como rango de fechas.
        - No te explayes mucho en tu respuesta, sé conciso y directo.
        - Solo debes responder a lo que el usuario te pregunta, no generes respuestas adicionales.
        """

        
        messages = [
            {"role": "system", "content": system_prompt},
        ]

        # Agregar historial de conversación (últimos 6 mensajes para no exceder tokens)
        for history_msg in chat_history[-6:]:
            messages.append(history_msg)
        
        # Agregar mensaje actual
        messages.append({"role": "user", "content": message.content})
        
        # 3. SIEMPRE enviar herramientas, pero con instrucciones claras
        response = ollama.chat(
            model=SLM_MODEL,
            messages=messages,
            tools=all_tools if all_tools else None,
            stream=True
        )
        
        full_response = ""
        tool_calls_detected = []
        
        for chunk in response:
            if hasattr(chunk, 'message') and chunk.message:
                content = chunk.message.get('content', '')
                
                # Detectar tool calls
                if hasattr(chunk.message, 'tool_calls') and chunk.message.tool_calls:
                    tool_calls_detected.extend(chunk.message.tool_calls)
                
                if content:
                    full_response += content
                    await msg.stream_token(content)
        
         # ACTUALIZAR HISTORIAL de conversación
        chat_history.append({"role": "user", "content": message.content})
        chat_history.append({"role": "assistant", "content": full_response})

        # 4. Manejar tool calls si el modelo decidió usarlas
        print(f"Tool calls: {tool_calls_detected}")

        if tool_calls_detected:
            await handle_tool_calls(msg, tool_calls_detected, messages, mcp_tools, full_response, message.content)
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

async def handle_tool_calls(msg, tool_calls, messages, mcp_tools, full_response, user_message):
    """Maneja tool calls con confirmación del usuario usando botones"""
    # await msg.stream_token("\n\n🛠️ **Ejecutando herramientas...**\n")

    tool_summary = await create_tool_summary(tool_calls, mcp_tools)

     # Crear acciones/botones
    # actions = [
    #     cl.Action(name="confirm_yes", value="yes", label="✅ Sí, ejecutar búsquedas", payload={"confirm": True}),
    #     cl.Action(name="confirm_no", value="no", label="❌ No, cancelar", payload={"confirm": False})
    # ]
    
    # Enviar mensaje con botones
    # confirmation_msg = await cl.Message(
    #     content=f"🔍 **Solicitud de Búsqueda**\n\n"
    #            f"Para responder a tu pregunta, necesito ejecutar las siguientes búsquedas:\n\n"
    #            f"{tool_summary}\n\n"
    #            f"¿Quieres que proceda con estas búsquedas?",
    #     actions=actions
    # ).send()

    await msg.stream_token(
        f"🔍 **Solicitud de Búsqueda**\n\n"
            f"Para responder a tu pregunta, ejecutare las siguientes búsquedas:\n\n"
            f"{tool_summary}\n\n"
    )

    # await confirmation_msg.send()

    # res = await cl.AskActionMessage(
    #     content="Selecciona una opción:",
    #     actions=actions,
    #     timeout=60
    # ).send()

    # confirmation_msg.actions = []
    # await confirmation_msg.update(content="")

    # if res and res["name"] == "confirm_yes":
    # await msg.stream_token("\n\n✅ **Usuario aceptó - ejecutando búsquedas...**\n")

    for tool_call in tool_calls:
        # await msg.stream_token(f"\n\n🛠️ **Herramienta {tool_call.function.name}**\n")

        if hasattr(tool_call, 'function'):
            tool_name = tool_call.function.name
            tool_args = tool_call.function.arguments

            # await msg.stream_token(f"✅ **Tool Parametros**: {tool_args}\n")

            # Ejecutar la herramienta MCP
            tool_result = await execute_mcp_tool(tool_name, tool_args, mcp_tools)

            print("Tool result:", tool_result)

            # Agregar resultado al contexto para segunda llamada
            messages.append({
                "role": "tool",
                "content": tool_result,
                "tool_call_id": getattr(tool_call, 'id', '')
            })
            
            # await msg.stream_token(f"✅ **{tool_name}**: {tool_result}\n")
    
    # 6. Segunda llamada con los resultados de las herramientas
    await msg.stream_token("\n📝 **Generando respuesta final...**\n")
    
    final_response = ollama.chat(
        model=SLM_MODEL,
        messages=messages,
        stream=True
    )
    
    for chunk in final_response:
        if hasattr(chunk, 'message') and chunk.message:
            content = chunk.message.get('content', '')
            if content:
                full_response += content
                await msg.stream_token(content)
    # else:
    #     await msg.stream_token("\n❌ Búsqueda cancelada por el usuario.\n")
    #     full_response += "\n❌ Búsqueda cancelada por el usuario.\n"
    
    # ACTUALIZAR HISTORIAL de conversación
    chat_history = cl.user_session.get("chat_history", [])
    chat_history.append({"role": "user", "content": user_message})
    chat_history.append({"role": "assistant", "content": full_response})

    cl.user_session.set("chat_history", chat_history)

async def create_tool_summary(tool_calls, mcp_tools):
    """Crea un resumen legible de las herramientas a ejecutar"""
    summary_parts = []
    
    for i, tool_call in enumerate(tool_calls, 1):
        if hasattr(tool_call, 'function'):
            tool_name = tool_call.function.name
            tool_args = tool_call.function.arguments
            
            # Obtener descripción de la herramienta
            tool_description = "Buscar información"
            for tools in mcp_tools.values():
                for tool in tools:
                    if tool['name'] == tool_name:
                        tool_description = tool['description']
                        break
            
            # Formatear parámetros de forma legible
            params_text = format_parameters(tool_args)
            
            summary_parts.append(
                f"**{i}. {tool_name.replace('_', ' ').title()}**\n"
                f"   • **Parámetros**: {params_text}\n"
            )
    
    return "\n".join(summary_parts) if summary_parts else "No se detectaron herramientas específicas"

def format_parameters(params_dict):
    """Formatea los parámetros de forma legible"""
    if not params_dict:
        return "Ninguno"
    
    formatted_params = []
    for key, value in params_dict.items():
        if value:  # Solo mostrar parámetros con valores
            formatted_params.append(f"{key}: {value}")
    
    return ", ".join(formatted_params) if formatted_params else "Parámetros por defecto"

async def execute_mcp_tool(tool_name: str, tool_args: dict, mcp_tools: dict) -> str:
    """Ejecuta una herramienta MCP con los parámetros que el modelo decidió"""
    try:
        # Buscar la sesión MCP correcta
        mcp_sessions_dict = cl.user_session.get("mcp_sessions", {})
        
        for connection_name, session in mcp_sessions_dict.items():
            tools_in_connection = mcp_tools.get(connection_name, [])
            if any(tool['name'] == tool_name for tool in tools_in_connection):
                # 🔥 EJECUTAR con los parámetros que el modelo envió
                result = await session.call_tool(tool_name, tool_args)
                return str(result.content) if hasattr(result, 'content') else str(result)
        
        return f"Error: No se encontró la herramienta {tool_name}"
        
    except Exception as e:
        return f"Error ejecutando {tool_name}: {str(e)}"

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
        print("Tool result:", result)
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