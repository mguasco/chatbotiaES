// chatbot-external-widget.js - Widget para sitios externos con configuraciÃ³n fija
// Variables globales
let isWidgetLoaded = false;
let sessionId = null;

// ConfiguraciÃ³n fija del servidor - NO CAMBIAR
const SERVER_URL = 'https://intranetqa.bas.com.ar/chatbotia';

// FunciÃ³n para generar ID de sesiÃ³n
function generateSessionId() {
    return 'external_' + Math.random().toString(36).substring(2, 15) + Date.now();
}

// PARCHE HTTPS - Forzar HTTPS cuando la pÃ¡gina estÃ¡ en HTTPS
function forceHTTPS(url) {
    if (window.location.protocol === 'https:' && url && url.startsWith('http:')) {
        return url.replace('http:', 'https:');
    }
    return url;
}

// FunciÃ³n principal para enviar pregunta
async function enviarPreguntaExternal() {
    console.log('FunciÃ³n enviarPreguntaExternal llamada');

    const preguntaInput = document.getElementById("question");
    const chatHistoryDiv = document.getElementById("chat-history");

    if (!preguntaInput || !chatHistoryDiv) {
        console.error('Elementos del DOM no encontrados');
        return;
    }

    const pregunta = preguntaInput.value.trim();
    if (!pregunta) {
        console.log('Pregunta vacÃ­a');
        return;
    }

    console.log('Enviando pregunta:', pregunta);

    // Obtener o crear session ID
    if (!sessionId) {
        sessionId = localStorage.getItem('chatSessionId') || generateSessionId();
        localStorage.setItem('chatSessionId', sessionId);
    }

    const originalHistoryContent = chatHistoryDiv.innerHTML;
    chatHistoryDiv.innerHTML += `<p><em>Procesando pregunta...</em></p>`;
    chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;

    try {
        const requestURL = forceHTTPS(`${SERVER_URL}/chat`);
        console.log('Enviando request a:', requestURL);
        
        const response = await fetch(requestURL, {
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
            chatHistoryDiv.innerHTML += `<div class="chat-message assistant-message" style="margin-top: 2px; margin-bottom: 2px; padding: 4px 8px;">${(data.full_conversation || "No se pudo obtener la conversaciÃ³n completa.").replace(/\n/g, "<br>")}</div>`;
        }

        chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;
        preguntaInput.value = '';

    } catch (error) {
        console.error('Error al contactar al chatbot:', error);
        chatHistoryDiv.innerHTML = originalHistoryContent + "<p style='color: red;'>Error de conexiÃ³n. Verifica que el servidor estÃ© funcionando.</p>";
        chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;
    }
}

// FunciÃ³n para limpiar conversaciÃ³n
async function iniciarNuevaConversacionExternal() {
    console.log('Iniciando nueva conversaciÃ³n');

    const chatHistoryDiv = document.getElementById("chat-history");
    const preguntaInput = document.getElementById("question");

    if (preguntaInput) preguntaInput.value = '';
    if (chatHistoryDiv) {
        chatHistoryDiv.innerHTML = "Iniciando nueva conversaciÃ³n...";
        chatHistoryDiv.scrollTop = chatHistoryDiv.scrollHeight;
    }

    if (!sessionId) {
        const newSessionId = generateSessionId();
        localStorage.setItem('chatSessionId', newSessionId);
        sessionId = newSessionId;
        if (chatHistoryDiv) {
            chatHistoryDiv.innerHTML = "Nueva conversaciÃ³n iniciada. Â¡Hola! Â¿En quÃ© puedo ayudarte?";
        }
        console.log("Nueva sesiÃ³n creada:", newSessionId);
        return;
    }

    try {
        const requestURL = forceHTTPS(`${SERVER_URL}/clear_chat_history`);
        console.log('Limpiando conversaciÃ³n en:', requestURL);
        
        const response = await fetch(requestURL, {
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
                chatHistoryDiv.innerHTML = `Error al iniciar nueva conversaciÃ³n: ${errorData.error || 'Error del servidor'}`;
            }
            return;
        }

        const data = await response.json();
        if (data.status === "success") {
            if (chatHistoryDiv) {
                chatHistoryDiv.innerHTML = "Nueva conversaciÃ³n iniciada. Â¡Hola! Â¿En quÃ© puedo ayudarte?";
            }
            const newSessionId = generateSessionId();
            localStorage.setItem('chatSessionId', newSessionId);
            sessionId = newSessionId;
            console.log("SesiÃ³n limpiada, nueva sesiÃ³n:", newSessionId);
        } else {
            if (chatHistoryDiv) {
                chatHistoryDiv.innerHTML = `Error: ${data.message || 'No se pudo iniciar una nueva conversaciÃ³n.'}`;
            }
        }

    } catch (error) {
        console.error('Error al contactar al servidor para nueva conversaciÃ³n:', error);
        if (chatHistoryDiv) {
            chatHistoryDiv.innerHTML = "Error al iniciar nueva conversaciÃ³n. Por favor, intÃ©ntalo de nuevo.";
        }
    }
}

// FunciÃ³n para alternar widget
function toggleExternalChatbot() {
    const panel = document.getElementById("chatbot-panel");
    if (panel) {
        panel.style.display = (panel.style.display === "none" || panel.style.display === "") ? "flex" : "none";
    }
}

// Inyectar CSS idÃ©ntico al widget interno
function injectExternalChatbotCSS() {
    const existingStyle = document.getElementById('external-chatbot-styles');
    if (existingStyle) return; // Ya estÃ¡ inyectado

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
    style.id = 'external-chatbot-styles';
    style.textContent = css;
    document.head.appendChild(style);
}

// FunciÃ³n para crear el widget
function createExternalChatbot() {
    if (isWidgetLoaded) return;
    
    console.log('Creando widget externo...');
    
    // Inyectar CSS
    injectExternalChatbotCSS();
    
    // Crear botÃ³n flotante
    const chatbotButton = document.createElement("button");
    chatbotButton.id = "chatbot-button";
    chatbotButton.innerHTML = "ðŸ’¬";
    chatbotButton.title = "Abrir ChatBot";
    
    // Crear panel del chatbot - ESTRUCTURA IDÃ‰NTICA
    const chatbotPanel = document.createElement("div");
    chatbotPanel.id = "chatbot-panel";
    chatbotPanel.innerHTML = `
        <h4>Hola soy la nueva IA de BAS</h4>
        <button id="new-chat-button">Nueva ConversaciÃ³n</button>
        <div id="chat-history">Â¡Hola! Â¿En quÃ© puedo ayudarte?</div>
        <div id="input-container">
            <input type="text" id="question" placeholder="EscribÃ­ tu pregunta...">
            <button id="send-button">Enviar</button>
        </div>
    `;

    document.body.appendChild(chatbotButton);
    document.body.appendChild(chatbotPanel);

    // Asignar eventos con los mismos IDs
    chatbotButton.addEventListener('click', toggleExternalChatbot);
    
    const sendBtn = document.getElementById("send-button");
    const input = document.getElementById("question");
    const newChatBtn = document.getElementById("new-chat-button");

    if (sendBtn) {
        sendBtn.addEventListener("click", (e) => {
            e.preventDefault();
            console.log('BotÃ³n enviar clickeado');
            enviarPreguntaExternal();
        });
    }

    if (newChatBtn) {
        newChatBtn.addEventListener("click", (e) => {
            e.preventDefault();
            iniciarNuevaConversacionExternal();
        });
    }

    if (input) {
        input.addEventListener("keypress", (event) => {
            if (event.key === "Enter") {
                event.preventDefault();
                console.log('Enter presionado en input');
                enviarPreguntaExternal();
            }
        });
    }

    isWidgetLoaded = true;
    console.log('Widget externo creado exitosamente');
}

// Inicializar cuando el DOM estÃ© listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createExternalChatbot);
} else {
    // DOM ya estÃ¡ listo
    createExternalChatbot();
}

// Exponer funciones globalmente para compatibilidad
window.ExternalChatbot = {
    toggle: toggleExternalChatbot,
    sendMessage: enviarPreguntaExternal,
    clearHistory: iniciarNuevaConversacionExternal
};

// Compatibilidad con versiones anteriores
window.toggleChatbot = toggleExternalChatbot;
window.enviarPregunta = enviarPreguntaExternal;
window.iniciarNuevaConversacion = iniciarNuevaConversacionExternal;