import logging
import shlex
from fastmcp.client import Client as FastMCPClient
import asyncio

logger = logging.getLogger(__name__)

class MCPClient:
    def __init__(self, url_or_command: str):
        self.url_or_command = url_or_command
        self.client = None
        self._context_manager = None
        self.is_command = self._is_npx_command(url_or_command)
        
    def _is_npx_command(self, value: str) -> bool:
        """Detectar si es un comando npx o una URL HTTP"""
        return value.startswith("npx") or not value.startswith("http")
    
    def _parse_command(self, command: str) -> list:
        """Parsear comando en lista de argumentos"""
        return shlex.split(command)
    
    async def connect(self):
        if self.client is None:
            # ✅ Usar FastMCPClient para URLs HTTP
            fastmcp_cm = FastMCPClient(self.url_or_command)
            self.client = await fastmcp_cm.__aenter__()
            self._context_manager = fastmcp_cm

    async def close(self):
        if self.client is not None:
            if self.is_command:
                # BasicMCPClient se cierra automáticamente
                self.client = None
            else:
                # FastMCPClient necesita context manager
                if self._context_manager is not None:
                    await self._context_manager.__aexit__(None, None, None)
                    self.client = None
                    self._context_manager = None

    async def list_tools(self):
        await self.connect()
        print(f"🔍 Cliente tipo: {type(self.client)}")
        tools = await self.client.list_tools()
        return tools

    async def call_tool(self, tool_name: str, arguments: dict):
        await self.connect()
        return await self.client.call_tool(tool_name, arguments)
    
    @property
    def base_url(self):
        """Propiedad para compatibilidad con MultiMCPAdapter"""
        return None if self.is_command else self.url_or_command