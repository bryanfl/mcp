#!/bin/bash
# filepath: /home/bryan/main/Empresas/UTP/Proyectos/MCP-UTP/stop_all_mcps.sh

echo "🛑 Deteniendo todos los servidores MCP..."

# Detener por PIDs guardados
for pidfile in pids/*.pid; do
    if [ -f "$pidfile" ]; then
        pid=$(cat "$pidfile")
        name=$(basename "$pidfile" .pid)
        echo "🔴 Deteniendo $name (PID: $pid)..."
        kill $pid 2>/dev/null
        rm "$pidfile"
    fi
done

# Backup: matar por puerto
echo "🧹 Limpieza adicional..."
pkill -f "python.*mcp" 2>/dev/null

echo "✅ Todos los servidores detenidos"