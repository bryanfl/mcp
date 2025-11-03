// class MCPAutoConnector {
//     constructor() {
//         this.maxRetries = 5;
//         this.retryCount = 0;
//         this.retryDelay = 1000;
//         this.config = this.getMCPConfig();
//     }

//     getCookie(name) {
//         const value = `; ${document.cookie}`;
//         const parts = value.split(`; ${name}=`);
//         if (parts.length === 2) return parts.pop().split(';').shift();
//         return null;
//     }

//     getMCPConfig() {
//         return {
//             "clientType": "streamable-http",
//             "name": "UTP Informativo",
//             "url": "http://localhost:8102/mcp",
//             "sessionId": "5b552430-ae32-4576-94a0-30c61145b4fb"
//         };
//     }

//     async connect() {
//         try {
//             console.log(`Intentando conexión MCP (intento ${this.retryCount + 1})`);
            
//             const response = await fetch('/mcp', {
//                 method: 'POST',
//                 headers: {
//                     'Content-Type': 'application/json',
//                 },
//                 body: JSON.stringify(this.config)
//             });

//             if (response.ok) {
//                 console.log('✅ Conexión MCP establecida automáticamente');
//                 this.onSuccess();
//             } else {
//                 throw new Error(`HTTP ${response.status}: ${response.statusText}`);
//             }
//         } catch (error) {
//             console.error('❌ Error en conexión MCP:', error);
//             this.retryConnection();
//         }
//     }

//     retryConnection() {
//         if (this.retryCount < this.maxRetries) {
//             this.retryCount++;
//             console.log(`Reintentando en ${this.retryDelay}ms...`);
//             setTimeout(() => this.connect(), this.retryDelay);
//         } else {
//             console.error('❌ No se pudo establecer la conexión MCP después de múltiples intentos');
//         }
//     }

//     onSuccess() {
//         // Opcional: ejecutar acciones después de una conexión exitosa
//         // Por ejemplo, notificar al usuario
//         const event = new CustomEvent('mcp-connected', {
//             detail: { config: this.config }
//         });
//         document.dispatchEvent(event);
//     }

//     start() {
//         // Esperar a que la aplicación esté completamente cargada
//         if (document.readyState === 'complete') {
//             this.connect();
//         } else {
//             window.addEventListener('load', () => {
//                 // Esperar un poco más para asegurar que Chainlit esté listo
//                 setTimeout(() => this.connect(), 1000);
//             });
//         }
//     }
// }

// // Inicializar el conector automático
// const mcpConnector = new MCPAutoConnector();
// mcpConnector.start();