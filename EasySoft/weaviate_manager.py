# weaviate_manager.py - Sistema con chunking inteligente y logging corregido
import os
import sys
import json
import hashlib
import mimetypes
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import argparse

from openai import OpenAI
from bs4 import BeautifulSoup
import weaviate
from weaviate.classes.config import Configure, Property, DataType
from weaviate.connect import ConnectionParams
from weaviate.util import generate_uuid5
import weaviate.classes as wvc
import numpy as np

from config import Config

@dataclass
class DocumentInfo:
    """Información sobre un documento"""
    file_path: str
    file_name: str
    file_hash: str
    last_modified: float
    file_size: int
    content_length: int
    vectorized: bool = False
    chunked: bool = False
    chunks_count: int = 0
    error: Optional[str] = None
    created_at: str = None
    updated_at: str = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at

@dataclass
class ProcessingStats:
    """Estadísticas de procesamiento"""
    new: int = 0
    modified: int = 0
    deleted: int = 0
    unchanged: int = 0
    errors: int = 0
    chunked_files: int = 0
    total_chunks: int = 0
    vectorized_documents: int = 0
    skipped_large: int = 0

class WeaviateManager:
    """Gestor completo de documentos en Weaviate con chunking inteligente"""
    
    def __init__(self, openai_api_key: str = None):
        self.openai_client = OpenAI(api_key=openai_api_key or Config.OPENAI_API_KEY)
        self.weaviate_client = None
        self.metadata_file = "document_metadata.json"
        self.document_registry = {}
        
        # Configurar logging
        self._setup_logging()
        
        # Configuración de archivos
        self.ignored_extensions = {".gz", ".skn", ".ppf", ".ejs", ".docx", ".pyc", "__pycache__"}
        self.ignored_files = {
            "vectorizatodos.py", "weaviate_manager.py", "app.py", 
            "config.py", "document_metadata.json", ".env", "update_documents.py"
        }
        
        # CONFIGURACIÓN DE CHUNKING CORREGIDA
        self.MAX_TOKENS = 7000  # Límite más conservador para text-embedding-3-large
        self.MAX_CHARS = self.MAX_TOKENS * 3  # ~18,000 chars (más seguro)
        self.CHUNK_OVERLAP = 300  # Overlap reducido entre chunks
        
        # EXTENSIONES CORREGIDAS - Incluir CSS/JS para chunking
        self.CHUNK_PRIORITY_EXTENSIONS = {".html", ".htm", ".txt", ".md", ".py", ".css", ".js"}
        
        self._connect_weaviate()
        self._load_metadata()

    def _setup_logging(self):
        """Configura el sistema de logging"""
        log_filename = f"vectorization_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"🚀 Iniciando WeaviateManager - Log: {log_filename}")

    def _connect_weaviate(self):
        """Conecta a Weaviate"""
        try:
            if Config.WEAVIATE_HTTP_SECURE:
                self.weaviate_client = weaviate.connect_to_custom(
                    http_host=Config.WEAVIATE_HOST,
                    http_port=Config.WEAVIATE_HTTP_PORT,
                    http_secure=Config.WEAVIATE_HTTP_SECURE,
                    grpc_host=Config.WEAVIATE_HOST,
                    grpc_port=Config.WEAVIATE_GRPC_PORT,
                    grpc_secure=Config.WEAVIATE_GRPC_SECURE
                )
            else:
                self.weaviate_client = weaviate.connect_to_local(
                    host=Config.WEAVIATE_HOST,
                    port=Config.WEAVIATE_HTTP_PORT,
                    grpc_port=Config.WEAVIATE_GRPC_PORT
                )
            
            if self.weaviate_client.is_ready():
                self.logger.info(f"✅ Conectado a Weaviate en {Config.WEAVIATE_HOST}:{Config.WEAVIATE_HTTP_PORT}")
            else:
                raise Exception("Weaviate no está listo")
                
        except Exception as e:
            self.logger.error(f"❌ Error conectando a Weaviate: {e}")
            raise

    def _load_metadata(self):
        """Carga metadatos de documentos existentes"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Actualizar para compatibilidad con nuevos campos
                    for path, info in data.items():
                        if 'chunked' not in info:
                            info['chunked'] = False
                        if 'chunks_count' not in info:
                            info['chunks_count'] = 0
                    
                    self.document_registry = {
                        path: DocumentInfo(**info) for path, info in data.items()
                    }
                self.logger.info(f"📋 Cargados metadatos de {len(self.document_registry)} documentos")
            except Exception as e:
                self.logger.warning(f"⚠️ Error cargando metadatos: {e}")
                self.document_registry = {}
        else:
            self.logger.info("📋 No se encontraron metadatos previos, iniciando registro nuevo")

    def _save_metadata(self):
        """Guarda metadatos de documentos"""
        try:
            data = {path: asdict(info) for path, info in self.document_registry.items()}
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"💾 Metadatos guardados para {len(self.document_registry)} documentos")
        except Exception as e:
            self.logger.error(f"❌ Error guardando metadatos: {e}")

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calcula hash MD5 de un archivo"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.logger.warning(f"⚠️ Error calculando hash de {file_path}: {e}")
            return ""

    def _should_ignore_file(self, file_path: str) -> bool:
        """Determina si un archivo debe ser ignorado"""
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext in self.ignored_extensions:
            return True
        if file_name in self.ignored_files:
            return True
        if not file_ext:
            return True
            
        return False

    def _extract_text(self, file_path: str) -> Tuple[str, Optional[str]]:
        """Extrae texto de un archivo"""
        try:
            extension = os.path.splitext(file_path)[1].lower()
            
            if extension in (".html", ".htm", ".css", ".js", ".txt", ".py"):
                with open(file_path, "r", encoding="utf-8", errors='ignore') as file:
                    content = file.read()
                    if extension in (".html", ".htm"):
                        soup = BeautifulSoup(content, "html.parser")
                        text = soup.get_text()
                    else:
                        text = content
                    return text, None
                    
            elif extension == ".xml":
                with open(file_path, "r", encoding="utf-8", errors='ignore') as file:
                    content = file.read()
                    soup = BeautifulSoup(content, "lxml")
                    text = soup.get_text()
                    return text, None
                    
            elif extension in (".jpg", ".png", ".mp4", ".svg", ".gif"):
                return "", None
                
            else:
                return "", f"Tipo de archivo no soportado: {extension}"
                
        except Exception as e:
            return "", f"Error extrayendo texto: {e}"

    def _get_embeddings(self, text: str) -> Optional[List[float]]:
        """Obtiene embeddings de OpenAI"""
        if not text or text.strip() == "":
            return None
            
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-large",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo embeddings: {e}")
            return None

    def _validate_chunk_size(self, text: str) -> bool:
        """Valida que el chunk no exceda límites de tokens"""
        # Estimación conservadora: 1 token ≈ 3.5 chars en promedio
        estimated_tokens = len(text) / 3.5
        return estimated_tokens <= self.MAX_TOKENS

    def _create_intelligent_chunks(self, text: str, file_path: str) -> List[str]:
        """Crea chunks inteligentes del texto con validación de tamaño"""
        if len(text) <= self.MAX_CHARS:
            return [text]
        
        extension = os.path.splitext(file_path)[1].lower()
        chunks = []
        
        # Tamaño efectivo del chunk (dejando espacio para overlap)
        effective_chunk_size = self.MAX_CHARS - self.CHUNK_OVERLAP
        
        if extension in (".html", ".htm"):
            # Para HTML: intentar dividir por secciones/párrafos
            chunks = self._chunk_by_html_structure(text, effective_chunk_size)
        elif extension in (".js", ".py", ".css"):
            # Para código: dividir por funciones/bloques
            chunks = self._chunk_by_code_structure(text, effective_chunk_size)
        else:
            # División general por párrafos/líneas
            chunks = self._chunk_by_paragraphs(text, effective_chunk_size)
        
        # VALIDACIÓN DE TAMAÑO - Dividir chunks que aún sean muy grandes
        validated_chunks = []
        for chunk in chunks:
            if self._validate_chunk_size(chunk):
                validated_chunks.append(chunk)
            else:
                # Dividir chunk muy grande en pedazos más pequeños
                sub_chunks = self._force_split_chunk(chunk, self.MAX_CHARS // 2)
                validated_chunks.extend(sub_chunks)
        
        # Añadir overlap entre chunks para contexto
        overlapped_chunks = []
        for i, chunk in enumerate(validated_chunks):
            if i > 0:
                # Añadir overlap del chunk anterior
                prev_chunk = validated_chunks[i-1]
                overlap_text = prev_chunk[-self.CHUNK_OVERLAP:] if len(prev_chunk) > self.CHUNK_OVERLAP else prev_chunk
                chunk = overlap_text + "\n" + chunk
                
                # Validar que con overlap no exceda límites
                if not self._validate_chunk_size(chunk):
                    chunk = validated_chunks[i]  # Usar sin overlap si excede
                    
            overlapped_chunks.append(chunk)
        
        self.logger.info(f"📄 {os.path.basename(file_path)}: {len(overlapped_chunks)} chunks creados y validados")
        return overlapped_chunks

    def _force_split_chunk(self, text: str, max_size: int) -> List[str]:
        """Fuerza división de chunk muy grande en pedazos más pequeños"""
        chunks = []
        for i in range(0, len(text), max_size):
            chunks.append(text[i:i+max_size])
        return chunks

    def _chunk_by_html_structure(self, text: str, chunk_size: int) -> List[str]:
        """Divide HTML por estructura semántica"""
        try:
            soup = BeautifulSoup(text, 'html.parser')
            
            # Intentar dividir por secciones principales
            sections = soup.find_all(['section', 'div', 'article', 'main'])
            if not sections:
                sections = soup.find_all(['h1', 'h2', 'h3'])
            
            chunks = []
            current_chunk = ""
            
            for section in sections:
                section_text = section.get_text(strip=True)
                if len(current_chunk) + len(section_text) > chunk_size:
                    if current_chunk:
                        chunks.append(current_chunk)
                        current_chunk = section_text
                    else:
                        # Sección muy grande, dividir por párrafos
                        chunks.extend(self._chunk_by_paragraphs(section_text, chunk_size))
                else:
                    current_chunk += "\n" + section_text
            
            if current_chunk:
                chunks.append(current_chunk)
            
            return chunks if chunks else self._chunk_by_paragraphs(text, chunk_size)
            
        except:
            return self._chunk_by_paragraphs(text, chunk_size)

    def _chunk_by_code_structure(self, text: str, chunk_size: int) -> List[str]:
        """Divide código por funciones/bloques"""
        lines = text.split('\n')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for line in lines:
            line_size = len(line) + 1  # +1 por el \n
            
            # Si la línea es muy larga, la dividimos
            if line_size > chunk_size:
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # Dividir línea larga
                for i in range(0, len(line), chunk_size):
                    chunks.append(line[i:i+chunk_size])
                continue
            
            # Si añadir esta línea excede el tamaño
            if current_size + line_size > chunk_size:
                chunks.append('\n'.join(current_chunk))
                current_chunk = [line]
                current_size = line_size
            else:
                current_chunk.append(line)
                current_size += line_size
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks

    def _chunk_by_paragraphs(self, text: str, chunk_size: int) -> List[str]:
        """División general por párrafos"""
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = para
                else:
                    # Párrafo muy largo, dividir por líneas
                    lines = para.split('\n')
                    for line in lines:
                        if len(current_chunk) + len(line) > chunk_size:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                                current_chunk = line
                            else:
                                # Línea muy larga, dividir por caracteres
                                for i in range(0, len(line), chunk_size):
                                    chunks.append(line[i:i+chunk_size])
                        else:
                            current_chunk += "\n" + line
            else:
                current_chunk += "\n\n" + para
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks

    def _process_large_document(self, doc_info: DocumentInfo, text: str) -> bool:
        """Procesa documentos usando chunking inteligente"""
        if len(text) <= self.MAX_CHARS:
            # Archivo normal
            return self._add_single_document(doc_info, text, is_chunk=False)
        
        extension = os.path.splitext(doc_info.file_path)[1].lower()
        
        # CORRECCIÓN: Usar chunking para todos los archivos de código/web grandes
        if extension in self.CHUNK_PRIORITY_EXTENSIONS or extension in (".css", ".js"):
            # Usar chunking inteligente
            chunks = self._create_intelligent_chunks(text, doc_info.file_path)
            self.logger.info(f"📄 {doc_info.file_name}: dividido en {len(chunks)} chunks inteligentes")
        else:
            # Solo truncar para archivos menos importantes
            self.logger.info(f"⚠️ {doc_info.file_name}: archivo largo ({len(text)} chars), truncando...")
            chunks = [text[:self.MAX_CHARS]]
        
        success_count = 0
        
        # Procesar cada chunk
        for idx, chunk in enumerate(chunks, 1):
            chunk_doc_info = DocumentInfo(
                file_path=f"{doc_info.file_path}_chunk_{idx}",
                file_name=f"{doc_info.file_name} (parte {idx}/{len(chunks)})",
                file_hash=f"{doc_info.file_hash}_chunk_{idx}",
                last_modified=doc_info.last_modified,
                file_size=len(chunk),
                content_length=len(chunk),
                chunked=True,
                chunks_count=len(chunks)
            )
            
            if self._add_single_document(chunk_doc_info, chunk, is_chunk=True):
                success_count += 1
        
        # Actualizar info del documento original
        doc_info.vectorized = success_count > 0
        doc_info.chunked = len(chunks) > 1
        doc_info.chunks_count = len(chunks)
        doc_info.error = None if success_count == len(chunks) else f"Solo {success_count}/{len(chunks)} chunks procesados"
        
        # Log detallado
        self.logger.info(f"✅ {doc_info.file_name}: {success_count}/{len(chunks)} chunks vectorizados")
        
        return success_count > 0

    def _add_single_document(self, doc_info: DocumentInfo, text: str, is_chunk: bool = False) -> bool:
        """Agrega un documento individual (chunk o completo)"""
        try:
            # VALIDACIÓN PREVIA DE TAMAÑO
            if not self._validate_chunk_size(text):
                self.logger.warning(f"⚠️ Chunk muy grande para {doc_info.file_name}, truncando...")
                text = text[:self.MAX_CHARS]
            
            # Obtener embeddings
            vector = self._get_embeddings(text)
            if vector is None and text.strip():
                self.logger.warning(f"⚠️ No se pudieron obtener embeddings para {doc_info.file_name}")
                return False
            
            # Preparar propiedades
            original_path = doc_info.file_path.split('_chunk_')[0] if is_chunk else doc_info.file_path
            properties = {
                "contenido": text,
                "nombre_archivo": doc_info.file_name,
                "ruta_archivo": doc_info.file_path,
                "archivo_original": original_path,
                "es_chunk": is_chunk,
                "numero_chunk": int(doc_info.file_path.split('_chunk_')[-1]) if is_chunk else 0,
                "tipo_archivo": mimetypes.guess_type(original_path)[0] or "desconocido",
                "hash_archivo": doc_info.file_hash,
                "fecha_modificacion": datetime.fromtimestamp(doc_info.last_modified).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "tamano_archivo": doc_info.file_size
            }
            
            # Generar UUID único
            unique_id = generate_uuid5(f"{doc_info.file_path}_{doc_info.file_hash}")
            
            # Insertar en Weaviate
            collection = self.weaviate_client.collections.get("Documento")
            
            # Eliminar si existe (para evitar duplicados)
            try:
                collection.data.delete_by_id(unique_id)
            except:
                pass
            
            collection.data.insert(
                properties=properties,
                vector=vector,
                uuid=unique_id
            )
            
            # CORRECCIÓN DEL CONTADOR: Marcar como vectorizado
            if not is_chunk:
                doc_info.vectorized = True
            
            # Log específico
            chunk_info = f" (chunk)" if is_chunk else ""
            self.logger.info(f"✅ VECTORIZADO: {doc_info.file_name}{chunk_info} - {len(text)} chars")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error agregando {doc_info.file_name}: {e}")
            return False

    def _ensure_collection_exists(self):
        """Asegura que la colección Documento existe con nuevos campos"""
        try:
            if self.weaviate_client.collections.exists("Documento"):
                self.logger.info("✅ Colección 'Documento' existe")
                return True
                
            # Crear la colección con campos adicionales para chunking
            self.weaviate_client.collections.create(
                name="Documento",
                properties=[
                    Property(name="contenido", data_type=DataType.TEXT),
                    Property(name="nombre_archivo", data_type=DataType.TEXT),
                    Property(name="ruta_archivo", data_type=DataType.TEXT),
                    Property(name="archivo_original", data_type=DataType.TEXT),
                    Property(name="es_chunk", data_type=DataType.BOOL),
                    Property(name="numero_chunk", data_type=DataType.INT),
                    Property(name="tipo_archivo", data_type=DataType.TEXT),
                    Property(name="hash_archivo", data_type=DataType.TEXT),
                    Property(name="fecha_modificacion", data_type=DataType.DATE),
                    Property(name="tamano_archivo", data_type=DataType.INT),
                ],
                vectorizer_config=Configure.Vectorizer.none()
            )
            self.logger.info("✅ Colección 'Documento' creada con campos de chunking")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error creando colección: {e}")
            return False

    def scan_directory(self, root_path: str) -> Dict[str, DocumentInfo]:
        """Escanea un directorio y devuelve información de archivos"""
        found_files = {}
        
        self.logger.info(f"🔍 Escaneando directorio: {root_path}")
        
        for root, dirs, files in os.walk(root_path):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                
                if self._should_ignore_file(file_path):
                    continue
                
                try:
                    stat = os.stat(file_path)
                    file_hash = self._calculate_file_hash(file_path)
                    
                    text, error = self._extract_text(file_path)
                    content_length = len(text) if text else 0
                    
                    doc_info = DocumentInfo(
                        file_path=file_path,
                        file_name=file_name,
                        file_hash=file_hash,
                        last_modified=stat.st_mtime,
                        file_size=stat.st_size,
                        content_length=content_length,
                        error=error
                    )
                    
                    found_files[file_path] = doc_info
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Error procesando {file_path}: {e}")
                    
        self.logger.info(f"📊 Encontrados {len(found_files)} archivos")
        return found_files

    def detect_changes(self, found_files: Dict[str, DocumentInfo]) -> Dict[str, List[str]]:
        """Detecta cambios entre archivos encontrados y registrados"""
        changes = {
            "new": [],
            "modified": [],
            "deleted": [],
            "unchanged": []
        }
        
        for file_path, found_info in found_files.items():
            if file_path not in self.document_registry:
                changes["new"].append(file_path)
            else:
                registered_info = self.document_registry[file_path]
                if (found_info.file_hash != registered_info.file_hash or 
                    found_info.last_modified != registered_info.last_modified):
                    changes["modified"].append(file_path)
                else:
                    changes["unchanged"].append(file_path)
        
        for file_path in self.document_registry:
            if file_path not in found_files:
                changes["deleted"].append(file_path)
        
        return changes

    def add_document_to_weaviate(self, doc_info: DocumentInfo) -> bool:
        """Agrega un documento a Weaviate con chunking inteligente"""
        try:
            text, error = self._extract_text(doc_info.file_path)
            if error:
                doc_info.error = error
                self.logger.warning(f"⚠️ Error en {doc_info.file_name}: {error}")
                return False
            
            # CORRECCIÓN: Decidir estrategia y marcar como vectorizado
            if len(text) <= self.MAX_CHARS:
                # Archivo normal - procesamiento directo
                success = self._add_single_document(doc_info, text, is_chunk=False)
                if success:
                    doc_info.vectorized = True
                return success
            else:
                # Archivo grande - usar chunking
                return self._process_large_document(doc_info, text)
            
        except Exception as e:
            doc_info.error = str(e)
            self.logger.error(f"❌ Error procesando {doc_info.file_name}: {e}")
            return False

    def remove_document_from_weaviate(self, file_path: str) -> bool:
        """Elimina un documento y todos sus chunks de Weaviate"""
        try:
            doc_info = self.document_registry.get(file_path)
            if not doc_info:
                return True
            
            collection = self.weaviate_client.collections.get("Documento")
            removed_count = 0
            
            # Si tiene chunks, eliminar todos
            if doc_info.chunked and doc_info.chunks_count > 1:
                for chunk_idx in range(1, doc_info.chunks_count + 1):
                    chunk_id = generate_uuid5(f"{file_path}_chunk_{chunk_idx}_{doc_info.file_hash}_chunk_{chunk_idx}")
                    try:
                        collection.data.delete_by_id(chunk_id)
                        removed_count += 1
                    except:
                        pass
                self.logger.info(f"🗑️ {removed_count} chunks eliminados de: {os.path.basename(file_path)}")
            else:
                # Documento individual
                unique_id = generate_uuid5(f"{file_path}_{doc_info.file_hash}")
                collection.data.delete_by_id(unique_id)
                removed_count = 1
                self.logger.info(f"🗑️ Documento eliminado: {os.path.basename(file_path)}")
            
            return removed_count > 0
            
        except Exception as e:
            self.logger.error(f"❌ Error eliminando documento {file_path}: {e}")
            return False

    def update_documents(self, root_path: str, force_rebuild: bool = False) -> Dict[str, int]:
        """Actualiza documentos en Weaviate"""
        stats = ProcessingStats()
        
        if not self._ensure_collection_exists():
            return {"error": 1}
        
        found_files = self.scan_directory(root_path)
        
        if force_rebuild:
            self.logger.info("🔄 Forzando reconstrucción completa...")
            try:
                self.weaviate_client.collections.delete("Documento")
                self._ensure_collection_exists()
                changes = {"new": list(found_files.keys()), "modified": [], "deleted": [], "unchanged": []}
                self.document_registry.clear()
            except Exception as e:
                self.logger.error(f"❌ Error en reconstrucción: {e}")
                return {"error": 1}
        else:
            changes = self.detect_changes(found_files)
        
        stats.unchanged = len(changes["unchanged"])
        
        self.logger.info(f"📊 Resumen de cambios:")
        self.logger.info(f"   🆕 Nuevos: {len(changes['new'])}")
        self.logger.info(f"   📄 Modificados: {len(changes['modified'])}")
        self.logger.info(f"   🗑️ Eliminados: {len(changes['deleted'])}")
        self.logger.info(f"   ✅ Sin cambios: {len(changes['unchanged'])}")
        
        # Procesar eliminaciones
        for file_path in changes["deleted"]:
            if self.remove_document_from_weaviate(file_path):
                del self.document_registry[file_path]
                stats.deleted += 1
            else:
                stats.errors += 1
        
        # Procesar nuevos
        for file_path in changes["new"]:
            doc_info = found_files[file_path]
            if self.add_document_to_weaviate(doc_info):
                self.document_registry[file_path] = doc_info
                stats.new += 1
                # CORRECCIÓN DEL CONTADOR: Contar documentos vectorizados correctamente
                if doc_info.vectorized:
                    stats.vectorized_documents += 1
                if doc_info.chunked:
                    stats.chunked_files += 1
                    stats.total_chunks += doc_info.chunks_count
            else:
                stats.errors += 1
        
        # Procesar modificados
        for file_path in changes["modified"]:
            self.remove_document_from_weaviate(file_path)
            
            doc_info = found_files[file_path]
            if self.add_document_to_weaviate(doc_info):
                self.document_registry[file_path] = doc_info
                stats.modified += 1
                # CORRECCIÓN DEL CONTADOR: Contar documentos vectorizados correctamente
                if doc_info.vectorized:
                    stats.vectorized_documents += 1
                if doc_info.chunked:
                    stats.chunked_files += 1
                    stats.total_chunks += doc_info.chunks_count
            else:
                stats.errors += 1
        
        self._save_metadata()
        
        # Log final con estadísticas detalladas
        self.logger.info("="*60)
        self.logger.info("📈 RESUMEN FINAL DE PROCESAMIENTO")
        self.logger.info("="*60)
        self.logger.info(f"🆕 Documentos nuevos: {stats.new}")
        self.logger.info(f"📄 Documentos modificados: {stats.modified}")
        self.logger.info(f"🗑️ Documentos eliminados: {stats.deleted}")
        self.logger.info(f"✅ Sin cambios: {stats.unchanged}")
        self.logger.info(f"❌ Errores: {stats.errors}")
        self.logger.info(f"📄 Archivos con chunking: {stats.chunked_files}")
        self.logger.info(f"🔢 Total de chunks: {stats.total_chunks}")
        self.logger.info(f"🎯 Documentos vectorizados: {stats.vectorized_documents}")
        
        return {
            "new": stats.new,
            "modified": stats.modified,
            "deleted": stats.deleted,
            "unchanged": stats.unchanged,
            "errors": stats.errors,
            "chunked_files": stats.chunked_files,
            "total_chunks": stats.total_chunks,
            "vectorized_documents": stats.vectorized_documents
        }

    def get_statistics(self) -> Dict:
        """Obtiene estadísticas detalladas de la base de datos"""
        try:
            collection = self.weaviate_client.collections.get("Documento")
            response = collection.aggregate.over_all(total_count=True)
            
            total_docs = response.total_count
            vectorized_docs = len([doc for doc in self.document_registry.values() if doc.vectorized])
            docs_with_errors = len([doc for doc in self.document_registry.values() if doc.error])
            chunked_docs = len([doc for doc in self.document_registry.values() if doc.chunked])
            total_chunks = sum(doc.chunks_count for doc in self.document_registry.values() if doc.chunks_count > 0)
            
            return {
                "total_documents_weaviate": total_docs,
                "total_documents_registry": len(self.document_registry),
                "vectorized_documents": vectorized_docs,
                "documents_with_errors": docs_with_errors,
                "chunked_documents": chunked_docs,
                "total_chunks_created": total_chunks,
                "registry_file_exists": os.path.exists(self.metadata_file)
            }
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {"error": str(e)}

    def generate_vectorization_report(self) -> str:
        """Genera un reporte detallado de vectorización"""
        report_filename = f"vectorization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        try:
            stats = self.get_statistics()
            
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write("="*80 + "\n")
                f.write("REPORTE DE VECTORIZACIÓN - EasySoft ChatBot\n")
                f.write("="*80 + "\n")
                f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total documentos en Weaviate: {stats.get('total_documents_weaviate', 0)}\n")
                f.write(f"Total documentos en registro: {stats.get('total_documents_registry', 0)}\n")
                f.write(f"Documentos vectorizados: {stats.get('vectorized_documents', 0)}\n")
                f.write(f"Documentos con chunking: {stats.get('chunked_documents', 0)}\n")
                f.write(f"Total chunks creados: {stats.get('total_chunks_created', 0)}\n")
                f.write(f"Documentos con errores: {stats.get('documents_with_errors', 0)}\n")
                f.write("\n" + "="*80 + "\n")
                f.write("DETALLE POR ARCHIVO\n")
                f.write("="*80 + "\n")
                
                # Ordenar documentos por estado
                vectorized = []
                chunked = []
                errors = []
                
                for doc in self.document_registry.values():
                    if doc.error:
                        errors.append(doc)
                    elif doc.chunked:
                        chunked.append(doc)
                    elif doc.vectorized:
                        vectorized.append(doc)
                
                # Documentos con chunking
                if chunked:
                    f.write(f"\n📄 ARCHIVOS CON CHUNKING ({len(chunked)}):\n")
                    f.write("-" * 50 + "\n")
                    for doc in sorted(chunked, key=lambda x: x.chunks_count, reverse=True):
                        f.write(f"{doc.file_name}: {doc.chunks_count} chunks, {doc.content_length:,} chars\n")
                
                # Documentos vectorizados normalmente
                if vectorized:
                    f.write(f"\n✅ ARCHIVOS VECTORIZADOS NORMALMENTE ({len(vectorized)}):\n")
                    f.write("-" * 50 + "\n")
                    for doc in sorted(vectorized, key=lambda x: x.content_length, reverse=True)[:20]:
                        f.write(f"{doc.file_name}: {doc.content_length:,} chars\n")
                    if len(vectorized) > 20:
                        f.write(f"... y {len(vectorized) - 20} más\n")
                
                # Archivos con errores
                if errors:
                    f.write(f"\n❌ ARCHIVOS CON ERRORES ({len(errors)}):\n")
                    f.write("-" * 50 + "\n")
                    for doc in errors:
                        f.write(f"{doc.file_name}: {doc.error}\n")
                
                f.write("\n" + "="*80 + "\n")
                f.write("ARCHIVOS MÁS GRANDES PROCESADOS\n")
                f.write("="*80 + "\n")
                
                large_files = sorted(
                    [doc for doc in self.document_registry.values() if doc.vectorized], 
                    key=lambda x: x.content_length, 
                    reverse=True
                )[:10]
                
                for doc in large_files:
                    chunks_info = f" ({doc.chunks_count} chunks)" if doc.chunked else ""
                    f.write(f"{doc.file_name}: {doc.content_length:,} chars{chunks_info}\n")
            
            self.logger.info(f"📊 Reporte generado: {report_filename}")
            return report_filename
            
        except Exception as e:
            self.logger.error(f"❌ Error generando reporte: {e}")
            return ""

    def cleanup(self):
        """Limpia recursos"""
        if self.weaviate_client:
            self.weaviate_client.close()
            self.logger.info("🔌 Conexión a Weaviate cerrada")

    def reset_database(self):
        """Limpia completamente la base de datos"""
        try:
            self.logger.info("🔄 Limpiando base de datos completamente...")
            
            if self.weaviate_client.collections.exists("Documento"):
                self.weaviate_client.collections.delete("Documento")
                self.logger.info("✅ Colección eliminada")
            
            self.document_registry.clear()
            if os.path.exists(self.metadata_file):
                os.remove(self.metadata_file)
                self.logger.info("✅ Metadatos eliminados")
            
            self._ensure_collection_exists()
            self.logger.info("✅ Base de datos limpia y lista")
            
        except Exception as e:
            self.logger.error(f"❌ Error limpiando base de datos: {e}")

def main():
    parser = argparse.ArgumentParser(description="Gestor de documentos Weaviate con chunking inteligente")
    parser.add_argument("command", choices=["update", "rebuild", "stats", "scan", "reset", "report"], 
                       help="Comando a ejecutar")
    parser.add_argument("--path", "-p", default="/home/chatbotia_BAS/EasySoft", 
                       help="Ruta del directorio a procesar")
    parser.add_argument("--api-key", help="API key de OpenAI")
    
    args = parser.parse_args()
    
    try:
        manager = WeaviateManager(args.api_key)
        
        if args.command == "update":
            print("🚀 Actualizando documentos con chunking inteligente...")
            stats = manager.update_documents(args.path)
            
            if "error" not in stats:
                # Generar reporte automáticamente
                report_file = manager.generate_vectorization_report()
                print(f"\n📊 Reporte generado: {report_file}")
                
        elif args.command == "rebuild":
            print("🔄 Reconstruyendo base de datos completa...")
            stats = manager.update_documents(args.path, force_rebuild=True)
            
            if "error" not in stats:
                report_file = manager.generate_vectorization_report()
                print(f"\n📊 Reporte generado: {report_file}")
                
        elif args.command == "reset":
            print("🗑️ Reseteando base de datos...")
            manager.reset_database()
            
        elif args.command == "stats":
            print("📊 Obteniendo estadísticas...")
            stats = manager.get_statistics()
            
            print(f"\n📈 Estadísticas actuales:")
            for key, value in stats.items():
                print(f"   {key}: {value}")
                
        elif args.command == "report":
            print("📊 Generando reporte detallado...")
            report_file = manager.generate_vectorization_report()
            if report_file:
                print(f"✅ Reporte generado: {report_file}")
            else:
                print("❌ Error generando reporte")
                
        elif args.command == "scan":
            print("🔍 Escaneando directorio...")
            found_files = manager.scan_directory(args.path)
            changes = manager.detect_changes(found_files)
            
            print(f"\n📊 Análisis de cambios:")
            for change_type, files in changes.items():
                print(f"   {change_type}: {len(files)} archivos")
                if len(files) <= 10:
                    for file_path in files:
                        print(f"      - {os.path.basename(file_path)}")
                elif len(files) > 10:
                    print(f"      (mostrando primeros 10 de {len(files)})")
                    for file_path in files[:10]:
                        print(f"      - {os.path.basename(file_path)}")
        
    except Exception as e:
        print(f"❌ Error ejecutando comando: {e}")
        return 1
    finally:
        manager.cleanup()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())