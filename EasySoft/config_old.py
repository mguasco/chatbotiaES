# config.py - Configuración para desarrollo local
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Weaviate - Para desarrollo local
    WEAVIATE_HOST = os.getenv('WEAVIATE_HOST', 'localhost')
    WEAVIATE_HTTP_PORT = int(os.getenv('WEAVIATE_HTTP_PORT', 8080))
    WEAVIATE_GRPC_PORT = int(os.getenv('WEAVIATE_GRPC_PORT', 50051))
    WEAVIATE_HTTP_SECURE = os.getenv('WEAVIATE_HTTP_SECURE', 'False').lower() == 'true'
    WEAVIATE_GRPC_SECURE = os.getenv('WEAVIATE_GRPC_SECURE', 'False').lower() == 'true'
    WEAVIATE_DISTANCE_THRESHOLD = float(os.getenv('WEAVIATE_DISTANCE_THRESHOLD', 0.35))
    
    # Flask - Para desarrollo local con subpath
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'  # Debug para desarrollo
    
    # URLs para desarrollo local con subpath
    BASE_URL = os.getenv('BASE_URL', 'http://intranetqa.bas.com.ar/chatbotia')
    
    # Aplicación
    MAX_HISTORY_MESSAGES = int(os.getenv('MAX_HISTORY_MESSAGES', 10))
    SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', 0.80))
    
    # Configuración de subpath para reverse proxy
    APPLICATION_ROOT = '/chatbotia'
    
    # Azure (para producción)
    AZURE_STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    AZURE_KEY_VAULT_URL = os.getenv('AZURE_KEY_VAULT_URL')