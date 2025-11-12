# logger/logging_utils_fixed.py
import logging
import json
import time
import os
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Callable
import functools

class OpenAILogger:
    """
    Logger especializado para registrar interacciones con OpenAI API.
    Permite logging detallado con formato consistente.
    """
    
    def __init__(self, log_level=logging.DEBUG, log_dir='logs'):
        """
        Inicializa el sistema de logging para OpenAI.
        
        Args:
            log_level: Nivel de logging (default: DEBUG)
            log_dir: Directorio donde se guardarán los logs
        """
        # Crear directorio de logs si no existe
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Configurar logger para consola
        self.console_logger = logging.getLogger('chatbot.openai.console')
        self.console_logger.setLevel(log_level)
        
        # Limpiar handlers existentes para evitar duplicados
        if self.console_logger.handlers:
            self.console_logger.handlers.clear()
        
        # Configurar handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_format)
        self.console_logger.addHandler(console_handler)
        
        # Configurar logger para archivo de peticiones/respuestas
        self.file_logger = logging.getLogger('chatbot.openai.file')
        self.file_logger.setLevel(log_level)
        
        # Limpiar handlers existentes para evitar duplicados
        if self.file_logger.handlers:
            self.file_logger.handlers.clear()
        
        # Crear un nuevo archivo de log cada día
        current_date = datetime.now().strftime('%Y-%m-%d')
        file_handler = logging.FileHandler(
            f'{log_dir}/openai_interactions_{current_date}.log',
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_format)
        self.file_logger.addHandler(file_handler)
        
        # Archivo JSON detallado para análisis posterior
        self.json_log_path = f'{log_dir}/openai_detailed_{current_date}.jsonl'
    
    def log_request(self, request_data: Dict[str, Any], session_id: str = None, user_id: str = None) -> Dict[str, Any]:
        """
        Registra una petición a OpenAI API.
        
        Args:
            request_data: Datos enviados a OpenAI
            session_id: ID de sesión (opcional)
            user_id: ID de usuario (opcional)
            
        Returns:
            Dict con información de la petición y metadatos
        """
        # Añadir metadatos
        log_entry = {
            "type": "request",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "user_id": user_id,
            "request": request_data
        }
        
        # Log a consola (resumido)
        self.console_logger.info(f"OpenAI Request - Session: {session_id}")
        self.console_logger.debug(f"Request data: {json.dumps(request_data, ensure_ascii=False)[:200]}...")
        
        # Log a archivo (completo)
        self.file_logger.info(f"OpenAI Request - Session: {session_id}")
        self.file_logger.debug(f"Full request: {json.dumps(request_data, ensure_ascii=False)}")
        
        # Guardar en JSONL para análisis posterior
        with open(self.json_log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        
        return log_entry
    
    def log_response(self, response_data: Dict[str, Any], request_entry: Dict[str, Any], 
                    elapsed_time: float = None, token_usage: Dict[str, int] = None,
                    error: Optional[str] = None) -> Dict[str, Any]:
        """
        Registra una respuesta de OpenAI API.
        
        Args:
            response_data: Datos recibidos de OpenAI
            request_entry: Entrada de log de la petición correspondiente
            elapsed_time: Tiempo de respuesta en segundos (opcional)
            token_usage: Información de uso de tokens (opcional)
            error: Error si ocurrió alguno (opcional)
            
        Returns:
            Dict con información de la respuesta y metadatos
        """
        session_id = request_entry.get("session_id", "unknown")
        
        # Añadir metadatos
        log_entry = {
            "type": "response",
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "user_id": request_entry.get("user_id"),
            "request_timestamp": request_entry.get("timestamp"),
            "elapsed_time_ms": int(elapsed_time * 1000) if elapsed_time else None,
            "token_usage": token_usage,
            "error": error,
            "response": response_data
        }
        
        # Log a consola (resumido)
        if error:
            self.console_logger.error(f"OpenAI Error - Session: {session_id} - Error: {error}")
        else:
            self.console_logger.info(f"OpenAI Response - Session: {session_id} - Time: {log_entry['elapsed_time_ms']}ms")
            
            # Log información sobre tokens si está disponible
            if token_usage:
                self.console_logger.info(f"Token usage: {token_usage}")
        
        # Log a archivo (completo)
        self.file_logger.info(f"OpenAI Response - Session: {session_id}")
        if error:
            self.file_logger.error(f"Error: {error}")
        else:
            response_preview = json.dumps(response_data, ensure_ascii=False)[:500] + "..." if len(json.dumps(response_data, ensure_ascii=False)) > 500 else json.dumps(response_data, ensure_ascii=False)
            self.file_logger.debug(f"Response preview: {response_preview}")
            if token_usage:
                self.file_logger.info(f"Token usage: {token_usage}")
        
        # Guardar en JSONL para análisis posterior
        with open(self.json_log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        
        return log_entry


# Decorador simplificado sin problemas de argumentos opcionales
def log_openai_call(logger=None):
    """
    Decorador que registra automáticamente las llamadas a OpenAI.
    
    Uso:
        @log_openai_call()
        def generate_response(self, messages):
            # Código que llama a OpenAI
    """
    if logger is None:
        logger = OpenAILogger()
    
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(self, *args, **kwargs):
            # Extraer información relevante según los argumentos comunes
            messages = None
            session_id = None
            
            # Si el primer argumento es una lista, probablemente son los mensajes
            if args and isinstance(args[0], list):
                messages = args[0]
            # O buscar en kwargs
            elif 'messages' in kwargs:
                messages = kwargs['messages']
                
            # Buscar session_id en los mensajes si es una lista de dicts
            if messages and isinstance(messages, list):
                for msg in messages:
                    if isinstance(msg, dict) and 'session_id' in msg:
                        session_id = msg['session_id']
                        break
            
            # Si no está en messages, buscar en kwargs
            if not session_id and 'session_id' in kwargs:
                session_id = kwargs['session_id']
                
            # Preparar los datos de petición
            request_data = {
                "messages_count": len(messages) if messages else 0,
                "last_message": messages[-1] if messages and len(messages) > 0 else None,
                "kwargs_keys": list(kwargs.keys())
            }
            
            # Log de la petición
            request_entry = logger.log_request(request_data, session_id)
            
            # Medir tiempo
            start_time = time.time()
            
            try:
                # Llamar a la función original
                result = fn(self, *args, **kwargs)
                
                # Calcular tiempo
                elapsed_time = time.time() - start_time
                
                # Preparar los datos de respuesta
                if result is None:
                    response_data = {"result": None}
                elif isinstance(result, str):
                    # Respuestas de texto (común en generate_response)
                    response_data = {
                        "text": result[:200] + "..." if len(result) > 200 else result
                    }
                elif isinstance(result, dict):
                    # Respuestas en formato diccionario
                    response_data = result
                elif hasattr(result, 'model_dump'):
                    # Objetos Pydantic
                    response_data = result.model_dump()
                else:
                    # Otros tipos
                    response_data = {"result_type": str(type(result)), "result_str": str(result)}
                
                # Log de la respuesta
                logger.log_response(
                    response_data=response_data,
                    request_entry=request_entry,
                    elapsed_time=elapsed_time
                )
                
                return result
                
            except Exception as e:
                # Log del error
                elapsed_time = time.time() - start_time
                logger.log_response(
                    response_data={},
                    request_entry=request_entry,
                    elapsed_time=elapsed_time,
                    error=str(e)
                )
                
                # Re-lanzar la excepción
                raise
        
        return wrapper
    
    return decorator