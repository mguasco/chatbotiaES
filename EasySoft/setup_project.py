#!/usr/bin/env python3
"""
Script para generar la estructura completa del proyecto chatbot refactorizado
Ejecuta este script en el directorio donde quieres crear el proyecto
"""

import os
import sys

def create_directory_structure():
    """Crea la estructura de directorios"""
    directories = [
        'services',
        'utils', 
        'models',
        'static',
        'templates',
        'assets/images',
        'assets/css',
        'template',
        'whxdata'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Directorio creado: {directory}")

def create_file(filepath, content):
    """Crea un archivo con el contenido especificado"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Archivo creado: {filepath}")
    except Exception as e:
        print(f"✗ Error creando {filepath}: {e}")

def main():
    print("🚀 Generando estructura del proyecto chatbot refactorizado...")
    print("=" * 60)
    
    # Crear estructura de directorios
    create_directory_structure()
    
    # 1. app.py - Simplificado
    app_py_content = '''# app.py - Simplificado, solo Flask y rutas
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import logging
import threading
from config import Config
from services.chatbot_service import ChatbotService
from services.weaviate_service import WeaviateService

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configurar Flask
BASE_DIR = os.path.abspath(os.getcwd())
app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

# Inicializar servicios
weaviate_service = WeaviateService()
chatbot_service = ChatbotService(weaviate_service)
chat_history_lock = threading.Lock()

@app.route('/config.js')
def serve_config():
    """Genera un archivo de configuración JavaScript dinámico"""
    config_js = f"""
window.CHATBOT_CONFIG = {{
    SERVER_URL: '{Config.BASE_URL}',
    API_VERSION: 'v1'
}};
"""
    return config_js, 200, {'Content-Type': 'application/javascript'}

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.htm')

# Rutas para archivos estáticos
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    assets_path = os.path.join(BASE_DIR, 'assets')
    file_path = os.path.join(assets_path, filename)
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        directory = os.path.dirname(file_path)
        filename_only = os.path.basename(file_path)
        return send_from_directory(directory, filename_only)
    else:
        return f"Archivo no encontrado: assets/{filename}", 404

@app.route('/template/<path:filename>')
def serve_template(filename):
    template_path = os.path.join(BASE_DIR, 'template')
    file_path = os.path.join(template_path, filename)
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        directory = os.path.dirname(file_path)
        filename_only = os.path.basename(file_path)
        return send_from_directory(directory, filename_only)
    else:
        return f"Archivo no encontrado: template/{filename}", 404

@app.route('/whxdata/<path:filename>')
def serve_whxdata(filename):
    whxdata_path = os.path.join(BASE_DIR, 'whxdata')
    file_path = os.path.join(whxdata_path, filename)
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        directory = os.path.dirname(file_path)
        filename_only = os.path.basename(file_path)
        return send_from_directory(directory, filename_only)
    else:
        return f"Archivo no encontrado: whxdata/{filename}", 404

@app.route('/<path:filename>')
def serve_static_files(filename):
    try:
        full_path = os.path.join(BASE_DIR, filename)
        allowed_extensions = (
            '.htm', '.html', '.css', '.js', '.svg', '.jpg', '.jpeg', 
            '.png', '.gif', '.ico', '.bmp', '.webp', '.tiff', '.pdf',
            '.json', '.xml', '.txt', '.md'
        )
        
        if os.path.isfile(full_path):
            file_extension = os.path.splitext(filename)[1].lower()
            if file_extension in allowed_extensions:
                directory = os.path.dirname(full_path)
                filename_only = os.path.basename(full_path)
                return send_from_directory(directory, filename_only)
            else:
                return "Tipo de archivo no permitido", 403
        else:
            return "Archivo no encontrado", 404
            
    except Exception as e:
        logging.error(f"Error sirviendo archivo estático {filename}: {e}")
        return "Error interno del servidor", 500

# RUTA PRINCIPAL DEL CHATBOT - Delegada al servicio
@app.route('/chat', methods=['POST'])
def chat():
    try:
        session_id = request.headers.get('X-Session-ID', 'default_session')
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No se enviaron datos JSON'}), 400
            
        user_question = data.get('question')
        if not user_question:
            return jsonify({'error': 'No se proporcionó pregunta'}), 400

        # Delegar al servicio de chatbot
        with chat_history_lock:
            response_data = chatbot_service.process_question(user_question, session_id)
        
        return jsonify(response_data)

    except Exception as e:
        logging.error(f"Error general en /chat: {e}")
        return jsonify({'error': f'Error del servidor: {str(e)}'}), 500

@app.route('/clear_chat_history', methods=['POST'])
def clear_chat_history():
    session_id = request.headers.get('X-Session-ID', 'default_session')
    
    success = chatbot_service.clear_chat_history(session_id)
    
    if success:
        return jsonify({"status": "success", "message": "Historial limpiado."})
    else:
        return jsonify({"status": "error", "message": "Error al limpiar historial."}), 500

@app.route('/health', methods=['GET'])
def health_check():
    health_status = chatbot_service.get_health_status()
    status_code = 200 if health_status.get("status") == "ok" else 503
    return jsonify(health_status), status_code

@app.route('/debug/files', methods=['GET'])
def debug_files():
    try:
        files_info = {}
        important_dirs = ['assets', 'template', 'whxdata']
        
        for dir_name in important_dirs:
            dir_path = os.path.join(BASE_DIR, dir_name)
            if os.path.exists(dir_path):
                files_info[dir_name] = []
                for root, dirs, files in os.walk(dir_path):
                    rel_path = os.path.relpath(root, dir_path)
                    if rel_path == '.':
                        rel_path = dir_name
                    files_info[f"{dir_name}/{rel_path}"] = files
            else:
                files_info[dir_name] = "DIRECTORIO NO ENCONTRADO"
        
        root_files = [f for f in os.listdir(BASE_DIR) if os.path.isfile(os.path.join(BASE_DIR, f))]
        files_info['root'] = root_files
        
        return jsonify(files_info)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    try:
        app.run(debug=Config.FLASK_DEBUG, host=Config.FLASK_HOST, port=Config.FLASK_PORT)
    finally:
        # Cerrar conexiones
        chatbot_service.cleanup()
'''

    # 2. config.py - Actualizado para Azure
    config_py_content = '''# config.py - Configuración para Azure
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Weaviate - Modificado para Azure
    WEAVIATE_HOST = os.getenv('WEAVIATE_HOST', 'localhost')
    WEAVIATE_HTTP_PORT = int(os.getenv('WEAVIATE_HTTP_PORT', 8080))
    WEAVIATE_GRPC_PORT = int(os.getenv('WEAVIATE_GRPC_PORT', 50051))
    WEAVIATE_HTTP_SECURE = os.getenv('WEAVIATE_HTTP_SECURE', 'False').lower() == 'true'
    WEAVIATE_GRPC_SECURE = os.getenv('WEAVIATE_GRPC_SECURE', 'False').lower() == 'true'
    WEAVIATE_DISTANCE_THRESHOLD = float(os.getenv('WEAVIATE_DISTANCE_THRESHOLD', 0.35))
    
    # Flask - Modificado para Azure
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))  # 80 para Azure
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # URLs para Azure
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')
    
    # Aplicación
    MAX_HISTORY_MESSAGES = int(os.getenv('MAX_HISTORY_MESSAGES', 6))
    SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', 0.80))
    
    # Nuevas configuraciones para Azure
    AZURE_STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    AZURE_KEY_VAULT_URL = os.getenv('AZURE_KEY_VAULT_URL')
'''

    # 3. services/__init__.py
    services_init_content = '''# services/__init__.py
from .chatbot_service import ChatbotService
from .weaviate_service import WeaviateService
from .openai_service import OpenAIService

__all__ = ['ChatbotService', 'WeaviateService', 'OpenAIService']
'''

    # 4. services/chatbot_service.py
    chatbot_service_content = '''# services/chatbot_service.py
import logging
import string
import time
from typing import Dict, Any, Optional
from services.openai_service import OpenAIService
from services.weaviate_service import WeaviateService
from utils.embeddings import EmbeddingUtils
from config import Config

class ChatbotService:
    def __init__(self, weaviate_service: WeaviateService):
        self.weaviate_service = weaviate_service
        self.openai_service = OpenAIService()
        self.embedding_utils = EmbeddingUtils(self.openai_service)
        self.chat_histories = {}
        
        # Respuestas predefinidas
        self.predefined_responses = {
            "hola": "¡Hola! ¿En qué puedo ayudarte hoy con los documentos de EasySoft?",
            "adios": "¡Hasta pronto! Si necesitas algo más de EasySoft, no dudes en preguntar.",
            "gracias": "De nada. Estoy aquí para ayudarte con lo que necesites.",
            "buenos dias": "¡Buenos días! ¿En qué puedo ayudarte con EasySoft?",
            "buenas tardes": "¡Buenas tardes! ¿En qué puedo ayudarte con EasySoft?",
            "buenas noches": "¡Buenas noches! ¿En qué puedo ayudarte con EasySoft?"
        }

    def process_question(self, user_question: str, session_id: str) -> Dict[str, Any]:
        """Procesa una pregunta del usuario y devuelve la respuesta"""
        try:
            # Inicializar historial de sesión si no existe
            if session_id not in self.chat_histories:
                self.chat_histories[session_id] = []

            logging.info(f"Pregunta recibida: {user_question}")

            # Limpiar y procesar la pregunta
            cleaned_question = user_question.lower().strip().translate(str.maketrans('', '', string.punctuation))
            predefined_keys = ["hola", "adios", "gracias", "buenos dias", "buenas tardes", "buenas noches"]
            
            # Verificar respuestas predefinidas
            if cleaned_question in predefined_keys:
                return self._handle_predefined_response(user_question, cleaned_question, session_id)

            # Procesar pregunta con contexto EasySoft
            if cleaned_question not in predefined_keys and "easysoft" not in cleaned_question:
                processed_question = user_question + " en EasySoft"
            else:
                processed_question = user_question

            # Obtener embeddings de la pregunta
            question_vector = self.embedding_utils.get_embeddings(processed_question)
            if question_vector is None:
                return self._create_error_response("Error al procesar la pregunta", user_question, session_id)

            # Buscar en Weaviate
            context_results = self.weaviate_service.search_similar_documents(question_vector)
            
            if not context_results["success"]:
                return self._create_no_info_response(user_question, session_id)

            # Verificar similitud del contexto
            if context_results["context"]:
                context_vector = self.embedding_utils.get_embeddings(context_results["context"])
                similarity = self.embedding_utils.cosine_similarity(question_vector, context_vector)
                logging.info(f"Similitud entre pregunta y contexto: {similarity:.3f}")

                if similarity < Config.SIMILARITY_THRESHOLD:
                    return self._create_no_info_response(user_question, session_id)
            else:
                return self._create_no_info_response(user_question, session_id)

            # Generar respuesta con OpenAI
            chatbot_response = self.openai_service.generate_response(
                user_question, 
                context_results["context"]
            )

            if not chatbot_response:
                return self._create_error_response("Error al generar respuesta", user_question, session_id)

            # Guardar en historial
            self.chat_histories[session_id].append({"role": "user", "content": user_question})
            self.chat_histories[session_id].append({"role": "assistant", "content": chatbot_response})

            # Limitar historial
            if len(self.chat_histories[session_id]) > Config.MAX_HISTORY_MESSAGES * 2:
                self.chat_histories[session_id] = self.chat_histories[session_id][-Config.MAX_HISTORY_MESSAGES * 2:]

            return self._create_success_response(user_question, chatbot_response)

        except Exception as e:
            logging.error(f"Error en process_question: {e}")
            return self._create_error_response(f"Error del servidor: {str(e)}", user_question, session_id)

    def _handle_predefined_response(self, user_question: str, cleaned_question: str, session_id: str) -> Dict[str, Any]:
        """Maneja respuestas predefinidas"""
        chatbot_response = self.predefined_responses[cleaned_question]
        
        self.chat_histories[session_id].append({"role": "user", "content": user_question})
        self.chat_histories[session_id].append({"role": "assistant", "content": chatbot_response})
        
        return self._create_success_response(user_question, chatbot_response)

    def _create_success_response(self, user_question: str, chatbot_response: str) -> Dict[str, Any]:
        """Crea una respuesta exitosa formateada"""
        full_display = f"<div class='chat-message user-message'><span class='message-label'>Pregunta:</span> {user_question}</div>\\n"
        full_display += f"<div class='chat-message assistant-message'><span class='message-label'>Respuesta:</span> {chatbot_response}</div>\\n"
        
        return {
            'response': chatbot_response,
            'full_conversation': full_display
        }

    def _create_no_info_response(self, user_question: str, session_id: str) -> Dict[str, Any]:
        """Crea respuesta cuando no hay información disponible"""
        chatbot_response = "No tengo la información para responder a esa pregunta basándome en los documentos de EasySoft disponibles."
        
        self.chat_histories[session_id].append({"role": "user", "content": user_question})
        self.chat_histories[session_id].append({"role": "assistant", "content": chatbot_response})
        
        return self._create_success_response(user_question, chatbot_response)

    def _create_error_response(self, error_message: str, user_question: str, session_id: str) -> Dict[str, Any]:
        """Crea respuesta de error"""
        return {
            'error': error_message,
            'full_conversation': f"<div class='chat-message user-message'><span class='message-label'>Pregunta:</span> {user_question}</div>\\n" +
                               f"<div class='chat-message assistant-message error'><span class='message-label'>Error:</span> {error_message}</div>\\n"
        }

    def clear_chat_history(self, session_id: str) -> bool:
        """Limpia el historial de chat de una sesión"""
        try:
            if session_id in self.chat_histories:
                del self.chat_histories[session_id]
            return True
        except Exception as e:
            logging.error(f"Error al limpiar historial de {session_id}: {e}")
            return False

    def get_health_status(self) -> Dict[str, Any]:
        """Devuelve el estado de salud de todos los servicios"""
        health_status = {
            "status": "ok",
            "timestamp": time.time(),
            "services": {}
        }
        
        # Check Weaviate
        health_status["services"]["weaviate"] = self.weaviate_service.get_health_status()
        
        # Check OpenAI
        health_status["services"]["openai"] = self.openai_service.get_health_status()
        
        # Determinar estado general
        all_services_ok = all(
            service == "connected" 
            for service in health_status["services"].values()
        )
        
        if not all_services_ok:
            health_status["status"] = "degraded"
        
        return health_status

    def cleanup(self):
        """Limpia recursos al cerrar la aplicación"""
        try:
            self.weaviate_service.close()
            logging.info("Servicios de chatbot cerrados correctamente.")
        except Exception as e:
            logging.error(f"Error al cerrar servicios: {e}")
'''

    # 5. services/weaviate_service.py
    weaviate_service_content = '''# services/weaviate_service.py
import logging
import time
import weaviate
import weaviate.classes as wvc
from typing import Dict, Any, Optional, List
from config import Config

class WeaviateService:
    def __init__(self):
        self.client = None
        self._connect()

    def _connect(self):
        """Conecta a Weaviate con reintentos"""
        max_retries = 5
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                if Config.WEAVIATE_HTTP_SECURE:
                    self.client = weaviate.connect_to_custom(
                        http_host=Config.WEAVIATE_HOST,
                        http_port=Config.WEAVIATE_HTTP_PORT,
                        http_secure=Config.WEAVIATE_HTTP_SECURE,
                        grpc_host=Config.WEAVIATE_HOST,
                        grpc_port=Config.WEAVIATE_GRPC_PORT,
                        grpc_secure=Config.WEAVIATE_GRPC_SECURE
                    )
                else:
                    self.client = weaviate.connect_to_local(
                        host=Config.WEAVIATE_HOST,
                        port=Config.WEAVIATE_HTTP_PORT,
                        grpc_port=Config.WEAVIATE_GRPC_PORT
                    )
                
                if self.client.is_ready():
                    logging.info(f"Conectado a Weaviate en {Config.WEAVIATE_HOST}:{Config.WEAVIATE_HTTP_PORT}")
                    return
                
            except Exception as e:
                logging.warning(f"Intento {attempt + 1} de conexión a Weaviate falló: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                
        logging.error("No se pudo conectar a Weaviate después de varios intentos")
        self.client = None

    def search_similar_documents(self, question_vector: List[float]) -> Dict[str, Any]:
        """Busca documentos similares en Weaviate"""
        try:
            if not self.client or not self.client.is_ready():
                return {"success": False, "context": None, "error": "Weaviate no disponible"}

            collection = self.client.collections.get("Documento")
            response = collection.query.near_vector(
                near_vector=question_vector,
                limit=5,
                return_metadata=wvc.query.MetadataQuery(distance=True)
            )

            filtered_results = []
            for obj in response.objects:
                content = obj.properties.get("contenido", '').strip()
                if (obj.metadata.distance is not None and 
                    obj.metadata.distance < Config.WEAVIATE_DISTANCE_THRESHOLD and 
                    len(content) > 100):
                    filtered_results.append(content)

            context = "\\n".join(filtered_results) if filtered_results else None
            
            return {
                "success": True,
                "context": context,
                "results_count": len(filtered_results)
            }

        except Exception as e:
            logging.error(f"Error al consultar Weaviate: {e}")
            return {"success": False, "context": None, "error": str(e)}

    def get_health_status(self) -> str:
        """Devuelve el estado de salud de Weaviate"""
        try:
            if self.client and self.client.is_ready():
                return "connected"
            else:
                return "disconnected"
        except:
            return "error"

    def close(self):
        """Cierra la conexión a Weaviate"""
        if self.client:
            try:
                self.client.close()
                logging.info("Conexión a Weaviate cerrada correctamente.")
            except Exception as e:
                logging.error(f"Error al cerrar conexión a Weaviate: {e}")
'''

    # 6. services/openai_service.py
    openai_service_content = '''# services/openai_service.py
import logging
from openai import OpenAI
from typing import Optional
from config import Config

class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.system_prompt = """
        Eres un asistente útil que responde preguntas solo con base en la información de los documentos de EasySoft.
        Si la información no está en el contexto, respondé: 'No tengo la información para responder a esa pregunta basándome en los documentos de EasySoft disponibles.'
        """

    def generate_response(self, user_question: str, context: str) -> Optional[str]:
        """Genera una respuesta usando OpenAI"""
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Información de contexto:\\n{context}\\n\\nPregunta del usuario: {user_question}"}
            ]

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()

        except Exception as e:
            logging.error(f"Error al llamar a OpenAI: {e}")
            return None

    def get_health_status(self) -> str:
        """Verifica el estado de OpenAI"""
        try:
            # Test simple con el modelo
            self.client.models.list()
            return "connected"
        except Exception as e:
            logging.error(f"Error en health check de OpenAI: {e}")
            return "error"
'''

    # 7. utils/__init__.py
    utils_init_content = '''# utils/__init__.py
from .embeddings import EmbeddingUtils

__all__ = ['EmbeddingUtils']
'''

    # 8. utils/embeddings.py
    embeddings_content = '''# utils/embeddings.py
import logging
import numpy as np
from typing import Optional, List
from services.openai_service import OpenAIService

class EmbeddingUtils:
    def __init__(self, openai_service: OpenAIService):
        self.openai_service = openai_service

    def get_embeddings(self, text: str) -> Optional[List[float]]:
        """Obtiene embeddings de OpenAI"""
        try:
            response = self.openai_service.client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logging.error(f"Error al obtener embeddings de OpenAI: {e}")
            return None

    @staticmethod
    def cosine_similarity(vec1: Optional[List[float]], vec2: Optional[List[float]]) -> float:
        """Calcula similitud coseno entre dos vectores"""
        if vec1 is None or vec2 is None:
            return 0
        
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        return np.dot(vec1_np, vec2_np) / (np.linalg.norm(vec1_np) * np.linalg.norm(vec2_np))
'''

    # 9. models/__init__.py
    models_init_content = '''# models/__init__.py
from .chat_models import ChatMessage, ChatSession, SearchResult, ChatResponse

__all__ = ['ChatMessage', 'ChatSession', 'SearchResult', 'ChatResponse']
'''

    # 10. models/chat_models.py
    chat_models_content = '''# models/chat_models.py
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class ChatMessage:
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class ChatSession:
    session_id: str
    messages: List[ChatMessage]
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class SearchResult:
    success: bool
    context: Optional[str]
    results_count: int = 0
    error: Optional[str] = None

@dataclass
class ChatResponse:
    response: str
    full_conversation: str
    error: Optional[str] = None
'''

    # 11. .env actualizado
    env_content = '''# Clave API de OpenAI
OPENAI_API_KEY=tu-openai-api-key-aqui

# URL base (cambiar para Azure)
BASE_URL=http://localhost:5000

# Configuración de conexión a Weaviate
WEAVIATE_HOST=localhost
WEAVIATE_HTTP_PORT=8080
WEAVIATE_GRPC_PORT=50051
WEAVIATE_HTTP_SECURE=False
WEAVIATE_GRPC_SECURE=False

# Umbral de distancia para la búsqueda en Weaviate
WEAVIATE_DISTANCE_THRESHOLD=0.35

# Configuración de la aplicación
MAX_HISTORY_MESSAGES=6
SIMILARITY_THRESHOLD=0.80

# Flask
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False

# Azure (para producción)
# AZURE_STORAGE_CONNECTION_STRING=tu-connection-string
# AZURE_KEY_VAULT_URL=https://tu-keyvault.vault.azure.net/
'''

    # 12. requirements.txt actualizado
    requirements_content = '''Flask==2.3.3
Flask-CORS==4.0.0
openai==1.3.5
weaviate-client==4.5.2
python-dotenv==1.0.0
numpy==1.24.3
waitress==2.1.2

# Azure dependencies (opcional)
# azure-keyvault-secrets==4.7.0
# azure-identity==1.15.0
# opencensus-ext-azure==1.1.13
'''

    # 13. Dockerfile actualizado
    dockerfile_content = '''FROM python:3.9-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \\
    gcc \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Crear usuario no-root para seguridad
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Healthcheck para Azure
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:5000/health || exit 1

# Exponer puerto
EXPOSE 5000

# Comando por defecto
CMD ["python", "app.py"]
'''

    # 14. docker-compose.yml para Azure
    docker_compose_content = '''version: '3.8'

services:
  weaviate:
    image: semitechnologies/weaviate:1.30.7
    container_name: weaviate_chatbot
    ports:
      - "8080:8080"
      - "50051:50051"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'none'
      ENABLE_MODULES: ''
      CLUSTER_HOSTNAME: 'node1'
    volumes:
      - weaviate_data:/var/lib/weaviate
    networks:
      - chatbot_network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'

  chatbot:
    build: .
    container_name: flask_chatbot
    ports:
      - "5000:5000"  # 80:80 para Azure
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - WEAVIATE_HOST=weaviate
      - WEAVIATE_HTTP_PORT=8080
      - WEAVIATE_GRPC_PORT=50051
      - WEAVIATE_HTTP_SECURE=False
      - WEAVIATE_GRPC_SECURE=False
      - FLASK_HOST=0.0.0.0
      - FLASK_PORT=5000  # 80 para Azure
      - FLASK_DEBUG=False
      - BASE_URL=${BASE_URL}
    depends_on:
      - weaviate
    networks:
      - chatbot_network
    restart: unless-stopped
    volumes:
      - ./:/app
    working_dir: /app
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'

volumes:
  weaviate_data:

networks:
  chatbot_network:
    driver: bridge
'''

    # 15. Script de despliegue para Azure
    deploy_azure_content = '''#!/bin/bash
# deploy-azure.sh - Script de despliegue para Azure

# Variables
RESOURCE_GROUP="chatbot-rg"
LOCATION="East US"
ACR_NAME="chatbotregistry"
CONTAINER_APP_ENV="chatbot-env"

echo "🚀 Iniciando despliegue en Azure..."

# Crear grupo de recursos
echo "📦 Creando grupo de recursos..."
az group create --name $RESOURCE_GROUP --location "$LOCATION"

# Crear Azure Container Registry
echo "🏗️ Creando Azure Container Registry..."
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic

# Build y push de la imagen
echo "🔨 Construyendo y subiendo imagen..."
az acr build --registry $ACR_NAME --image chatbot:latest .

# Crear Container Apps Environment
echo "🌐 Creando Container Apps Environment..."
az containerapp env create \\
  --name $CONTAINER_APP_ENV \\
  --resource-group $RESOURCE_GROUP \\
  --location "$LOCATION"

# Crear Azure Files para Weaviate
STORAGE_ACCOUNT="chatbotstorage$RANDOM"
echo "💾 Creando almacenamiento..."
az storage account create \\
  --name $STORAGE_ACCOUNT \\
  --resource-group $RESOURCE_GROUP \\
  --location "$LOCATION" \\
  --sku Standard_LRS

# Desplegar Weaviate Container App
echo "🧠 Desplegando Weaviate..."
az containerapp create \\
  --name weaviate-app \\
  --resource-group $RESOURCE_GROUP \\
  --environment $CONTAINER_APP_ENV \\
  --image semitechnologies/weaviate:1.30.7 \\
  --target-port 8080 \\
  --ingress external \\
  --env-vars \\
    AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \\
    PERSISTENCE_DATA_PATH=/var/lib/weaviate

# Desplegar Chatbot Container App
echo "🤖 Desplegando Chatbot..."
az containerapp create \\
  --name chatbot-app \\
  --resource-group $RESOURCE_GROUP \\
  --environment $CONTAINER_APP_ENV \\
  --image $ACR_NAME.azurecr.io/chatbot:latest \\
  --target-port 80 \\
  --ingress external \\
  --registry-server $ACR_NAME.azurecr.io \\
  --env-vars \\
    WEAVIATE_HOST=weaviate-app \\
    FLASK_PORT=80 \\
    FLASK_DEBUG=False

echo "✅ Despliegue completado!"
'''

    # 16. README.md
    readme_content = '''# Chatbot EasySoft - Versión Refactorizada

## Descripción
Chatbot inteligente que responde preguntas basándose en documentos de EasySoft, utilizando OpenAI GPT y Weaviate como base de datos vectorial.

## Estructura del Proyecto

```
/proyecto-chatbot/
├── app.py                     # Flask app principal
├── config.py                  # Configuración centralizada
├── services/                  # Servicios modulares
│   ├── chatbot_service.py     # Lógica principal del chatbot
│   ├── weaviate_service.py    # Gestión de Weaviate
│   └── openai_service.py      # Integración con OpenAI
├── utils/                     # Utilidades
│   └── embeddings.py          # Manejo de embeddings
├── models/                    # Modelos de datos
│   └── chat_models.py         # Estructuras de datos
├── static/                    # Archivos estáticos
├── requirements.txt           # Dependencias
├── dockerfile                 # Imagen Docker
├── docker-compose.yml         # Orquestación local
└── deploy-azure.sh           # Script de despliegue Azure
```

## Instalación Local

1. Clonar o generar el proyecto:
```bash
python setup_project.py
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tus credenciales
```

4. Levantar servicios con Docker:
```bash
docker-compose up -d
```

5. Ejecutar la aplicación:
```bash
python app.py
```

## Despliegue en Azure

### Opción 1: Azure Container Apps (Recomendado)
```bash
# Instalar Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login
az login

# Ejecutar script de despliegue
chmod +x deploy-azure.sh
./deploy-azure.sh
```

### Opción 2: Manual
1. Crear Azure Container Registry
2. Subir imágenes
3. Crear Container Apps
4. Configurar variables de entorno

## Configuración

### Variables de Entorno Importantes

#### Para Desarrollo Local:
- `OPENAI_API_KEY`: Tu API key de OpenAI
- `WEAVIATE_HOST=localhost`
- `FLASK_PORT=5000`
- `FLASK_DEBUG=True`

#### Para Producción Azure:
- `WEAVIATE_HOST=weaviate-app`
- `FLASK_PORT=80`
- `FLASK_DEBUG=False`
- `WEAVIATE_HTTP_SECURE=True`

## API Endpoints

- `GET /` - Página principal
- `POST /chat` - Enviar pregunta al chatbot
- `POST /clear_chat_history` - Limpiar historial
- `GET /health` - Estado de servicios
- `GET /debug/files` - Debug de archivos

## Estructura de Respuesta

```json
{
  "response": "Respuesta del chatbot",
  "full_conversation": "<div>HTML formateado</div>"
}
```

## Monitoreo

### Health Check
```bash
curl http://localhost:5000/health
```

### Logs
```bash
# Docker
docker-compose logs -f chatbot

# Azure
az containerapp logs show --name chatbot-app --resource-group chatbot-rg
```

## Desarrollo

### Agregar Nuevas Funcionalidades

1. **Nuevos servicios**: Crear en `services/`
2. **Utilidades**: Agregar en `utils/`
3. **Modelos**: Definir en `models/`
4. **Rutas**: Agregar en `app.py`

### Testing
```bash
# Instalar dependencias de testing
pip install pytest pytest-flask

# Ejecutar tests
pytest tests/
```

## Troubleshooting

### Problemas Comunes

1. **Weaviate no conecta**:
   - Verificar que el contenedor esté corriendo
   - Revisar puertos y configuración de red

2. **OpenAI API Error**:
   - Verificar API key
   - Revisar cuota y límites

3. **Archivos estáticos no cargan**:
   - Verificar estructura de directorios
   - Revisar permisos de archivos

### Logs Útiles
```bash
# Ver logs de todos los servicios
docker-compose logs

# Solo chatbot
docker-compose logs chatbot

# Solo Weaviate
docker-compose logs weaviate
```

## Seguridad

- ✅ Variables de entorno para secretos
- ✅ Usuario no-root en Docker
- ✅ CORS configurado
- ✅ Health checks
- 🔄 Azure Key Vault (en desarrollo)
- 🔄 SSL/TLS (en desarrollo)

## Performance

### Optimizaciones Implementadas
- Conexión persistente a Weaviate
- Cache de embeddings
- Límite de historial de chat
- Health checks eficientes

### Métricas Recomendadas
- Tiempo de respuesta promedio
- Uso de memoria
- Latencia de Weaviate
- Rate limiting de OpenAI

## Contribución

1. Fork del proyecto
2. Crear rama feature
3. Commit cambios
4. Push a la rama
5. Crear Pull Request

## Licencia

[Especificar licencia]

## Contacto

[Información de contacto]
'''

    # Crear todos los archivos
    files_to_create = [
        ('app.py', app_py_content),
        ('config.py', config_py_content),
        ('services/__init__.py', services_init_content),
        ('services/chatbot_service.py', chatbot_service_content),
        ('services/weaviate_service.py', weaviate_service_content),
        ('services/openai_service.py', openai_service_content),
        ('utils/__init__.py', utils_init_content),
        ('utils/embeddings.py', embeddings_content),
        ('models/__init__.py', models_init_content),
        ('models/chat_models.py', chat_models_content),
        ('.env', env_content),
        ('requirements.txt', requirements_content),
        ('dockerfile', dockerfile_content),
        ('docker-compose.yml', docker_compose_content),
        ('deploy-azure.sh', deploy_azure_content),
        ('README.md', readme_content),
    ]
    
    print(f"\n📝 Creando {len(files_to_create)} archivos...")
    for filepath, content in files_to_create:
        create_file(filepath, content)
    
    # Copiar archivos existentes que deben mantenerse
    existing_files_to_copy = [
        'chatbot-widget.js',
        'index.htm',
        'vectorizatodos.py'
    ]
    
    print(f"\n📋 Archivos existentes que debes copiar manualmente:")
    for filename in existing_files_to_copy:
        print(f"   • {filename}")
    
    print("\n" + "="*60)
    print("🎉 ¡Estructura del proyecto generada exitosamente!")
    print("\n📚 Próximos pasos:")
    print("1. Copiar tus archivos existentes (chatbot-widget.js, index.htm, etc.)")
    print("2. Actualizar tu API key de OpenAI en .env")
    print("3. Copiar tus assets y archivos estáticos")
    print("4. Ejecutar: pip install -r requirements.txt")
    print("5. Ejecutar: docker-compose up -d")
    print("6. Ejecutar: python app.py")
    print("\n🚀 Para Azure: chmod +x deploy-azure.sh && ./deploy-azure.sh")
    print("\n📖 Consulta README.md para más detalles")

if __name__ == "__main__":
    main()