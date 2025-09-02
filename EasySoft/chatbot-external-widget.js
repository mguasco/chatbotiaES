// chatbot-external-widget.js - Widget para sitios externos
// Configuración del servidor

const CHATBOT_CONFIG = {
    SERVER_URL: 'https://intranetqa.bas.com.ar/chatbotia',  // Sin slash final
    API_VERSION: 'v1',
    WIDGET_TITLE: 'ChatBot BAS',
    POSITION: 'bottom-right'
};

// Variables globales
let isWidgetLoaded = false;
let sessionId = null;

// Función para generar ID de sesión
function generateSessionId() {
    return 'external_' + Math.random().toString(36).substring(2, 15) + Date.now();
}

// Función para forzar HTTPS si es necesario
function ensureProtocol(url) {
    if (window.location.protocol === 'https:' && url.startsWith('http:')) {
        return url.replace('http:', 'https:');
    }
    return url;
}

// Función principal para enviar pregunta
async function enviarPreguntaExternal() {
    const preguntaInput = document.getElementById("external-chatbot-question");
    const chatHistoryDiv = document.getElementById("external-chatbot-history");

    if (!preguntaInput || !chatHistoryDiv) {
        console.error('Elementos del chatbot no encontrados');
        return;
    }

    const pregunta = preguntaInput.value.trim();
    if (!pregunta) return;

    // Obtener o crear session ID
    if (!sessionId) {
        sessionId = localStorage.getItem('externalChatSessionId') || generateSessionId();
        localStorage.setItem('externalChatSessionId', sessionId);
    }

    const originalContent = chatHistoryDiv.innerHTML;
    chatHistoryDiv.innerHTML += `<div class="external-chat-message external-user-message">
        <strong>Tú:</strong> ${pregunta}
    </div>
    <div class="external-chat-message external-loading">
        <em>Procesando...</em>
    </div>`;
    
    chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;
    preguntaInput.value = '';

    try {
        const baseUrl = CHATBOT_CONFIG.SERVER_URL.replace(/\/$/, ''); // Remover slash final
	const requestURL = ensureProtocol(`${baseUrl}/chat`);
        
        const response = await fetch(requestURL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Session-ID': sessionId
            },
            body: JSON.stringify({ question: pregunta })
        });

        if (!response.ok) {
            throw new Error(`Error del servidor: ${response.status}`);
        }

        const data = await response.json();

        // Remover mensaje de carga
        const loadingMsg = chatHistoryDiv.querySelector('.external-loading');
        if (loadingMsg) loadingMsg.remove();

        if (data.error) {
            chatHistoryDiv.innerHTML += `<div class="external-chat-message external-error-message">
                <strong>Error:</strong> ${data.error}
            </div>`;
        } else {
            // Mostrar respuesta del bot
            const botResponse = data.response || 'Lo siento, no pude procesar tu pregunta.';
            chatHistoryDiv.innerHTML += `<div class="external-chat-message external-bot-message">
                <strong>ChatBot:</strong> ${botResponse}
            </div>`;
        }

        chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;

    } catch (error) {
        console.error('Error conectando con chatbot:', error);
        
        // Remover mensaje de carga
        const loadingMsg = chatHistoryDiv.querySelector('.external-loading');
        if (loadingMsg) loadingMsg.remove();
        
        chatHistoryDiv.innerHTML += `<div class="external-chat-message external-error-message">
            <strong>Error:</strong> No se pudo conectar con el chatbot. Intenta de nuevo.
        </div>`;
        chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;
    }
}

// Función para limpiar conversación
async function limpiarConversacionExternal() {
    const chatHistoryDiv = document.getElementById("external-chatbot-history");
    
    if (!sessionId) {
        chatHistoryDiv.innerHTML = `<div class="external-chat-message external-bot-message">
            <strong>ChatBot:</strong> ¡Hola! ¿En qué puedo ayudarte?
        </div>`;
        return;
    }

    try {
        const requestURL = ensureProtocol(`${CHATBOT_CONFIG.SERVER_URL}/clear_chat_history`);
        
        const response = await fetch(requestURL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Session-ID': sessionId
            },
            body: JSON.stringify({})
        });

        if (response.ok) {
            chatHistoryDiv.innerHTML = `<div class="external-chat-message external-bot-message">
                <strong>ChatBot:</strong> Nueva conversación iniciada. ¡Hola! ¿En qué puedo ayudarte?
            </div>`;
            
            // Generar nueva sesión
            sessionId = generateSessionId();
            localStorage.setItem('externalChatSessionId', sessionId);
        } else {
            throw new Error('Error limpiando historial');
        }
    } catch (error) {
        console.error('Error limpiando conversación:', error);
        chatHistoryDiv.innerHTML = `<div class="external-chat-message external-bot-message">
            <strong>ChatBot:</strong> Nueva conversación iniciada. ¡Hola! ¿En qué puedo ayudarte?
        </div>`;
    }
}

// Función para alternar widget
function toggleExternalChatbot() {
    const panel = document.getElementById("external-chatbot-panel");
    if (panel) {
        const isVisible = panel.style.display === "flex";
        panel.style.display = isVisible ? "none" : "flex";
        
        // Enfocar input si se abre
        if (!isVisible) {
            setTimeout(() => {
                const input = document.getElementById("external-chatbot-question");
                if (input) input.focus();
            }, 100);
        }
    }
}

