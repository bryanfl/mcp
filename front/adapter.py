from llama_index.core.tools import FunctionTool
from typing import Dict, Any
import chainlit as cl

class MCPToolAdapter:
    def __init__(self, mcp_sessions: Dict):
        self.mcp_sessions = mcp_sessions
    
    def _find_mcp_for_tool(self, tool_name: str) -> str:
        """Encuentra qué conexión MCP tiene la herramienta solicitada"""
        mcp_tools = cl.user_session.get("mcp_tools", {})
        
        for mcp_name, tools in mcp_tools.items():
            for tool in tools:
                if tool["name"] == tool_name:
                    return mcp_name
        raise ValueError(f"Tool {tool_name} not found in any MCP session")
    
    def create_tool_function(self, tool_name: str, tool_description: str):
        """Crea una función dinámica para una herramienta MCP"""
        
        async def tool_function(**kwargs) -> str:
            try:
                # Encontrar la sesión MCP correcta
                mcp_name = self._find_mcp_for_tool(tool_name)
                mcp_sessions = cl.user_session.get("mcp_sessions", {})
                session = mcp_sessions.get(mcp_name)
                
                if not session:
                    return f"Error: No active MCP session for {mcp_name}"
                
                # Llamar a la herramienta MCP
                result = await session.call_tool(tool_name, kwargs)
                return result.content
                
            except Exception as e:
                return f"Error executing tool {tool_name}: {str(e)}"
        
        return tool_function

def create_llamaindex_tools() -> list:
    """Convierte herramientas MCP de Chainlit a FunctionTools de LlamaIndex"""
    
    # Obtener sesiones y herramientas de la sesión de usuario
    mcp_sessions = cl.user_session.get("mcp_sessions", {})
    mcp_tools = cl.user_session.get("mcp_tools", {})
    
    if not mcp_tools:
        return []
    
    adapter = MCPToolAdapter(mcp_sessions)
    tools = []
    
    # Convertir cada herramienta MCP a FunctionTool
    for mcp_name, tool_list in mcp_tools.items():
        for tool_data in tool_list:
            # Crear función dinámica para la herramienta
            tool_fn = adapter.create_tool_function(
                tool_data["name"],
                tool_data["description"]
            )
            
            # Crear FunctionTool para LlamaIndex
            tool = FunctionTool.from_defaults(
                fn=tool_fn,
                name=tool_data["name"],
                description=tool_data["description"],
            )
            tools.append(tool)
    
    return tools