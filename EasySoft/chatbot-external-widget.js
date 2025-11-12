// chatbot-widget.js - Widget interno con hora usando regex - VERSIÓN UNIVERSAL (MEJORADA)
// Encoding: UTF-8

// Variables globales
let SERVER_URL = '';
let isConfigLoaded = false;
let salesiqLoaded = false;
let processingTimeout = null;
// ? NUEVO: recordar el último mensaje del usuario para posicionar el scroll
let lastUserMsgId = null;
// ⭐ NUEVO: Variable para controlar si está procesando una pregunta
let isProcessingQuestion = false;

// ?? NUEVO: Historial de preguntas del usuario para SalesIQ (máx. 3)
const USER_HISTORY_KEY = 'chatUserHistory';

// ? NUEVO: Detectar si estamos en ambiente externo
const isExternalEnvironment = !(
    // Estos dominios no se consideran externos (son donde está alojado el backend)
    window.location.hostname.includes('intranetqa.bas.com.ar') || 
    window.location.hostname.includes('localhost') || 
    window.location.hostname.includes('127.0.0.1')
);

// ? NUEVO: Si es ambiente externo, configurar directamente
if (isExternalEnvironment) {
    SERVER_URL = 'https://intranetqa.bas.com.ar/chatbotia';
    isConfigLoaded = true;
}

// PARCHE HTTPS - Forzar HTTPS cuando la página está en HTTPS
function forceHTTPS(url) {
    if (window.location.protocol === 'https:' && url && url.startsWith('http:')) {
        return url.replace('http:', 'https:');
    }
    return url;
}

function getBaseURL() {
    // ? NUEVO: Si es ambiente externo, usar SERVER_URL directamente
const isExternalEnvironment = !(
    // Estos dominios no se consideran externos (son donde está alojado el backend)
    window.location.hostname.includes('intranetqa.bas.com.ar') || 
    window.location.hostname.includes('localhost') || 
    window.location.hostname.includes('127.0.0.1')
);    

    if (isExternalEnvironment) {
        return SERVER_URL;
    }
    
    const protocol = window.location.protocol;
    const host = window.location.host;
    
    // Para desarrollo local, no usar /chatbotia
    if (host.includes('localhost') || host.includes('127.0.0.1')) {
        return `${protocol}//${host}`;
    }
    
    // Para producción, mantener /chatbotia
    return `${protocol}//${host}/chatbotia`;
}

// ? NUEVO: Función para generar ID de sesión
function generateSessionId() {
    const prefix = isExternalEnvironment ? 'external_' : 'session_';
    return prefix + Math.random().toString(36).substring(2, 15) + Date.now();
}

// Función para obtener hora formateada
function getCurrentTime() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    return `${hours}:${minutes}`;
}

