import chainlit as cl
from google import genai
from bots.utp_informativo import system_prompt_utp_informativo
from bots.utp_ads import system_prompt_utp_ads
from dotenv import load_dotenv
import os
import requests

load_dotenv()

mcp_sessions = {}
available_tools = {}
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
SLM_MODEL = "gemini-2.5-flash-lite"

@cl.set_chat_profiles
async def chat_profile():
    return [
        # cl.ChatProfile(
        #     name="UTP ADS",
        #     markdown_description="Realiza tus consultas sobre campañas en UTP",
        #     icon="https://www.utp.edu.pe/sites/default/files/favicon_utp_1.png",
        # ),
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

    if chat_profile == "UTP Informativo":
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

        url = 'http://localhost:8103/agent/chat'
        headers = {"Authorization": "Bearer TU_TOKEN"}
        data = {"message": message.content}
        full_response = ""

        with requests.post(url, headers=headers, json=data, stream=True) as response:
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode("utf-8")
                    print(decoded_line)
                    full_response += decoded_line
                    await msg.stream_token(decoded_line)

        # msg.content = "esto es una respuesta"
        # await msg.update()
        
    except Exception as e:
        msg.content = f"⚠️ Error: {str(e)}"
        await msg.update()