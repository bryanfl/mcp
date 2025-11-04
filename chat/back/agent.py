from google import genai
from google.genai import types
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
import os
import asyncio
from mcp_client import MCPClient

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
mcp_utp_informativo = MCPClient(f"{os.getenv('URL_MCP_INFORMATIVO')}/mcp")
SLM_MODEL = "gemini-2.5-flash-lite"

def get_month_name_spanish(month_number: int) -> str:
    """Devuelve el nombre del mes en español"""
    months = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]
    return months[month_number - 1] if 1 <= month_number <= 12 else "mes desconocido"

def get_urls_utp():
    response = requests.get("https://utp.edu.pe/sitemap.xml")
    
    # 🔥 Usar 'xml' en lugar de 'html.parser' para archivos XML
    soup = BeautifulSoup(response.text, 'xml')

    # Encontrar todos los elementos <loc> y extraer su texto
    loc_values = [loc.get_text(strip=True) for loc in soup.find_all('loc')]

    utp_urls = {
        "url_modalidades": {
            "description": """
                URLs de las modalidades de estudio de la UTP.

                /cgt - Carreras para Gente que Trabaja (semipresencial).
                /carreras-a-distancia - Carreras Virtuales a Distancia.
                https://www.utp.edu.pe/ - Modalidad Presencial y a la vez el Home de UTP el cual muestra informacion general como carreras, modalidades, sedes, facultades, entre otros pero solo a rasgos generales no se debe usar para obtener informacion detallada.
            """,
            "urls": []
        },
        "url_carreras_pregrado": {
            "description": "URLs de las carreras de pregrado de la UTP.",
            "urls": []
        },
        "url_carreras_cgt_semipresencial": {
            "description": "URLs de las carreras de CGT semipresencial de la UTP.",
            "urls": []
        },
        "url_carreras_virtual_a_distancia": {
            "description": "URLs de las carreras virtuales a distancia de la UTP.",
            "urls": []
        },
        "url_facultades": {
            "description": "URLs de las facultades de la UTP.",
            "urls": []
        },
        "url_campus_o_sedes_utp": {
            "description": "URLs de los campus o sedes de la UTP.",
            "urls": []
        }
    }

    for url in loc_values:
        if "/pregrado/facultad" in url:
            utp_urls["url_carreras_pregrado"]["urls"].append(url)
        elif "/cgt/facultad" in url or "/carreras-para-gente-que-trabaja/facultad" in url:
            utp_urls["url_carreras_cgt_semipresencial"]["urls"].append(url)
        elif "/carreras-a-distancia/facultad" in url:
            utp_urls["url_carreras_virtual_a_distancia"]["urls"].append(url)
        elif "https://www.utp.edu.pe/" == url or "https://www.utp.edu.pe/cgt" == url or "https://www.utp.edu.pe/carreras-a-distancia" == url:
            utp_urls["url_modalidades"]["urls"].append(url)
        elif ".pe/facultad" in url or ".pe/arquitectura" in url:
            utp_urls["url_facultades"]["urls"].append(url)
        elif "https://www.utp.edu.pe/pregrado" == url or "https://www.utp.edu.pe/pregrado/ab-testing" == url or "https://www.utp.edu.pe/virtual" == url:
            pass
        else:
            utp_urls["url_campus_o_sedes_utp"]["urls"].append(url)

    return utp_urls

current_date = datetime.now()
current_year = current_date.year
current_month = current_date.month
current_day = current_date.day

system_prompt_utp_informativo = f"""Eres un asistente especializado de la Universidad Tecnológica del Perú (UTP).

    CONTEXTO TEMPORAL ACTUAL:
    - Fecha de hoy: {current_day} de {get_month_name_spanish(current_month)} de {current_year}
    - Año actual: {current_year}
    - Mes actual: {get_month_name_spanish(current_month)}

    INSTRUCCIONES IMPORTANTES:
    - Eres un bot que ayuda a los usuarios con información sobre la UTP.
    - Siempre responde en español.
    - Si no sabes la respuesta, di que no sabes.
    - Usa las herramientas disponibles para buscar información específica sobre la UTP cuando sea necesario.
    - No inventes información.

    DEBES TOMAR COMO BASE ESTAS URLS PARA CONSULTAS SOBRE LA UTP:
    {get_urls_utp()}
"""

def convert_to_gemini_format(my_tools):
    """Convierte tus herramientas al formato que espera Gemini"""
    gemini_tools = []
    
    for tool in my_tools:
        # Convertir el schema a formato Gemini
        parameters = {}
        if tool.inputSchema and "properties" in tool.inputSchema:
            parameters = {
                "type": tool.inputSchema["type"],
                "properties": tool.inputSchema["properties"],
                "required": tool.inputSchema["required"]
            }

        # Crear la función para Gemini
        function_declaration = types.FunctionDeclaration(
            name=tool.name,
            description=tool.description,
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

async def handle_tool_calls(
    tool_calls, 
    mcp_client,
    messages
):
    """Maneja tool calls con confirmación del usuario usando botones"""

    for tool_call in tool_calls:
        tool_name = tool_call.name
        tool_args = dict(tool_call.args) if tool_call.args else {}

        print(tool_name, tool_args)
        # Ejecutar la herramienta MCP
        tool_result = await mcp_client.call_tool(tool_name, tool_args,)
        print(f"Resultado de la herramienta {tool_name}: {tool_result}")
        # Agregar resultado al contexto para segunda llamada
        messages.append(types.Content(
            role="function",
            parts=[types.Part.from_function_response(
                name=tool_name,
                response={"result": tool_result}
            )]
        ))
            
    final_stream = await client.aio.models.generate_content_stream(
        model=SLM_MODEL,
        contents=messages,
        config=types.GenerateContentConfig(
            temperature=0.5,
            system_instruction=system_prompt_utp_informativo
        )
    )

    return final_stream
    
async def chat(message):
    print("message", message)
    tools = await mcp_utp_informativo.list_tools()
    tools = convert_to_gemini_format(tools)

    config = types.GenerateContentConfig(
        tools=tools if tools else None,  # 🔥 No pasar tools si está vacío
        # max_output_tokens=1024,
        temperature= 0.5,
        top_p=0.95,
        top_k=40,
        system_instruction=system_prompt_utp_informativo
    )

    messages = [
        convert_message_to_gemini_format("user", message)
    ]

    stream = await client.aio.models.generate_content_stream(
        model=SLM_MODEL,
        contents=messages,
        config=config
    )

    tool_calls_detected = []
    full_response = ""

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
            yield f"data: {chunk.text}\n\n"
            await asyncio.sleep(0.01)

    print("\nTool calls detectados durante el stream:")

    if len(tool_calls_detected) > 0:

        final_stream = await handle_tool_calls(
            tool_calls_detected, 
            mcp_utp_informativo, 
            messages
        )

        async for chunk in final_stream:
            if chunk.text:
                yield f"data: {chunk.text}\n\n"
                await asyncio.sleep(0.01)