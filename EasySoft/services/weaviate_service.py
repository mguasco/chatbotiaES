# services/weaviate_service.py - VERSIÓN COMPLETA FUNCIONAL
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
                    logging.info(f"? Conectado a Weaviate en {Config.WEAVIATE_HOST}:{Config.WEAVIATE_HTTP_PORT}")
                    return
                
            except Exception as e:
                logging.warning(f"?? Intento {attempt + 1} de conexión a Weaviate falló: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                
        logging.error("? No se pudo conectar a Weaviate después de varios intentos")
        self.client = None

    def search_similar_documents(
        self,
        question_vector: List[float],
        query_text: Optional[str] = None,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Busca documentos similares en Weaviate usando vector search + fallback híbrido.
        """
        try:
            if not self.client or not self.client.is_ready():
                return {"success": False, "context": None, "error": "Weaviate no disponible"}

            collection = self.client.collections.get("Documento")

            # 1?? Búsqueda vectorial principal
            response = collection.query.near_vector(
                near_vector=question_vector,
                limit=max_results,
                return_metadata=wvc.query.MetadataQuery(distance=True)
            )

            results = self._filter_results(response)
            
            # 2?? Si no hay suficientes resultados, usar híbrido (vector + keyword)
            if len(results) < 2 and query_text:
                logging.info("Pocos resultados vectoriales, intentando búsqueda híbrida...")
                try:
                    hybrid_response = collection.query.hybrid(
                        query=query_text,
                        alpha=0.7,  # mezcla entre vector y BM25
                        limit=max_results,
                        return_metadata=wvc.query.MetadataQuery(score=True)
                    )
                    hybrid_results = self._filter_results(hybrid_response, use_distance=False)
                    # Combinar evitando duplicados
                    for r in hybrid_results:
                        if r not in results:
                            results.append(r)
                except Exception as hybrid_error:
                    logging.warning(f"?? Error en búsqueda híbrida: {hybrid_error}")

            context = "\n".join(results) if results else None
            
            return {
                "success": True,
                "context": context,
                "results_count": len(results)
            }

        except Exception as e:
            logging.error(f"Error al consultar Weaviate: {e}")
            return {"success": False, "context": None, "error": str(e)}

    def search_similar_documents_permissive(
        self, 
        question_vector: List[float], 
        query_text: Optional[str] = None, 
        max_results: int = 5
    ) -> Dict[str, Any]:
        """Búsqueda muy permisiva como último recurso"""
        try:
            if not self.client or not self.client.is_ready():
                return {"success": False, "context": None, "error": "Weaviate no disponible"}

            collection = self.client.collections.get("Documento")
            
            # Búsqueda con umbral muy alto (más permisivo)
            response = collection.query.near_vector(
                near_vector=question_vector,
                limit=max_results,
                return_metadata=wvc.query.MetadataQuery(distance=True)
            )

            results = []
            for obj in response.objects:
                content = obj.properties.get("contenido", '').strip()
                if content and len(content) > 20:  # Muy permisivo
                    # Aceptar distancias hasta 0.7 (muy permisivo)
                    if obj.metadata.distance is None or obj.metadata.distance < 0.7:
                        results.append(content)

            context = "\n".join(results) if results else None
            
            return {
                "success": bool(context),
                "context": context,
                "results_count": len(results)
            }
            
        except Exception as e:
            logging.error(f"Error en búsqueda permisiva: {e}")
            return {"success": False, "context": None, "error": str(e)}

    def _filter_results(self, response, use_distance=True) -> List[str]:
        """Filtra resultados eliminando vacíos y no relevantes"""
        filtered_results = []
        for obj in response.objects:
            content = obj.properties.get("contenido", '').strip()
            if not content:
                continue
            if use_distance:
                if obj.metadata.distance is not None and obj.metadata.distance < Config.WEAVIATE_DISTANCE_THRESHOLD:
                    filtered_results.append(content)
            else:
                # Para BM25 o híbrido usamos score, no distance
                filtered_results.append(content)
        return filtered_results

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