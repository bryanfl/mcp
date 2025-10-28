module.exports = {
  apps: [
    {
      name: "mcp-utp-ads",
      script: "uv",
      args: "run servers/ads.py",
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
      name: "chat-utp",
      script: ".venv/bin/chainlit",
      args: "run front/index.py --port 8100",
      interpreter: "none",
      env_file: ".env",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      time: true
    }
  ]
};