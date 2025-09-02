// chatbot-widget.js - Widget corregido con soporte para subpath

// Variables globales
let SERVER_URL = '';
let isConfigLoaded = false;

// PARCHE HTTPS - Forzar HTTPS cuando la página está en HTTPS
function forceHTTPS(url) {
    if (window.location.protocol === 'https:' && url && url.startsWith('http:')) {
        return url.replace('http:', 'https:');
    }
    return url;
}

function getBaseURL() {
    const protocol = window.location.protocol;
    const host = window.location.host;
    
    // Para desarrollo local, no usar /chatbotia
    if (host.includes('localhost') || host.includes('127.0.0.1')) {
        return `${protocol}//${host}`;  // ? Sin /chatbotia para localhost
    }
    
    // Para producción, mantener /chatbotia
    return `${protocol}//${host}/chatbotia`;
}

// Cargar configuración del servidor
async function loadConfig() {
    try {
        console.log('Cargando configuración...');
        const response = await fetch(forceHTTPS('/chatbotia/config.js'))
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const configScript = await response.text();
        
        // Ejecutar el script de configuración
        const script = document.createElement('script');
        script.textContent = configScript;
        document.head.appendChild(script);
        
        // Usar la configuración cargada
        if (window.CHATBOT_CONFIG) {
            SERVER_URL = window.CHATBOT_CONFIG.SERVER_URL;
            console.log('Configuración cargada. SERVER_URL:', SERVER_URL);
        } else {
            SERVER_URL = window.location.origin + '/chatbotia';
            console.log('Usando fallback URL:', SERVER_URL);
        }
        
        isConfigLoaded = true;
        
    } catch (error) {
        console.error('Error cargando configuración:', error);
        SERVER_URL = window.location.origin + '/chatbotia';
        isConfigLoaded = true;
        console.log('Usando URL de emergencia:', SERVER_URL);
    }
}

// Funciones principales del chatbot
function toggleChatbot() {
    const panel = document.getElementById("chatbot-panel");
    if (panel) {
        panel.style.display = (panel.style.display === "none" || panel.style.display === "") ? "flex" : "none";
    }
}

async function enviarPregunta() {
    console.log('Función enviarPregunta llamada');
    
    if (!isConfigLoaded) {
        console.log('Configuración no cargada, esperando...');
        await loadConfig();
    }

    const preguntaInput = document.getElementById("question");
    const chatHistoryDiv = document.getElementById("chat-history");

    if (!preguntaInput || !chatHistoryDiv) {
        console.error('Elementos del DOM no encontrados');
        return;
    }

    const pregunta = preguntaInput.value.trim();
    if (!pregunta) {
        console.log('Pregunta vacía');
        return;
    }

    console.log('Enviando pregunta:', pregunta);

    const originalHistoryContent = chatHistoryDiv.innerHTML;
    chatHistoryDiv.innerHTML += `<p><em>Procesando pregunta...</em></p>`;
    chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;

    let sessionId = localStorage.getItem('chatSessionId');
    if (!sessionId) {
        sessionId = 'session_' + Math.random().toString(36).substring(2, 15) + Date.now();
        localStorage.setItem('chatSessionId', sessionId);
        console.log('Nueva sesión creada:', sessionId);
    }

    try {
        console.log('Enviando request a:', `${SERVER_URL}/chat`);
        
        const baseURL = getBaseURL();
        const response = await fetch(forceHTTPS(`${baseURL}/chat`), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Session-ID': sessionId
            },
            body: JSON.stringify({ question: pregunta })
        });

        console.log('Response status:', response.status);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Error response:', errorText);
            chatHistoryDiv.innerHTML = originalHistoryContent + `<p style='color: red;'>Error del servidor (${response.status}): ${errorText}</p>`;
            return;
        }

        const data = await response.json();
        console.log('Response data:', data);

        if (data.error) {
            chatHistoryDiv.innerHTML = originalHistoryContent + `<p style='color: red;'>Error: ${data.error}</p>`;
        } else {
            // Limpiar el mensaje de "procesando"
            chatHistoryDiv.innerHTML = originalHistoryContent;
            chatHistoryDiv.innerHTML += `<div class="chat-message assistant-message" style="margin-top: 2px; margin-bottom: 2px; padding: 4px 8px;">${(data.full_conversation || "No se pudo obtener la conversación completa.").replace(/\n/g, "<br>")}</div>`;
        }

        chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;
        preguntaInput.value = '';

    } catch (error) {
        console.error('Error al contactar al chatbot:', error);
        chatHistoryDiv.innerHTML = originalHistoryContent + "<p style='color: red;'>Error de conexión. Verifica que el servidor esté funcionando.</p>";
        chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;
    }
}