// ?? Escapar HTML del usuario para evitar XSS
function escapeHtml(str) {
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// ?? Extraer SOLO el último bloque del asistente desde full_conversation
function extractLastAssistantBlock(fullHtml) {
    if (!fullHtml) return "";
    // 1) Intento con DOM real (navegador)
    try {
        const container = document.createElement('div');
        container.innerHTML = fullHtml;
        const allAssistant = container.querySelectorAll('.chat-message.assistant-message, .assistant-message');
        if (allAssistant && allAssistant.length > 0) {
            const last = allAssistant[allAssistant.length - 1];
            return last.outerHTML || last.innerHTML || "";
        }
    } catch (_) { /* ignore */ }
    // 2) Fallback con regex (toma el último div con clase assistant-message)
    const regex = /(<div[^>]*class=['"][^'"]*assistant-message[^'"]*['"][^>]*>[\s\S]*?<\/div>)/gi;
    let match, lastMatch = "";
    while ((match = regex.exec(fullHtml)) !== null) {
        lastMatch = match[1];
    }
    return lastMatch;
}

// Limpiar señales de reformulación
function stripReformulatedHints(html, originalQuestion, dataObj) {
    if (!html) return "";
    let out = String(html);
    out = out.replace(/<strong>\s*Pregunta\s+reformulada:\s*<\/strong>[\s\S]*?(?:<br\s*\/?>|\n|$)/gi, "");
    out = out.replace(/<b>\s*Pregunta\s+reformulada:\s*<\/b>[\s\S]*?(?:<br\s*\/?>|\n|$)/gi, "");
    out = out.replace(/\b(?:Pregunta\s+reformulada|Reformulada|Reformulated\s+question)\s*:\s*[^\n<]*(?:<br\s*\/?>|\n|$)/gi, "");
    out = out.replace(/^(?:\s*<[^>]+>)*\s*(?:"|\"|\')?[([][^)\]]{5,160}[)\]](?:"|\"|\')?\s*(?:<br\s*\/?>|\n)/, "");
    const rq = (dataObj && (dataObj.reformulated_question || dataObj.question_reformulated || "")) || "";
    if (rq) {
        const escRQ = escapeHtml(rq).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
        out = out.replace(new RegExp(escRQ, "gi"), "");
        const plainRQ = rq.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
        out = out.replace(new RegExp(plainRQ, "gi"), "");
    }
    if (originalQuestion) {
        const escQ = escapeHtml(originalQuestion).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
        out = out.replace(new RegExp(`^\\s*${escQ}\\s*(?:<br\\s*/?>|\\n)+`, "i"), "");
    }
    return out;
}

// Normaliza párrafos cuando el bloque del asistente viene sin <p>/<br>
function normalizeAssistantParagraphs(blockHtml) {
    if (!blockHtml) return blockHtml;
    try {
        const container = document.createElement('div');
        container.innerHTML = blockHtml;
        const msg = container.querySelector('.assistant-message') || container.firstElementChild;
        if (!msg) return blockHtml;

        const inner = msg.innerHTML;
        // Si ya tiene estructura de párrafos o breaks, no tocar
        if (/<\s*(p|br|ul|ol|li)\b/i.test(inner)) {
            return blockHtml;
        }

        // Normalizar saltos de línea del backend
        let normalized = inner.replace(/\r\n/g, '\n');
        normalized = normalized.replace(/[ \t]+\n/g, '\n').replace(/\n[ \t]+/g, '\n');
        // Doble salto -> nuevo párrafo
        normalized = normalized.replace(/\n\s*\n/g, '</p><p>');
        // Salto simple -> <br>
        normalized = normalized.replace(/\n/g, '<br>');
        msg.innerHTML = `<p>${normalized}</p>`;
        return container.innerHTML;
    } catch (_) {
        return blockHtml;
    }
}

// Helper: posicionar el scroll en la última pregunta del usuario
function scrollToLastQuestion() {
    const chatHistoryDiv = document.getElementById("chat-history");
    if (!chatHistoryDiv) return;

    const userMessages = chatHistoryDiv.querySelectorAll('.user-message');
    if (!userMessages || userMessages.length === 0) return;

    const target = userMessages[userMessages.length - 1];

    requestAnimationFrame(() => {
        try {
            target.scrollIntoView({ behavior: 'auto', block: 'start' });
        } catch (e) {
            const top = target.offsetTop || 0;
            chatHistoryDiv.scrollTop = Math.max(top - 10, 0);
        }
    });
}

// ? NUEVO: posicionar el scroll en un elemento por id (usado en escalación)
function scrollToElementById(id) {
    if (!id) return;
    const target = document.getElementById(id);
    const chatHistoryDiv = document.getElementById("chat-history");
    if (!target || !chatHistoryDiv) return;
    requestAnimationFrame(() => {
        try {
            target.scrollIntoView({ behavior: 'auto', block: 'start' });
        } catch (e) {
            const top = target.offsetTop || 0;
            chatHistoryDiv.scrollTop = Math.max(top - 10, 0);
        }
    });
}

// ?? NUEVAS FUNCIONES: Gestión del historial de preguntas para SalesIQ
// Función para agregar la pregunta del usuario al historial
function addUserQuestionToHistory(question) {
    try {
        let history = JSON.parse(localStorage.getItem(USER_HISTORY_KEY) || '[]');
        // Limpiar el historial para evitar preguntas vacías
        const cleanedQuestion = String(question || '').trim();
        if (cleanedQuestion) {
            // Agregar la nueva pregunta
            history.push(cleanedQuestion);
            // Mantener solo las últimas 3 preguntas
            if (history.length > 3) {
                history = history.slice(-3);
            }
            localStorage.setItem(USER_HISTORY_KEY, JSON.stringify(history));
        }
    } catch (e) {
        console.error('Error al gestionar el historial de preguntas:', e);
    }
}

// Función para obtener las últimas N preguntas concatenadas
function getContextualUserQuestions() {
    try {
        const history = JSON.parse(localStorage.getItem(USER_HISTORY_KEY) || '[]');
        if (history.length === 0) return 'Última pregunta no disponible.';
        
        // Formato para el agente: [1] Pregunta1 | [2] Pregunta2 | [3] Pregunta3
        return history.map((q, index) => `[${index + 1}] ${q}`).join(' | ');
        
    } catch (e) {
        return 'Error al obtener historial de preguntas.';
    }
}
// FIN NUEVAS FUNCIONES

// ⭐ NUEVO: Función para actualizar estado de botones según procesamiento
function updateButtonStates(isProcessing) {
    const sendButton = document.getElementById("send-button");
    const questionInput = document.getElementById("question");
    
    if (sendButton) {
        if (isProcessing) {
            // Deshabilitar mientras procesa
            sendButton.disabled = true;
            sendButton.style.opacity = "0.5";
            sendButton.style.cursor = "not-allowed";
        } else {
            // Habilitar cuando termina
            sendButton.disabled = false;
            sendButton.style.opacity = "1";
            sendButton.style.cursor = "pointer";
        }
    }
    
    if (questionInput) {
        questionInput.disabled = isProcessing;
        questionInput.style.opacity = isProcessing ? "0.7" : "1";
        
        // IMPORTANTE: Si estamos habilitando el campo, asegurar que tenga el foco
        if (!isProcessing) {
            setTimeout(() => {
                questionInput.focus();
            }, 50);
        }
    }
}

// Función para cargar SalesIQ dinámicamente
function loadSalesIQ() {
    if (salesiqLoaded) {
        console.log('\u{1F4CB} SalesIQ ya está cargado');
        return;
    }
    
    console.log('\u{1F504} Cargando widget de SalesIQ...');
    
    // Configurar Zoho SalesIQ
    window.$zoho = window.$zoho || {};
    window.$zoho.salesiq = window.$zoho.salesiq || {
        widgetcode: "siqb25b943eaf1f92c7ed086df7176833fd70631f401d4249c45a91bf30aa6ab02f",
        values: {},
        ready: function() {
            console.log('\u{2705} SalesIQ cargado y listo');
        }
    };
    
    // Crear script de SalesIQ
    const script = document.createElement('script');
    script.type = 'text/javascript';
    script.id = 'zsiqscript';
    script.defer = true;
    script.src = 'https://salesiq.zohopublic.com/widget';
    
    // Evitar duplicados
    const existingScript = document.getElementById('zsiqscript');
    if (existingScript) {
        existingScript.remove();
    }
    
    const firstScript = document.getElementsByTagName('script')[0];
    firstScript.parentNode.insertBefore(script, firstScript);
    
    salesiqLoaded = true;
    console.log('\u{1F4E6} Script de SalesIQ insertado en DOM');
}

// Función para enviar contexto al agente de SalesIQ
function sendContextToSalesIQ(sessionContext, lastQuestion, escalationReason) {
    try {
        if (!window.$zoho || !window.$zoho.salesiq) {
            console.warn('\u{26A0}\u{FE0F} SalesIQ no está disponible para enviar contexto');
            return false;
        }
        
        // ?? OBTENER EL CONTEXTO DE PREGUNTAS
        const contextualQuestions = getContextualUserQuestions(); 

        // Mapeo de razones a texto legible
        const reasonMap = {
            'user_explicit_request': 'Solicitud explícita del usuario',
            'no_context': 'No se encontró información relacionada a la consulta',
            'low_similarity': 'Información encontrada no relacionada con la consulta',
            'sensitive_topic': 'Tema sensible que requiere atención personalizada',
            'multiple_failed_attempts': 'Múltiples intentos fallidos de respuesta'
        };
        
        const readableReason = reasonMap[escalationReason] || escalationReason;
        
        // Preparar el mensaje contextual para el agente
        const contextMessage = `
\u{1F916} TRANSFERENCIA DESDE CHATBOT IA
\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}

\u{1F4CB} RAZÓN DE ESCALACIÓN: ${readableReason}

\u{2753} ÚLTIMAS PREGUNTAS (CONCATENADAS):
${contextualQuestions}

\u{1F4AC} CONTEXTO DE LA CONVERSACIÓN:
${sessionContext || 'Sin historial previo'}

\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}\u{2500}
\u{23F0} ${new Date().toLocaleString('es-AR')}
        `.trim();
        
        // Enviar información al agente usando visitor.info
        window.$zoho.salesiq.visitor.info({
            // ?? CAMBIO: Usar las preguntas concatenadas
            "Ultima_Pregunta_IA": contextualQuestions, 
            "Razon_Escalacion": readableReason,
            "Contexto_Conversacion": sessionContext || 'Sin historial',
            "Fecha_Escalacion": new Date().toISOString()
        });

	// Mantenemos lastQuestion (la última) para el visitor.question, que se usa para iniciar el chat
	window.$zoho.salesiq.visitor.question(contextualQuestions);
        
        // También enviar como mensaje visible para el agente
        if (window.$zoho.salesiq.chat && typeof window.$zoho.salesiq.chat.message === 'function') {
            window.$zoho.salesiq.chat.message(contextMessage);
        }
        
        console.log('\u{2705} Contexto enviado a SalesIQ:', {
            // ?? CAMBIO: Mostrar las preguntas contextuales en el log
            lastQuestion: contextualQuestions.substring(0, 50) + '...',
            reason: readableReason
        });
        
        return true;
        
    } catch (error) {
        console.error('\u{274C} Error enviando contexto a SalesIQ:', error);
        return false;
    }
}

// ⭐ MODIFICADA: Función para mostrar escalación a humanos (mejorada)
function showHumanEscalation(escalationData) {
    const chatHistoryDiv = document.getElementById("chat-history");
    
    if (!chatHistoryDiv) {
        console.error('\u{274C} No se encontró chat-history div');
        return;
    }
    
    // Extraer datos de escalación
    const reason = escalationData.escalation_reason || escalationData || 'user_request';
    // lastQuestion es la última, usada para iniciar la conversación en SalesIQ
    const lastQuestion = escalationData.user_question || 'Pregunta no disponible';
    const sessionContext = escalationData.session_context || 'Sin contexto disponible';
    
    const currentTime = getCurrentTime();
    
    // ⭐ NUEVO: Generar ID único para el botón de consultor
    const escalationId = `escalation-${Date.now()}`;
    
    const escalationHtml = `
        <div class="chat-message system-message" style="background: #cfdcf4ff; border-left: 4px solid #b3ddf6ff; margin: 10px 0; padding: 15px; border-radius: 8px;">
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <span style="font-size: 24px; margin-right: 10px;">\u{1F464}</span>
                <strong style="color: #212529;">Conectando con un consultor</strong>
                <span style="margin-left: auto; font-size: 11px; color: #666;">${currentTime}</span>
            </div>
            <p style="margin: 5px 0; color: #212529;">Te estoy derivando a un especialista que podrá ayudarte mejor con tu consulta.</p>
            <div style="margin-top: 15px;">
                <button id="${escalationId}" class="salesiq-button escalation-btn" data-reason="${reason}" data-question="${encodeURIComponent(lastQuestion)}" data-context="${encodeURIComponent(sessionContext)}" style="
                    background: #6574cd; 
                    color: white; 
                    border: none; 
                    padding: 12px 24px; 
                    border-radius: 6px; 
                    cursor: pointer;
                    font-weight: bold;
                    font-size: 14px;
                    transition: background-color 0.3s;
                ">\u{1F4AC} Hablar con un consultor</button>
                <div id="${escalationId}-status" style="margin-top: 8px; font-size: 12px; color: #6574cd;"></div>
            </div>
        </div>
    `;
    
    chatHistoryDiv.innerHTML += escalationHtml;

    // ? Posicionar el scroll en la última pregunta del usuario tras insertar el bloque de escalación
    scrollToElementById(lastUserMsgId);
    
    // ⭐ NUEVO: Usar delegación de eventos para manejar botones de consultor
    setupEscalationButtons();
}

// ⭐ NUEVO: Configurar todos los botones de escalación en el chat
function setupEscalationButtons() {
    // Remover listeners previos
    document.querySelectorAll('.escalation-btn').forEach(btn => {
        btn.removeAttribute('onclick');
    });
    
    // Usar delegación de eventos en el chat-history
    const chatHistoryDiv = document.getElementById("chat-history");
    if (!chatHistoryDiv) return;
    
    // Eliminar listener previo si existe
    if (chatHistoryDiv._hasEscalationListener) {
        return;
    }
    
    // Agregar nuevo listener usando delegación
    chatHistoryDiv.addEventListener('click', function(event) {
        // Buscar si el click fue en un botón de escalación
        let targetBtn = event.target;
        while (targetBtn && !targetBtn.classList.contains('escalation-btn')) {
            if (targetBtn === chatHistoryDiv) {
                targetBtn = null;
                break;
            }
            targetBtn = targetBtn.parentElement;
        }
        
        // Si no es un botón de escalación, salir
        if (!targetBtn) return;
        
        // Ejecutar acción de escalación
        const btnId = targetBtn.id;
        const reason = targetBtn.getAttribute('data-reason');
        const question = decodeURIComponent(targetBtn.getAttribute('data-question') || '');
        const context = decodeURIComponent(targetBtn.getAttribute('data-context') || '');
        
        // Obtener el div de estado asociado
        const statusDiv = document.getElementById(`${btnId}-status`);
        
        // Procesar la escalación
        activateSalesIQConsultant(targetBtn, statusDiv, reason, question, context);
    });
    
    // Marcar que ya tiene listener para evitar duplicados
    chatHistoryDiv._hasEscalationListener = true;
}

// ⭐ NUEVO: Función separada para activar SalesIQ (antes estaba dentro de showHumanEscalation)
function activateSalesIQConsultant(activateButton, statusDiv, reason, lastQuestion, sessionContext) {
    console.log('\u{1F680} Activando widget de SalesIQ...');
    
    // Minimizar widget de IA inmediatamente
    minimizeChatbotWidget();
    
    // Actualizar estado visual
    activateButton.disabled = true;
    activateButton.innerHTML = '\u{1F504} Conectando...';
    activateButton.style.background = '#6574cd';
    if (statusDiv) {
        statusDiv.textContent = 'Preparando chat y enviando contexto...';
    }
    
    // Cargar SalesIQ si no está cargado
    loadSalesIQ();
    
    // Esperar un momento y luego abrir el chat
    setTimeout(() => {
        if (window.$zoho && window.$zoho.salesiq) {
            try {
                // Enviar contexto antes de abrir el chat
                const contextSent = sendContextToSalesIQ(sessionContext, lastQuestion, reason);
                
                if (statusDiv && contextSent) {
                    statusDiv.textContent = '\u{2705} Contexto enviado al agente...';
                }
                
                // Pequeña pausa para asegurar que el contexto llegue
                setTimeout(() => {
                    // Intentar diferentes métodos para abrir SalesIQ
                    if (window.$zoho.salesiq.chat && typeof window.$zoho.salesiq.chat.start === 'function') {
                        window.$zoho.salesiq.chat.start();
                        console.log('\u{2705} Chat de SalesIQ iniciado con .start()');
                        if (statusDiv) {
                            statusDiv.textContent = '\u{2705} Chat derivado - Contexto enviado al agente';
                        }
                        activateButton.innerHTML = '\u{2705} Ya has sido derivado';
                        activateButton.style.background = '#b9b9b9ff';
                    } else if (window.$zoho.salesiq.floatbutton && typeof window.$zoho.salesiq.floatbutton.click === 'function') {
                        window.$zoho.salesiq.floatbutton.click();
                        console.log('\u{2705} Chat de SalesIQ iniciado con .click()');
                        if (statusDiv) {
                            statusDiv.textContent = '\u{2705} Chat derivado - Contexto enviado al agente';
                        }
                        activateButton.innerHTML = '\u{2705} Chat derivado';
                        activateButton.style.background = '#b9b9b9ff';
                    } else {
                        throw new Error('Métodos de SalesIQ no disponibles');
                    }
                    
                    // Agregar botón para restaurar widget de IA
                    //addRestoreWidgetButton();
                    
                }, 500);
                
            } catch (error) {
                console.log('\u{26A0}\u{FE0F} Error iniciando SalesIQ:', error);
                console.log('\u{1F504} Abriendo página de contacto como fallback...');
                
                // Fallback: abrir ventana de contacto
                window.open('https://bas.com.ar/contacto', '_blank');
                
                // Restaurar widget ya que no se pudo conectar
                restoreChatbotWidget();
                
                if (statusDiv) {
                    statusDiv.textContent = '\u{2197}\u{FE0F} Página de contacto abierta';
                }
                activateButton.innerHTML = '\u{2197}\u{FE0F} Contacto abierto';
                activateButton.style.background = '#17a2b8';
            }
        } else {
            console.log('\u{26A0}\u{FE0F} SalesIQ no disponible, abriendo fallback...');
            
            // Fallback: abrir ventana de contacto
            window.open('https://bas.com.ar/contacto', '_blank');
            
            // Restaurar widget ya que no se pudo conectar
            restoreChatbotWidget();
            
            if (statusDiv) {
                statusDiv.textContent = '\u{2197}\u{FE0F} Página de contacto abierta';
            }
            activateButton.innerHTML = '\u{2197}\u{FE0F} Contacto abierto';
            activateButton.style.background = '#17a2b8';
        }
    }, 2000);
}

// Minimizar widget de IA
function minimizeChatbotWidget() {
    const panel = document.getElementById("chatbot-panel");
    const button = document.getElementById("chatbot-button");
    
    if (panel) {
        panel.style.display = "none";
        console.log('\u{1F4F1} Widget de IA minimizado');
    }
    
    if (button) {
        // ?? Ícono de dormir cuando se minimiza
        button.innerHTML = "\u{1F4A4}";
        button.title = "Widget de IA (en segundo plano - SalesIQ activo)";
        button.style.opacity = "0.6";
    }
}

// Restaurar widget de IA
function restoreChatbotWidget() {
    const panel = document.getElementById("chatbot-panel");
    const button = document.getElementById("chatbot-button");
    
    if (button) {
        // ?? Burbuja de chat visible
        button.innerHTML = "\u{1F4AC}";
        button.title = "Abrir ChatBot";
        button.style.opacity = "1";
    }
    
    console.log('\u{1F4F1} Widget de IA restaurado');
}

// Función para actualizar estado de procesamiento
function updateProcessingStatus(chatHistoryDiv, elapsedSeconds) {
    const messages = [
        'Procesando pregunta...',
        'Buscando información...',
        'Analizando información...',
        'Preparando respuesta...',
        'Esto está tomando más tiempo de lo usual...'
    ];
    
    let messageIndex = Math.min(Math.floor(elapsedSeconds / 3), messages.length - 1);
    
    const processingElement = chatHistoryDiv.querySelector('.processing-message');
    if (processingElement) {
        processingElement.innerHTML = `<em>${messages[messageIndex]}</em>`;
    }
}

// Cargar configuración del servidor
async function loadConfig() {
    // ? NUEVO: Si es ambiente externo, ya está configurado
    if (isExternalEnvironment) {
        return;
    }
    
    try {
    	console.log('Cargando configuración...');
    	const response = await fetch(forceHTTPS(`${getBaseURL()}/config.js`));   
	if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const configScript = await response.text();
        
        const script = document.createElement('script');
        script.textContent = configScript;
        document.head.appendChild(script);
        
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
    // Evitar enviar preguntas mientras se procesa otra
    if (isProcessingQuestion) {
        console.log('Ya hay una pregunta en proceso, espera...');
        return;
    }
    
    if (!isConfigLoaded) {
        await loadConfig();
    }

    const preguntaInput = document.getElementById("question");
    const chatHistoryDiv = document.getElementById("chat-history");

    if (!preguntaInput || !chatHistoryDiv) {
        return;
    }

    const pregunta = preguntaInput.value.trim();
    if (!pregunta) {
        return;
    }
    
    // Guardar referencia al elemento que tiene el foco
    const activeElement = document.activeElement;
    
    // Marcar que estamos procesando una pregunta
    isProcessingQuestion = true;
    updateButtonStates(true);
    
    // Guardar la pregunta del usuario en el historial para SalesIQ
    addUserQuestionToHistory(pregunta);

    // Asignar ID único al mensaje del usuario y recordarlo
    lastUserMsgId = `user-${Date.now()}`;

    // Mostrar primero la PREGUNTA del usuario
    const questionHTML = `
        <div class="chat-message user-message" id="${lastUserMsgId}"><span class="user-icon" aria-hidden="true" title="Usuario">&#x1F464;</span> 
            ${escapeHtml(pregunta)}
            <div class="msg-time" style="font-size:11px; opacity:.7; margin-top:2px;">${getCurrentTime()}</div>
        </div>`;
    chatHistoryDiv.innerHTML += questionHTML;
    scrollToElementById(lastUserMsgId);
    setTimeout(() => scrollToElementById(lastUserMsgId), 0);

    // Luego el placeholder de PROCESANDO
    chatHistoryDiv.innerHTML += `<p class="processing-message"><em>Procesando pregunta...</em></p>`;
    // Limpiar el input inmediatamente
    preguntaInput.value = '';

    let sessionId = localStorage.getItem('chatSessionId');
    if (!sessionId) {
        sessionId = generateSessionId();
        localStorage.setItem('chatSessionId', sessionId);
    }
    
    // Iniciar contador de tiempo de procesamiento
    let elapsedSeconds = 0;
    processingTimeout = setInterval(() => {
        elapsedSeconds++;
        updateProcessingStatus(chatHistoryDiv, elapsedSeconds);
    }, 3000);

    try {
        const baseURL = getBaseURL();
        const response = await fetch(forceHTTPS(`${baseURL}/chat`), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Session-ID': sessionId
            },
            body: JSON.stringify({ question: pregunta })
        });

        // Limpiar timeout de procesamiento
        if (processingTimeout) {
            clearInterval(processingTimeout);
            processingTimeout = null;
        }

        // Remover mensaje de procesamiento ante cualquier resultado
        const processingElement = chatHistoryDiv.querySelector('.processing-message');
        if (processingElement) processingElement.remove();

        if (!response.ok) {
            const errorText = await response.text();
            chatHistoryDiv.innerHTML += `<p style='color: red;'>Error del servidor (${response.status}): ${escapeHtml(errorText)}</p>`;
            
            // Marcar que terminamos de procesar
            isProcessingQuestion = false;
            updateButtonStates(false);
            
            // IMPORTANTE: Devolver el foco al campo de entrada
            setTimeout(() => {
                preguntaInput.focus();
            }, 100);
            
            return;
        }

        const data = await response.json();
        const responseTime = getCurrentTime();

        // Solo imprimimos el último bloque del asistente
        let lastAssistant = extractLastAssistantBlock(data.full_conversation || "");
        lastAssistant = stripReformulatedHints(lastAssistant, pregunta, data);

        if (!lastAssistant) {
            const flat = data.answer || "";
            if (flat) {
                lastAssistant = `<div class="chat-message assistant-message">${escapeHtml(flat).replace(/\n/g, "<br>")}</div>`;
            }
        }

        if (!lastAssistant) {
            lastAssistant = `<div class="chat-message assistant-message">No se obtuvo respuesta del asistente.</div>`;
        }

        
        // Normalizar párrafos si vino sin etiquetas
        // Quitar únicamente el paréntesis '(según la documentación)' si aparece al inicio del texto
        lastAssistant = lastAssistant.replace(/\s*\(seg[uú]n la documentaci[oó]n(?: disponible)?\)\s*:?\s*/i, '');

        lastAssistant = normalizeAssistantParagraphs(lastAssistant);

        // Ícono pegado al primer párrafo (con fallback si no hay <p>)
        let inserted = lastAssistant.replace(
            /(<p[^>]*>)(\s*)/i,
            `$1<span class="assistant-icon" aria-hidden="true" title="IA">&#x2728;</span> `
        );
        if (inserted === lastAssistant) {
            // Fallback: insertar apenas abre el bloque del asistente
            inserted = lastAssistant.replace(
                /(<div[^>]*class=['"][^'"]*assistant-message[^'"]*['"][^>]*>)/i,
                `$1<span class="assistant-icon" aria-hidden="true" title="IA">&#x2728;</span> `
            );
        }
        lastAssistant = inserted;

        // Insertar timestamp dentro del bloque del asistente
        lastAssistant = lastAssistant.replace(
            /(<div[^>]*class=['"][^'"]*assistant-message[^'"]*['"][^>]*>)([\s\S]*?)(<\/div>)/i,
            `$1$2<span style="display:block;font-size:11px;color:#666;margin-top:4px;">${responseTime}</span>$3`
        );

        chatHistoryDiv.innerHTML += lastAssistant;
        // Reposicionar SIEMPRE en la última pregunta del usuario
        scrollToElementById(lastUserMsgId);

        // Si hay escalación, mostrar bloque y volver a la pregunta
        if (data.escalate_to_human) {
            showHumanEscalation({
                escalation_reason: data.escalation_reason,
                user_question: data.user_question || pregunta,
                session_context: data.session_context || 'Sin contexto disponible'
            });
            // Asegurar posicionamiento en la pregunta
            scrollToElementById(lastUserMsgId);
            
            // Configurar todos los botones de escalación
            setupEscalationButtons();
        }

    } catch (error) {
        if (processingTimeout) {
            clearInterval(processingTimeout);
            processingTimeout = null;
        }
        chatHistoryDiv.innerHTML += "<p style='color: red;'>Error de conexión. Verifica que el servidor esté funcionando.</p>";
        // Mantener el foco en la última pregunta incluso en error
        scrollToElementById(lastUserMsgId);
    } finally {
        // Marcar que terminamos de procesar, independientemente del resultado
        isProcessingQuestion = false;
        updateButtonStates(false);
        
        // IMPORTANTE: Devolver el foco al campo de entrada
        setTimeout(() => {
            preguntaInput.focus();
        }, 100);
    }
}

async function iniciarNuevaConversacion() {
    if (!isConfigLoaded) await loadConfig();

    const chatHistoryDiv = document.getElementById("chat-history");
    const preguntaInput = document.getElementById("question");

    if (preguntaInput) preguntaInput.value = '';
    if (chatHistoryDiv) chatHistoryDiv.innerHTML = "Iniciando nueva conversación...";
    
    // ?? NUEVA LÍNEA: Limpiar el historial de preguntas del usuario
    localStorage.removeItem(USER_HISTORY_KEY);

    let sessionId = localStorage.getItem('chatSessionId');
    if (!sessionId) {
        const newSessionId = generateSessionId();
        localStorage.setItem('chatSessionId', newSessionId);
        if (chatHistoryDiv) chatHistoryDiv.innerHTML = "Nueva conversación iniciada. ¿En qué puedo ayudarte?";
        return;
    }

    try {
        const baseURL = getBaseURL();
        const response = await fetch(forceHTTPS(`${baseURL}/clear_chat_history`), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Session-ID': sessionId
            },
            body: JSON.stringify({})
        });

        if (!response.ok) {
            const errorData = await response.json();
            if (chatHistoryDiv) chatHistoryDiv.innerHTML = `Error al iniciar nueva conversación: ${escapeHtml(errorData.error || 'Error del servidor')}`;
            return;
        }

        const data = await response.json();
        if (data.status === "success") {
            if (chatHistoryDiv) chatHistoryDiv.innerHTML = "Nueva conversación iniciada. ¿En qué puedo ayudarte?";
            const newSessionId = generateSessionId();
            localStorage.setItem('chatSessionId', newSessionId);
        } else {
            if (chatHistoryDiv) chatHistoryDiv.innerHTML = `Error: ${escapeHtml(data.message || 'No se pudo iniciar una nueva conversación.')}`;
        }

    } catch (_) {
        if (chatHistoryDiv) chatHistoryDiv.innerHTML = "Error al iniciar nueva conversación. Por favor, inténtalo de nuevo.";
    }
}

// Inyectar CSS básico
function injectCSS() {
    // ? NUEVO: Evitar duplicar CSS si ya existe
    if (document.getElementById('chatbot-widget-styles')) {
        return;
    }
    
    const css = `

        /* Icono del usuario (??) */
        .user-message .user-icon {
            display: inline-block;
            font-size: 16px;
            line-height: 1;
            margin-right: 6px;
            vertical-align: text-top;
            user-select: none;
        }

        /* Icono del asistente (?) */
        .assistant-message p { margin: 0 0 10px; }

        .assistant-message .assistant-icon {
            display: inline-block;
            font-size: 16px;
            line-height: 1;
            margin-right: 6px;
            vertical-align: text-top;
            user-select: none;
        }
    

        #chatbot-button {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #6574CD;
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
            width: 380px;
            max-width: 90vw;
            height: 550px;
            max-height: 70vh;
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
            background: #e9ecef;
            color: #212529;
            border-radius: 10px 10px 0 0;
            font-size: 14px;
        }
        
        #new-chat-button {
            margin: 10px;
            padding: 8px 12px;
            background: #6574cd;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            font-size: 14px;
        }
        
        #chat-history {
            scroll-behavior: smooth;
            flex: 1;
            padding: 4px;
            overflow-y: auto;
            border-bottom: 1px solid #eee;
            margin-left: 6px;
        }
        
        #input-container {
            display: flex;
            padding: 10px;
        }
        
        #question {
            flex: 1;
            padding: 4px;
            border: 1px solid #6574CD;
            border-radius: 5px;
            margin-right: 5px;
        }
        
        #send-button {
            padding: 8px 12px;
            background: #6574cd;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            font-size: 14px;
        }
        
        /* ⭐ NUEVO: Estilo para botón deshabilitado */
        #send-button:disabled {
            background: #a9b1d9;
            cursor: not-allowed;
        }
        
        .chat-message {
            margin: 4px 0 4px 0px;
            padding: 4px;
            border-radius: 5px;
        }
        
        .user-message {
            background: #dee2e6;
            text-align: right;
            color: black;
            font-weight: bold;
            margin-bottom: 2px;
        }
        
        .assistant-message {
            background: #faf8f8ff;
            margin-top: 2px;
            margin-left: -5px;
        }
        
        .system-message {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
        }
        
        .message-label {
            font-weight: bold;
        }
        
        .processing-message {
            color: #6574cd;
            font-style: italic;
            margin: 10px 0;
        }
        
        /* ⭐ NUEVO: Estilo para botón de escalación más claro */
        .escalation-btn {
            position: relative;
            z-index: 50;
        }
        
        .salesiq-button:hover:not(:disabled) {
            background: #5227cc !important;
        }
        
        @media (max-width: 480px) {
            #chatbot-panel {
                width: 100vw;
                height: 100vh;
                bottom: 0;
                right: 0;
                border-radius: 0;
                max-width: 100vw;
                max-height: 100vh;
            }
            
            #chatbot-button {
                bottom: 15px;
                right: 15px;
                width: 55px;
                height: 55px;
                font-size: 22px;
            }
        }
    `;
    
    const style = document.createElement('style');
    style.id = 'chatbot-widget-styles';
    style.textContent = css;
    document.head.appendChild(style);
}

// Crear el widget
async function createWidget() {
    // ? NUEVO: Evitar duplicar si ya existe
    if (document.getElementById('chatbot-button')) {
        console.log('Widget ya existe, no se creará de nuevo');
        return;
    }
    
    injectCSS();
    
    const chatbotButton = document.createElement("button");
    chatbotButton.id = "chatbot-button";
    // ?? Burbuja de chat visible (emoji)
    chatbotButton.innerHTML = "\u{1F4AC}";
    chatbotButton.title = "Abrir ChatBot";
    
    const chatbotPanel = document.createElement("div");
    chatbotPanel.id = "chatbot-panel";
    
    // ? NUEVO: Determinar ruta del logo según el ambiente
    const logoSrc = isExternalEnvironment ? 
        "https://intranetqa.bas.com.ar/chatbotia/assets/images/Favicon-EasySoft.svg" : 
        "/assets/images/Favicon-EasySoft.svg";
    
    chatbotPanel.innerHTML = `
        <h4 style="font-weight: normal;">
            <img src="${logoSrc}" alt="BAS" width="40" height="40" style="vertical-align:middle; margin-right:6px;" onerror="this.style.display='none'">
            <strong>Soy tu asistente</strong>, <span style="font-weight: normal;">impulsado por IA</span>
        </h4>
        <button id="new-chat-button">Empezar nueva Conversación</button>
        <div id="chat-history">Hola ¿En qué puedo ayudarte?</div>
        <div id="input-container">
            <input type="text" id="question" placeholder="Escribí tu pregunta...">
            <button id="send-button">Enviar</button>
        </div>
    `;

    document.body.appendChild(chatbotButton);
    document.body.appendChild(chatbotPanel);

    chatbotButton.addEventListener('click', toggleChatbot);
    
    const sendBtn = document.getElementById("send-button");
    const input = document.getElementById("question");
    const newChatBtn = document.getElementById("new-chat-button");

    if (sendBtn) {
        sendBtn.addEventListener("click", (e) => {
            e.preventDefault();
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
                enviarPregunta();
            }
        });
    }
}

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', async () => {
        await loadConfig();
        await createWidget();
    });
} else {
    (async () => {
        await loadConfig();
        await createWidget();
    })();
}

// ⭐ NUEVO: Configurar cualquier botón de escalación preexistente
document.addEventListener('DOMContentLoaded', function() {
    // Esperar un momento para asegurar que todo el DOM está cargado
    setTimeout(setupEscalationButtons, 1000);
});

// Exponer funciones globalmente para compatibilidad
window.toggleChatbot = toggleChatbot;
window.enviarPregunta = enviarPregunta;
window.iniciarNuevaConversacion = iniciarNuevaConversacion;

// ? NUEVO: Compatibilidad con widget externo
if (isExternalEnvironment) {
    window.ExternalChatbot = {
        toggle: toggleChatbot,
        sendMessage: enviarPregunta,
        clearHistory: iniciarNuevaConversacion
    };
}