# services/chatbot_service.py
import logging
import string
import time
from typing import Dict, Any
from services.openai_service import OpenAIService
from services.weaviate_service import WeaviateService
from utils.embeddings import EmbeddingUtils
from config import Config

# Guardar preguntas no respondidas
def guardar_pregunta_no_respondida(pregunta: str, archivo: str = "preguntas_no_respondidas.txt"):
    try:
        with open(archivo, "a", encoding="utf-8") as f:
            f.write(pregunta.strip() + "\n")
    except Exception as e:
        logging.error(f"No se pudo guardar la pregunta no respondida: {e}")


class ChatbotService:
    def __init__(self, weaviate_service: WeaviateService):
        self.weaviate_service = weaviate_service
        self.openai_service = OpenAIService()
        self.embedding_utils = EmbeddingUtils(self.openai_service)
        self.chat_histories = {}

        self.predefined_responses = {
            "hola": "¡Hola! ¿En qué puedo ayudarte hoy?",
            "adios": "¡Hasta pronto! Si necesitas algo más de EasySoft, no dudes en preguntar.",
            "gracias": "De nada. Estoy aquí para ayudarte con lo que necesites.",
            "buenos dias": "¡Buenos días! ¿En qué puedo ayudarte?",
            "buenas tardes": "¡Buenas tardes! ¿En qué puedo ayudarte?",
            "buenas noches": "¡Buenas noches! ¿En qué puedo ayudarte?"
        }

    def process_question(self, user_question: str, session_id: str) -> Dict[str, Any]:
        try:
            if session_id not in self.chat_histories:
                self.chat_histories[session_id] = []

            logging.info(f"Pregunta recibida: {user_question}")

            cleaned_question = user_question.lower().strip().translate(str.maketrans('', '', string.punctuation))

            # 1️⃣ Respuesta predefinida
            if cleaned_question in self.predefined_responses:
                return self._handle_predefined_response(user_question, cleaned_question, session_id)

            # 2️⃣ Reformulación de pregunta
            processed_question = self._reformular_pregunta(user_question, session_id)

            # 3️⃣ Obtener embeddings
            question_vector = self.embedding_utils.get_embeddings(processed_question)
            if question_vector is None:
                return self._create_error_response("Error al procesar la pregunta", user_question, session_id)

            # 4️⃣ Buscar en Weaviate (híbrido)
            context_results = self.weaviate_service.search_similar_documents(
                question_vector,
                query_text=processed_question,
                max_results=5
            )

            # 5️⃣ Validación estricta: no contexto = no respuesta
            context = context_results.get("context", "")
            if (not context) or (context_results.get("results_count", 0) == 0) or len(context) < 50:
                return self._create_no_info_response(user_question, session_id)

            # 6️⃣ Verificar similitud para evitar respuestas sin respaldo
            context_vector = self.embedding_utils.get_embeddings(context)
            similarity = self.embedding_utils.cosine_similarity(question_vector, context_vector)
            logging.info(f"Similitud entre pregunta y contexto: {similarity:.3f}")

            if similarity < Config.SIMILARITY_THRESHOLD:
                return self._create_no_info_response(user_question, session_id)

            # 7️⃣ Construir mensajes para OpenAI
            history = self.chat_histories[session_id][-Config.MAX_HISTORY_MESSAGES * 2:]
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Respondé únicamente en base a los documentos de EasySoft. "
                        "Si no encontrás información en ellos, indicá que no tenés la información. "
                        f"Contexto relevante extraído de los documentos:\n{context}"
                    )
                }
            ] + history + [{"role": "user", "content": user_question}]

            chatbot_response = self.openai_service.generate_response(messages)
            if not chatbot_response:
                return self._create_error_response("Error al generar respuesta", user_question, session_id)

            # 8️⃣ Actualizar historial
            self.chat_histories[session_id].append({"role": "user", "content": user_question})
            self.chat_histories[session_id].append({"role": "assistant", "content": chatbot_response})

            if len(self.chat_histories[session_id]) > Config.MAX_HISTORY_MESSAGES * 2:
                self.chat_histories[session_id] = self.chat_histories[session_id][-Config.MAX_HISTORY_MESSAGES * 2:]

            return self._create_success_response(user_question, chatbot_response)

        except Exception as e:
            logging.error(f"Error en process_question: {e}")
            return self._create_error_response(f"Error del servidor: {str(e)}", user_question, session_id)

    # Reformulación de preguntas ambiguas
    def _reformular_pregunta(self, user_question: str, session_id: str) -> str:
        processed_question = user_question
        if "easysoft" not in user_question.lower():
            processed_question += " en EasySoft"

        palabras_clave = ["detalle", "detalles", "cada uno", "eso", "ellos", "ellas", "más info"]
        if any(pk in user_question.lower() for pk in palabras_clave) and session_id in self.chat_histories:
            prev_user_msgs = [msg["content"] for msg in self.chat_histories[session_id] if msg["role"] == "user"]
            if prev_user_msgs:
                ultima_pregunta = prev_user_msgs[-1]
                processed_question = f"{user_question} (Relacionado con: {ultima_pregunta}) en EasySoft"

        return processed_question

    def _handle_predefined_response(self, user_question: str, cleaned_question: str, session_id: str) -> Dict[str, Any]:
        chatbot_response = self.predefined_responses[cleaned_question]
        self.chat_histories[session_id].append({"role": "user", "content": user_question})
        self.chat_histories[session_id].append({"role": "assistant", "content": chatbot_response})
        return self._create_success_response(user_question, chatbot_response)

    def _create_success_response(self, user_question: str, chatbot_response: str) -> Dict[str, Any]:
        full_display = f"<div class='chat-message user-message'><span class='message-label'>Pregunta:</span> {user_question}</div>\n"
        full_display += f"<div class='chat-message assistant-message'><span class='message-label'>Respuesta:</span> {chatbot_response}</div>\n"
        return {'response': chatbot_response, 'full_conversation': full_display}

    def _create_no_info_response(self, user_question: str, session_id: str) -> Dict[str, Any]:
        chatbot_response = "No tengo la información para responder a esa pregunta basándome en la información disponible."
        self.chat_histories[session_id].append({"role": "user", "content": user_question})
        self.chat_histories[session_id].append({"role": "assistant", "content": chatbot_response})
        guardar_pregunta_no_respondida(user_question)
        return self._create_success_response(user_question, chatbot_response)

    def _create_error_response(self, error_message: str, user_question: str, session_id: str) -> Dict[str, Any]:
        return {
            'error': error_message,
            'full_conversation': f"<div class='chat-message user-message'><span class='message-label'>Pregunta:</span> {user_question}</div>\n" +
                               f"<div class='chat-message assistant-message error'><span class='message-label'>Error:</span> {error_message}</div>\n"
        }

    def clear_chat_history(self, session_id: str) -> bool:
        try:
            if session_id in self.chat_histories:
                del self.chat_histories[session_id]
            return True
        except Exception as e:
            logging.error(f"Error al limpiar historial de {session_id}: {e}")
            return False

    def get_health_status(self) -> Dict[str, Any]:
        health_status = {
            "status": "ok",
            "timestamp": time.time(),
            "services": {}
        }
        health_status["services"]["weaviate"] = self.weaviate_service.get_health_status()
        health_status["services"]["openai"] = self.openai_service.get_health_status()

        all_services_ok = all(service == "connected" for service in health_status["services"].values())
        if not all_services_ok:
            health_status["status"] = "degraded"
        return health_status

    def cleanup(self):
        try:
            self.weaviate_service.close()
            logging.info("Servicios de chatbot cerrados correctamente.")
        except Exception as e:
            logging.error(f"Error al cerrar servicios: {e}")
