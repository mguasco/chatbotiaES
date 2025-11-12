# -*- coding: utf-8 -*-
# services/openai_service.py - VERSIÓN ULTRA-ROBUSTA PARA GPT-5-MINI
import logging
import traceback
import json
from typing import Optional, List, Dict, Any, Union
from openai import OpenAI
from config import Config


class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.system_prompt = (
            "Eres un asistente útil especializado en EasySoft. Responde preguntas solo en base a la "
            "información disponible. Si la información no está en el "
            "contexto, respondé: 'No puedo responder a esa pregunta "
            "con la información disponible.'"
        )
        self.safe_fallback = (
            "No puedo responder a esa pregunta basándome en la "
            "información disponible."
        )
        self.max_out_tokens = getattr(Config, "OPENAI_MAX_OUTPUT_TOKENS", 1500)

    def generate_response(self, messages: List[Dict[str, Any]]) -> Optional[str]:
        """Genera respuesta con manejo ultra-robusto para GPT-5-Mini"""
        try:
            # Preparar mensajes
            system_message = {"role": "system", "content": self.system_prompt}
            full_messages = [system_message] + messages
            normalized_messages = self._normalize_messages(full_messages)
            
            # Log inicial
            logging.info(f"?? Enviando {len(normalized_messages)} mensajes a GPT-5-Mini")
            last_user_msg = normalized_messages[-1]['content'][:100] if normalized_messages else "N/A"
            logging.info(f"?? Último mensaje: {last_user_msg}...")
            
            # Llamada a OpenAI
            response = self.client.chat.completions.create(
                model="gpt-5-mini",
                messages=normalized_messages,
                max_completion_tokens=self.max_out_tokens
            )
            
            # Log detallado de la respuesta RAW
            logging.info(f"?? Respuesta RAW recibida - tipo: {type(response)}")
            
            # EXTRACCIÓN ULTRA-ROBUSTA
            extracted_text = self._extract_text_ultra_robust(response)
            
            if extracted_text and extracted_text.strip():
                final_response = extracted_text.strip()
                logging.info(f"? ÉXITO: Respuesta extraída - {len(final_response)} chars")
                logging.info(f"?? Preview: {final_response[:150]}...")
                return final_response
            else:
                logging.error(f"? FALLO: No se pudo extraer texto válido")
                logging.error(f"?? Debug - extracted_text: '{extracted_text}' (tipo: {type(extracted_text)})")
                
                # Fallback de emergencia
                return self.safe_fallback
                
        except Exception as e:
            logging.error(f"? Error crítico en OpenAI: {e}")
            logging.error(f"?? Traceback completo: {traceback.format_exc()}")
            return None

    def _extract_text_ultra_robust(self, response) -> Optional[str]:
        """Extracción ultra-robusta que maneja todas las variaciones de GPT-5-Mini"""
        
        # Método 1: Estructura estándar - response.choices[0].message.content
        try:
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                logging.info(f"?? Choice encontrado - tipo: {type(choice)}")
                
                # Log finish_reason para debug
                finish_reason = getattr(choice, 'finish_reason', 'unknown')
                logging.info(f"?? Finish reason: {finish_reason}")
                
                if hasattr(choice, 'message'):
                    message = choice.message
                    logging.info(f"?? Message encontrado - tipo: {type(message)}")
                    
                    if hasattr(message, 'content'):
                        content = message.content
                        logging.info(f"?? Content encontrado - tipo: {type(content)}, valor: '{content}'")
                        
                        if content and isinstance(content, str):
                            return content
                        elif content is not None:
                            return str(content)
        except Exception as e:
            logging.warning(f"?? Método 1 falló: {e}")

        # Método 2: Búsqueda en todos los atributos del choice
        try:
            if hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                
                # Inspeccionar todos los atributos del choice
                for attr_name in dir(choice):
                    if not attr_name.startswith('_'):
                        try:
                            attr_value = getattr(choice, attr_name)
                            logging.info(f"?? Choice.{attr_name}: {type(attr_value)} = {attr_value}")
                            
                            # Si encontramos algo que parece texto
                            if isinstance(attr_value, str) and len(attr_value) > 10:
                                logging.info(f"? Texto encontrado en choice.{attr_name}")
                                return attr_value
                                
                            # Si es un objeto con content
                            elif hasattr(attr_value, 'content'):
                                content = attr_value.content
                                if isinstance(content, str) and len(content) > 10:
                                    logging.info(f"? Texto encontrado en choice.{attr_name}.content")
                                    return content
                                    
                        except Exception as attr_error:
                            logging.debug(f"Error accediendo a {attr_name}: {attr_error}")
                            
        except Exception as e:
            logging.warning(f"?? Método 2 falló: {e}")

        # Método 3: Inspección completa del response
        try:
            logging.info("?? Inspeccionando response completo...")
            
            # Convertir a dict si es posible
            if hasattr(response, 'model_dump'):
                response_dict = response.model_dump()
                logging.info(f"?? Response como dict: {json.dumps(response_dict, indent=2, default=str)}")
                
                # Buscar recursivamente cualquier campo que contenga texto largo
                found_text = self._search_text_in_dict(response_dict)
                if found_text:
                    return found_text
                    
            elif hasattr(response, '__dict__'):
                response_dict = response.__dict__
                logging.info(f"?? Response.__dict__: {response_dict}")
                
                found_text = self._search_text_in_dict(response_dict)
                if found_text:
                    return found_text
                    
        except Exception as e:
            logging.warning(f"?? Método 3 falló: {e}")

        # Método 4: Fuerza bruta - inspeccionar todo
        try:
            logging.info("?? Método fuerza bruta...")
            
            for attr_name in dir(response):
                if not attr_name.startswith('_'):
                    try:
                        attr_value = getattr(response, attr_name)
                        logging.info(f"?? Response.{attr_name}: {type(attr_value)}")
                        
                        # Si es string largo, probablemente es la respuesta
                        if isinstance(attr_value, str) and len(attr_value) > 50:
                            logging.info(f"? Posible respuesta en response.{attr_name}: {attr_value[:100]}...")
                            return attr_value
                            
                    except Exception as attr_error:
                        logging.debug(f"Error accediendo a response.{attr_name}: {attr_error}")
                        
        except Exception as e:
            logging.warning(f"?? Método 4 falló: {e}")

        # Si llegamos aquí, nada funcionó
        logging.error("? TODOS los métodos de extracción fallaron")
        return None

    def _search_text_in_dict(self, data: Union[dict, list, Any], path: str = "") -> Optional[str]:
        """Busca recursivamente texto en estructuras de datos"""
        try:
            if isinstance(data, dict):
                for key, value in data.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    # Si el valor es un string largo, es candidato
                    if isinstance(value, str) and len(value) > 50:
                        logging.info(f"? Texto encontrado en {current_path}: {value[:100]}...")
                        return value
                    
                    # Búsqueda recursiva
                    result = self._search_text_in_dict(value, current_path)
                    if result:
                        return result
                        
            elif isinstance(data, list):
                for i, item in enumerate(data):
                    current_path = f"{path}[{i}]" if path else f"[{i}]"
                    result = self._search_text_in_dict(item, current_path)
                    if result:
                        return result
                        
        except Exception as e:
            logging.debug(f"Error en búsqueda recursiva: {e}")
            
        return None

    def _normalize_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normaliza mensajes para asegurar formato correcto"""
        normalized = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Asegurar que content es string
            if not isinstance(content, str):
                content = str(content)
            
            # Limpiar contenido
            content = content.strip()
            
            # Solo agregar mensajes con contenido
            if content:
                normalized.append({
                    "role": role,
                    "content": content
                })
        
        return normalized

    def get_health_status(self) -> str:
        """Verifica el estado de salud de OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-5-mini",
                messages=[{"role": "user", "content": "test"}],
                max_completion_tokens=5
            )
            logging.info("? OpenAI health check exitoso")
            return "connected"
        except Exception as e:
            logging.error(f"? Error en health check de OpenAI: {e}")
            return "error"

    def test_simple_completion(self) -> bool:
        """Test simple para verificar que OpenAI funciona"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-5-mini",
                messages=[{"role": "user", "content": "Di exactamente: TEST_EXITOSO_123"}],
                max_completion_tokens=10  # Usar parámetro correcto
            )
            
            extracted = self._extract_text_ultra_robust(response)
            
            if extracted and "TEST_EXITOSO_123" in extracted:
                logging.info(f"? Test simple exitoso: {extracted}")
                return True
            else:
                logging.error(f"? Test simple falló - respuesta: '{extracted}'")
                return False
                
        except Exception as e:
            logging.error(f"? Test simple falló: {e}")
            return False