// Función para inyectar CSS
function injectExternalChatbotCSS() {
    const existingStyle = document.getElementById('external-chatbot-styles');
    if (existingStyle) return; // Ya está inyectado

    const css = `
        #external-chatbot-button {
            position: fixed;
            ${CHATBOT_CONFIG.POSITION.includes('bottom') ? 'bottom: 20px;' : 'top: 20px;'}
            ${CHATBOT_CONFIG.POSITION.includes('right') ? 'right: 20px;' : 'left: 20px;'}
            background: linear-gradient(135deg, #007bff, #0056b3);
            color: white;
            border: none;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            font-size: 24px;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,123,255,0.3);
            z-index: 10000;
            transition: all 0.3s ease;
        }
        
        #external-chatbot-button:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 20px rgba(0,123,255,0.4);
        }
        
        #external-chatbot-panel {
            position: fixed;
            ${CHATBOT_CONFIG.POSITION.includes('bottom') ? 'bottom: 90px;' : 'top: 90px;'}
            ${CHATBOT_CONFIG.POSITION.includes('right') ? 'right: 20px;' : 'left: 20px;'}
            width: 380px;
            height: 500px;
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 12px;
            display: none;
            flex-direction: column;
            box-shadow: 0 8px 32px rgba(0,0,0,0.15);
            z-index: 10001;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        
        #external-chatbot-header {
            padding: 16px;
            background: linear-gradient(135deg, #007bff, #0056b3);
            color: white;
            border-radius: 12px 12px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        #external-chatbot-title {
            font-weight: 600;
            font-size: 16px;
        }
        
        #external-new-chat-button {
            background: rgba(255,255,255,0.2);
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
            transition: background 0.2s;
        }
        
        #external-new-chat-button:hover {
            background: rgba(255,255,255,0.3);
        }
        
        #external-chatbot-history {
            flex: 1;
            padding: 16px;
            overflow-y: auto;
            border-bottom: 1px solid #f0f0f0;
            line-height: 1.4;
        }
        
        #external-chatbot-input-container {
            display: flex;
            padding: 12px;
            gap: 8px;
        }
        
        #external-chatbot-question {
            flex: 1;
            padding: 12px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            outline: none;
            font-size: 14px;
            resize: none;
        }
        
        #external-chatbot-question:focus {
            border-color: #007bff;
            box-shadow: 0 0 0 2px rgba(0,123,255,0.1);
        }
        
        #external-send-button {
            padding: 12px 16px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.2s;
        }
        
        #external-send-button:hover {
            background: #0056b3;
        }
        
        .external-chat-message {
            margin: 12px 0;
            padding: 10px 12px;
            border-radius: 8px;
            max-width: 85%;
            word-wrap: break-word;
        }
        
        .external-user-message {
            background: #e3f2fd;
            margin-left: auto;
            text-align: right;
        }
        
        .external-bot-message {
            background: #f1f8e9;
        }
        
        .external-error-message {
            background: #ffebee;
            color: #c62828;
        }
        
        .external-loading {
            background: #f5f5f5;
            font-style: italic;
            color: #666;
        }
        
        .external-chat-message strong {
            display: block;
            margin-bottom: 4px;
            font-size: 12px;
            opacity: 0.8;
        }
        
        /* Responsive */
        @media (max-width: 480px) {
            #external-chatbot-panel {
                width: calc(100vw - 40px);
                height: calc(100vh - 140px);
                left: 20px !important;
                right: 20px !important;
            }
        }
    `;
    
    const style = document.createElement('style');
    style.id = 'external-chatbot-styles';
    style.textContent = css;
    document.head.appendChild(style);
}

// Función para crear el widget
function createExternalChatbot() {
    if (isWidgetLoaded) return;
    
    // Inyectar CSS
    injectExternalChatbotCSS();
    
    // Crear botón flotante
    const chatbotButton = document.createElement("button");
    chatbotButton.id = "external-chatbot-button";
    chatbotButton.innerHTML = "??";
    chatbotButton.title = `Abrir ${CHATBOT_CONFIG.WIDGET_TITLE}`;
    chatbotButton.onclick = toggleExternalChatbot;
    
    // Crear panel del chatbot
    const chatbotPanel = document.createElement("div");
    chatbotPanel.id = "external-chatbot-panel";
    chatbotPanel.innerHTML = `
        <div id="external-chatbot-header">
            <div id="external-chatbot-title">${CHATBOT_CONFIG.WIDGET_TITLE}</div>
            <button id="external-new-chat-button">Nueva Conversación</button>
        </div>
        <div id="external-chatbot-history">
            <div class="external-chat-message external-bot-message">
                <strong>ChatBot:</strong> ¡Hola! ¿En qué puedo ayudarte?
            </div>
        </div>
        <div id="external-chatbot-input-container">
            <textarea id="external-chatbot-question" placeholder="Escribe tu pregunta..." rows="1"></textarea>
            <button id="external-send-button">Enviar</button>
        </div>
    `;

    document.body.appendChild(chatbotButton);
    document.body.appendChild(chatbotPanel);

    // Asignar eventos
    const sendBtn = document.getElementById("external-send-button");
    const input = document.getElementById("external-chatbot-question");
    const newChatBtn = document.getElementById("external-new-chat-button");

    if (sendBtn) {
        sendBtn.addEventListener("click", enviarPreguntaExternal);
    }

    if (newChatBtn) {
        newChatBtn.addEventListener("click", limpiarConversacionExternal);
    }

    if (input) {
        // Auto-resize textarea
        input.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });
        
        // Enter para enviar, Shift+Enter para nueva línea
        input.addEventListener("keypress", function(event) {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                enviarPreguntaExternal();
            }
        });
    }

    isWidgetLoaded = true;
    console.log('ChatBot widget cargado exitosamente');
}

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createExternalChatbot);
} else {
    createExternalChatbot();
}

// Exponer funciones globalmente si es necesario
window.ExternalChatbot = {
    toggle: toggleExternalChatbot,
    sendMessage: enviarPreguntaExternal,
    clearHistory: limpiarConversacionExternal
};