# utils/embeddings.py
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