async function iniciarNuevaConversacion() {
    console.log('Iniciando nueva conversación');
    
    if (!isConfigLoaded) {
        await loadConfig();
    }

    const chatHistoryDiv = document.getElementById("chat-history");
    const preguntaInput = document.getElementById("question");

    if (preguntaInput) preguntaInput.value = '';
    if (chatHistoryDiv) {
        chatHistoryDiv.innerHTML = "Iniciando nueva conversación...";
        chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;
    }

    let sessionId = localStorage.getItem('chatSessionId');
    if (!sessionId) {
        const newSessionId = 'session_' + Math.random().toString(36).substring(2, 15) + Date.now();
        localStorage.setItem('chatSessionId', newSessionId);
        if (chatHistoryDiv) {
            chatHistoryDiv.innerHTML = "Nueva conversación iniciada. ¡Hola! ¿En qué puedo ayudarte?";
        }
        console.log("Nueva sesión creada:", newSessionId);
        return;
    }

    try {
        const response = await fetch(forceHTTPS(`${SERVER_URL}/clear_chat_history`), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Session-ID': sessionId
            },
            body: JSON.stringify({})
        });

        if (!response.ok) {
            const errorData = await response.json();
            if (chatHistoryDiv) {
                chatHistoryDiv.innerHTML = `Error al iniciar nueva conversación: ${errorData.error || 'Error del servidor'}`;
            }
            return;
        }

        const data = await response.json();
        if (data.status === "success") {
            if (chatHistoryDiv) {
                chatHistoryDiv.innerHTML = "Nueva conversación iniciada. ¡Hola! ¿En qué puedo ayudarte?";
            }
            const newSessionId = 'session_' + Math.random().toString(36).substring(2, 15) + Date.now();
            localStorage.setItem('chatSessionId', newSessionId);
            console.log("Sesión limpiada, nueva sesión:", newSessionId);
        } else {
            if (chatHistoryDiv) {
                chatHistoryDiv.innerHTML = `Error: ${data.message || 'No se pudo iniciar una nueva conversación.'}`;
            }
        }

    } catch (error) {
        console.error('Error al contactar al servidor para nueva conversación:', error);
        if (chatHistoryDiv) {
            chatHistoryDiv.innerHTML = "Error al iniciar nueva conversación. Por favor, inténtalo de nuevo.";
        }
    }
}

// Inyectar CSS básico
function injectCSS() {
    const css = `
        #chatbot-button {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            font-size: 24px;
            cursor: pointer;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            z-index: 1000;
        }
        
        #chatbot-panel {
            position: fixed;
            bottom: 90px;
            right: 20px;
            width: 30%;
            height: 70%;
            background: white;
            border: 1px solid #ccc;
            border-radius: 10px;
            display: none;
            flex-direction: column;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            z-index: 1001;
        }
        
        #chatbot-panel h4 {
            margin: 0;
            padding: 15px;
            background: #007bff;
            color: white;
            border-radius: 10px 10px 0 0;
        }
        
        #new-chat-button {
            margin: 10px;
            padding: 8px 12px;
            background: #28a745;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        
        #chat-history {
            flex: 1;
            padding: 10px;
            overflow-y: auto;
            border-bottom: 1px solid #eee;
        }
        
        #input-container {
            display: flex;
            padding: 10px;
        }
        
        #question {
            flex: 1;
            padding: 8px;
            border: 1px solid #ccc;
            border-radius: 5px;
            margin-right: 5px;
        }
        
        #send-button {
            padding: 8px 12px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        
        .chat-message {
            margin: 10px 0;
            padding: 8px;
            border-radius: 5px;
        }
        
        .user-message {
            background: #e3f2fd;
        }
        
        .assistant-message {
            background: #f1f8e9;
        }
        
        .message-label {
            font-weight: bold;
        }
    `;
    
    const style = document.createElement('style');
    style.textContent = css;
    document.head.appendChild(style);
}

// Crear el widget
async function createWidget() {
    console.log('Creando widget...');
    
    // Inyectar CSS
    injectCSS();
    
    // Crear botón flotante
    const chatbotButton = document.createElement("button");
    chatbotButton.id = "chatbot-button";
    chatbotButton.innerHTML = "💬";
    chatbotButton.title = "Abrir ChatBot";
    
    // Crear panel del chatbot
    const chatbotPanel = document.createElement("div");
    chatbotPanel.id = "chatbot-panel";
    chatbotPanel.innerHTML = `
        <h4>Hola soy la nueva IA de BAS</h4>
        <button id="new-chat-button">Nueva Conversación</button>
        <div id="chat-history">¡Hola! ¿En qué puedo ayudarte?</div>
        <div id="input-container">
            <input type="text" id="question" placeholder="Escribí tu pregunta...">
            <button id="send-button">Enviar</button>
        </div>
    `;

    document.body.appendChild(chatbotButton);
    document.body.appendChild(chatbotPanel);

    // Asignar eventos
    chatbotButton.addEventListener('click', toggleChatbot);
    
    const sendBtn = document.getElementById("send-button");
    const input = document.getElementById("question");
    const newChatBtn = document.getElementById("new-chat-button");

    if (sendBtn) {
        sendBtn.addEventListener("click", (e) => {
            e.preventDefault();
            console.log('Botón enviar clickeado');
            enviarPregunta();
        });
    }

    if (newChatBtn) {
        newChatBtn.addEventListener("click", (e) => {
            e.preventDefault();
            iniciarNuevaConversacion();
        });
    }

    if (input) {
        input.addEventListener("keypress", (event) => {
            if (event.key === "Enter") {
                event.preventDefault();
                console.log('Enter presionado en input');
                enviarPregunta();
            }
        });
    }

    console.log('Widget creado exitosamente');
}

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', async () => {
        await loadConfig();
        await createWidget();
    });
} else {
    // DOM ya está listo
    (async () => {
        await loadConfig();
        await createWidget();
    })();
}

// Exponer funciones globalmente para compatibilidad
window.toggleChatbot = toggleChatbot;
window.enviarPregunta = enviarPregunta;
window.iniciarNuevaConversacion = iniciarNuevaConversacion;