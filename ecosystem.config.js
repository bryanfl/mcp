module.exports = {
  apps: [
    {
      name: "agent",
      script: "uv",
      args: "run chat/back/index.py",
      interpreter: "none",
      env_file: ".env",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      time: true
    },
    {
      name: "mcp-utp-info",
      script: "uv",
      args: "run servers/utp.py",
      interpreter: "none",
      env_file: ".env",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      time: true
    },
    {
      name: "chat",
      cwd: "chat/front",          // 🔹 Usa 'cwd' en lugar de 'pwd'
      script: "pnpm",
      args: "start -p 8100",      // 🔹 Pasar el puerto correctamente
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      time: true
    }
    // {
    //   name: "chat",
    //   script: ".venv/bin/chainlit",
    //   args: "run front/index.py --port 8100",
    //   interpreter: "none",
    //   env_file: ".env",
    //   instances: 1,
    //   autorestart: true,
    //   watch: false,
    //   max_memory_restart: "1G",
    //   time: true
    // }
  ]
};