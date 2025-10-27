import chainlit as cl
from google.genai import types

SLM_MODEL = "gemini-2.5-flash-lite"

async def handle_tool_calls(
    client,
    msg, 
    tool_calls, 
    messages, 
    mcp_tools, 
    user_message
):
    """Maneja tool calls con confirmación del usuario usando botones"""

    chat_profile = cl.user_session.get("chat_profile")

    for tool_call in tool_calls:
        tool_name = tool_call.name
        tool_args = dict(tool_call.args) if tool_call.args else {}

        # Ejecutar la herramienta MCP
        tool_result = await execute_mcp_tool(tool_name, tool_args, mcp_tools)

        # Agregar resultado al contexto para segunda llamada
        messages.append(types.Content(
            role="function",
            parts=[types.Part.from_function_response(
                name=tool_name,
                response={"result": tool_result}
            )]
        ))
            
        # await msg.stream_token(f"✅ **{tool_name}**: {tool_result}\n")
    
    # 6. Segunda llamada con los resultados de las herramientas
    # await msg.stream_token("\n📝 **Generando respuesta final...**\n")
    print('messages', messages)
    final_stream = await client.aio.models.generate_content_stream(
        model=SLM_MODEL,
        contents=messages,
        config=types.GenerateContentConfig(
            # max_output_tokens=512,
            temperature=0.5 if chat_profile == "UTP Informativo" else 1.5,
            # system_instruction=system_prompt
            system_instruction=cl.user_session.get("system_prompt", "")
        )
    )

    final_response = ""
    async for chunk in final_stream:
        if chunk.text:
            final_response += chunk.text
            await msg.stream_token(chunk.text)
    
    # ACTUALIZAR HISTORIAL de conversación
    chat_history = cl.user_session.get("chat_history", [])
    chat_history.append(convert_message_to_gemini_format("user", user_message))
    chat_history.append(convert_message_to_gemini_format("model", final_response))

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

def convert_to_gemini_format(my_tools):
    """Convierte tus herramientas al formato que espera Gemini"""
    gemini_tools = []
    
    for tool in my_tools:
        # Convertir el schema a formato Gemini
        parameters = {}
        if "input_schema" in tool and "properties" in tool["input_schema"]:
            parameters = {
                "type": "OBJECT",
                "properties": tool["input_schema"]["properties"],
                "required": tool["input_schema"].get("required", [])
            }
        print(tool["name"])
        # Crear la función para Gemini
        function_declaration = types.FunctionDeclaration(
            name=tool["name"],
            description=tool.get("description", ""),
            parameters=parameters
        )
        
        gemini_tools.append(types.Tool(
            function_declarations=[function_declaration]
        ))
    
    return gemini_tools

def convert_message_to_gemini_format(role, message) -> types.Content:
    """Convierte un mensaje de Chainlit a formato Gemini."""
    return types.Content(
        role=role,
        parts=[types.Part.from_text(text=message)]
    )
