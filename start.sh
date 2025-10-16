#!/bin/bash
# filepath: /home/bryan/main/Empresas/UTP/Proyectos/MCP-UTP/start_all_mcps.sh

echo "🚀 Iniciando todos los servidores MCP..."

# Directorio base
BASE_DIR="/home/bryan/main/Empresas/UTP/Proyectos/MCP-UTP"

# Función para iniciar servidor en background
start_server() {
    local script=$1
    local name=$2
    local port=$3
    
    echo "📡 Iniciando $name en puerto $port..."
    cd "$BASE_DIR"
    python3 "$script" > "logs/${name}.log" 2>&1 &
    echo $! > "pids/${name}.pid"
    echo "✅ $name iniciado (PID: $!)"
}

# Crear directorios para logs y PIDs
mkdir -p logs pids

# Iniciar servidores
start_server "servers/social_networks.py" "utp-mcp" "8001" 
start_server "servers/ads.py" "ads-mcp" "8002"

echo ""
echo "🎉 Todos los servidores MCP iniciados!"
echo "📊 Verifica los logs en: ./logs/"
echo "🛑 Para detener: ./stop_all_mcps.sh"