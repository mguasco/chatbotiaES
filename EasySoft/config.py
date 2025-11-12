# config.py - Configuración para desarrollo local - SOLO MEJORAS MÍNIMAS
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
    
    # ?? MEJORA PARA CONSISTENCIA: Umbral más permisivo
    WEAVIATE_DISTANCE_THRESHOLD = float(os.getenv('WEAVIATE_DISTANCE_THRESHOLD', 0.45))  # Era 0.35, ahora 0.45
    
    # Flask - Para desarrollo local con subpath
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # URLs para desarrollo local con subpath
    BASE_URL = os.getenv('BASE_URL', 'http://intranetqa.bas.com.ar/chatbotia')
    
    # ?? MEJORAS PARA CONSISTENCIA: Configuración más permisiva
    MAX_HISTORY_MESSAGES = int(os.getenv('MAX_HISTORY_MESSAGES', 8))  # Era 6, ahora 8
    SIMILARITY_THRESHOLD = float(os.getenv('SIMILARITY_THRESHOLD', 0.80))  # Era 0.80, ahora 0.65
    OPENAI_MAX_OUTPUT_TOKENS = int(os.getenv('OPENAI_MAX_OUTPUT_TOKENS', 1800))  # Era 1500, ahora 1800
    
    # Configuración de subpath para reverse proxy
    APPLICATION_ROOT = '/chatbotia'
    
    # Azure (para producción)
    AZURE_STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    AZURE_KEY_VAULT_URL = os.getenv('AZURE_KEY_VAULT_URL')

    # Para escalar a SalesIQ
    ENABLE_HUMAN_ESCALATION = os.getenv('ENABLE_HUMAN_ESCALATION', 'True').lower() == 'true'
    ESCALATION_THRESHOLD = int(os.getenv('ESCALATION_THRESHOLD', 3))  # Intentos antes de escalar
    SALESIQ_WIDGET_CODE = os.getenv('SALESIQ_WIDGET_CODE', 'siqb25b943eaf1f92c7ed086df7176833fd70631f401d4249c45a91bf30aa6ab02f')
