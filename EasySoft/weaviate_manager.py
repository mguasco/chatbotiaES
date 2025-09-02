# weaviate_manager.py - Sistema completo de gestión de documentos
import os
import sys
import json
import hashlib
import mimetypes
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
    error: Optional[str] = None
    created_at: str = None
    updated_at: str = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.updated_at is None:
            self.updated_at = self.created_at

class WeaviateManager:
    """Gestor completo de documentos en Weaviate"""
    
    def __init__(self, openai_api_key: str = None):
        self.openai_client = OpenAI(api_key=openai_api_key or Config.OPENAI_API_KEY)
        self.weaviate_client = None
        self.metadata_file = "document_metadata.json"
        self.document_registry = {}
        
        # Configuración de archivos
        self.ignored_extensions = {".gz", ".skn", ".ppf", ".ejs", ".docx", ".pyc", "__pycache__"}
        self.ignored_files = {
            "vectorizatodos.py", "weaviate_manager.py", "app.py", 
            "config.py", "document_metadata.json", ".env", "update_documents.py"
        }
        
        self._connect_weaviate()
        self._load_metadata()

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
                print(f"✅ Conectado a Weaviate en {Config.WEAVIATE_HOST}:{Config.WEAVIATE_HTTP_PORT}")
            else:
                raise Exception("Weaviate no está listo")
                
        except Exception as e:
            print(f"❌ Error conectando a Weaviate: {e}")
            raise

    def _load_metadata(self):
        """Carga metadatos de documentos existentes"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.document_registry = {
                        path: DocumentInfo(**info) for path, info in data.items()
                    }
                print(f"📋 Cargados metadatos de {len(self.document_registry)} documentos")
            except Exception as e:
                print(f"⚠️ Error cargando metadatos: {e}")
                self.document_registry = {}
        else:
            print("📋 No se encontraron metadatos previos, iniciando registro nuevo")

    def _save_metadata(self):
        """Guarda metadatos de documentos"""
        try:
            data = {path: asdict(info) for path, info in self.document_registry.items()}
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"💾 Metadatos guardados para {len(self.document_registry)} documentos")
        except Exception as e:
            print(f"❌ Error guardando metadatos: {e}")

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calcula hash MD5 de un archivo"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"⚠️ Error calculando hash de {file_path}: {e}")
            return ""

    def _should_ignore_file(self, file_path: str) -> bool:
        """Determina si un archivo debe ser ignorado"""
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Verificar extensiones ignoradas
        if file_ext in self.ignored_extensions:
            return True
            
        # Verificar nombres de archivos ignorados
        if file_name in self.ignored_files:
            return True
            
        # Ignorar archivos sin extensión
        if not file_ext:
            return True
            
        return False

    def _extract_text(self, file_path: str) -> Tuple[str, Optional[str]]:
        """Extrae texto de un archivo"""
        try:
            extension = os.path.splitext(file_path)[1].lower()
            
            if extension in (".html", ".htm", ".css", ".js", ".txt", ".py"):
                with open(file_path, "r", encoding="utf-8", errors='ignore') as file:
                    if extension in (".html", ".htm"):
                        soup = BeautifulSoup(file, "html.parser")
                        return soup.get_text(), None
                    return file.read(), None
                    
            elif extension == ".xml":
                with open(file_path, "r", encoding="utf-8", errors='ignore') as file:
                    soup = BeautifulSoup(file, "lxml")
                    return soup.get_text(), None
                    
            elif extension in (".jpg", ".png", ".mp4", ".svg", ".gif"):
                return "", None  # Archivos no textuales
                
            else:
                return "", f"Tipo de archivo no soportado: {extension}"
                
        except Exception as e:
            return "", f"Error extrayendo texto: {e}"

    def _get_embeddings(self, text: str) -> Optional[List[float]]:
        """Obtiene embeddings de OpenAI"""
        if not text or text.strip() == "":
            return None
            
        try:
            # Truncar texto si es muy largo
            max_chars = 8000 * 4  # ~8000 tokens
            if len(text) > max_chars:
                text = text[:max_chars]
                
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"❌ Error obteniendo embeddings: {e}")
            return None

    def _ensure_collection_exists(self):
        """Asegura que la colección Documento existe"""
        try:
            if self.weaviate_client.collections.exists("Documento"):
                print("✅ Colección 'Documento' existe")
                return True
                
            # Crear la colección
            self.weaviate_client.collections.create(
                name="Documento",
                properties=[
                    Property(name="contenido", data_type=DataType.TEXT),
                    Property(name="nombre_archivo", data_type=DataType.TEXT),
                    Property(name="ruta_archivo", data_type=DataType.TEXT),
                    Property(name="tipo_archivo", data_type=DataType.TEXT),
                    Property(name="hash_archivo", data_type=DataType.TEXT),
                    Property(name="fecha_modificacion", data_type=DataType.DATE),
                    Property(name="tamano_archivo", data_type=DataType.INT),
                ],
                vectorizer_config=Configure.Vectorizer.none()
            )
            print("✅ Colección 'Documento' creada exitosamente")
            return True
            
        except Exception as e:
            print(f"❌ Error creando colección: {e}")
            return False

    def scan_directory(self, root_path: str) -> Dict[str, DocumentInfo]:
        """Escanea un directorio y devuelve información de archivos"""
        found_files = {}
        
        print(f"🔍 Escaneando directorio: {root_path}")
        
        for root, dirs, files in os.walk(root_path):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                
                # Saltar archivos ignorados
                if self._should_ignore_file(file_path):
                    continue
                
                try:
                    stat = os.stat(file_path)
                    file_hash = self._calculate_file_hash(file_path)
                    
                    # Extraer texto para obtener longitud
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
                    print(f"⚠️ Error procesando {file_path}: {e}")
                    
        print(f"📊 Encontrados {len(found_files)} archivos")
        return found_files

    def detect_changes(self, found_files: Dict[str, DocumentInfo]) -> Dict[str, List[str]]:
        """Detecta cambios entre archivos encontrados y registrados"""
        changes = {
            "new": [],      # Archivos nuevos
            "modified": [], # Archivos modificados
            "deleted": [],  # Archivos eliminados
            "unchanged": [] # Archivos sin cambios
        }
        
        # Detectar archivos nuevos y modificados
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
        
        # Detectar archivos eliminados
        for file_path in self.document_registry:
            if file_path not in found_files:
                changes["deleted"].append(file_path)
        
        return changes

    def add_document_to_weaviate(self, doc_info: DocumentInfo) -> bool:
        """Agrega un documento a Weaviate"""
        try:
            # Extraer texto
            text, error = self._extract_text(doc_info.file_path)
            if error:
                doc_info.error = error
                print(f"⚠️ Error en {doc_info.file_name}: {error}")
                return False
            
            # Obtener embeddings
            vector = self._get_embeddings(text)
            if vector is None and text.strip():
                doc_info.error = "No se pudieron obtener embeddings"
                print(f"⚠️ No se pudieron obtener embeddings para {doc_info.file_name}")
                return False
            
            # Preparar propiedades
            properties = {
                "contenido": text if text else "Archivo sin contenido extraíble",
                "nombre_archivo": doc_info.file_name,
                "ruta_archivo": doc_info.file_path,
                "tipo_archivo": mimetypes.guess_type(doc_info.file_path)[0] or "desconocido",
                "hash_archivo": doc_info.file_hash,
                "fecha_modificacion": datetime.fromtimestamp(doc_info.last_modified).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "tamano_archivo": doc_info.file_size
            }
            
            # Insertar en Weaviate
            collection = self.weaviate_client.collections.get("Documento")
            
            if vector is not None:
                collection.data.insert(
                    properties=properties,
                    vector=vector,
                    uuid=generate_uuid5(doc_info.file_path)
                )
            else:
                collection.data.insert(
                    properties=properties,
                    uuid=generate_uuid5(doc_info.file_path)
                )
            
            doc_info.vectorized = True
            doc_info.updated_at = datetime.now().isoformat()
            print(f"✅ {doc_info.file_name} agregado exitosamente")
            return True
            
        except Exception as e:
            doc_info.error = str(e)
            print(f"❌ Error agregando {doc_info.file_name}: {e}")
            return False

    def remove_document_from_weaviate(self, file_path: str) -> bool:
        """Elimina un documento de Weaviate"""
        try:
            collection = self.weaviate_client.collections.get("Documento")
            collection.data.delete_by_id(generate_uuid5(file_path))
            print(f"🗑️ Documento eliminado: {os.path.basename(file_path)}")
            return True
        except Exception as e:
            print(f"❌ Error eliminando documento {file_path}: {e}")
            return False

    def update_documents(self, root_path: str, force_rebuild: bool = False) -> Dict[str, int]:
        """Actualiza documentos en Weaviate"""
        if not self._ensure_collection_exists():
            return {"error": 1}
        
        # Escanear archivos
        found_files = self.scan_directory(root_path)
        
        if force_rebuild:
            print("🔄 Forzando reconstrucción completa...")
            # Eliminar colección y recrear
            try:
                self.weaviate_client.collections.delete("Documento")
                self._ensure_collection_exists()
                changes = {"new": list(found_files.keys()), "modified": [], "deleted": [], "unchanged": []}
                self.document_registry.clear()
            except Exception as e:
                print(f"❌ Error en reconstrucción: {e}")
                return {"error": 1}
        else:
            # Detectar cambios
            changes = self.detect_changes(found_files)
        
        # Estadísticas
        stats = {
            "new": 0,
            "modified": 0, 
            "deleted": 0,
            "unchanged": len(changes["unchanged"]),
            "errors": 0
        }
        
        print(f"\n📊 Resumen de cambios:")
        print(f"   🆕 Nuevos: {len(changes['new'])}")
        print(f"   🔄 Modificados: {len(changes['modified'])}")
        print(f"   🗑️ Eliminados: {len(changes['deleted'])}")
        print(f"   ✅ Sin cambios: {len(changes['unchanged'])}")
        
        # Procesar archivos eliminados
        for file_path in changes["deleted"]:
            if self.remove_document_from_weaviate(file_path):
                del self.document_registry[file_path]
                stats["deleted"] += 1
            else:
                stats["errors"] += 1
        
        # Procesar archivos nuevos
        for file_path in changes["new"]:
            doc_info = found_files[file_path]
            if self.add_document_to_weaviate(doc_info):
                self.document_registry[file_path] = doc_info
                stats["new"] += 1
            else:
                stats["errors"] += 1
        
        # Procesar archivos modificados
        for file_path in changes["modified"]:
            # Primero eliminar el anterior
            self.remove_document_from_weaviate(file_path)
            
            # Luego agregar el nuevo
            doc_info = found_files[file_path]
            if self.add_document_to_weaviate(doc_info):
                self.document_registry[file_path] = doc_info
                stats["modified"] += 1
            else:
                stats["errors"] += 1
        
        # Guardar metadatos
        self._save_metadata()
        
        return stats

    def get_statistics(self) -> Dict:
        """Obtiene estadísticas de la base de datos"""
        try:
            collection = self.weaviate_client.collections.get("Documento")
            response = collection.aggregate.over_all(total_count=True)
            
            total_docs = response.total_count
            vectorized_docs = len([doc for doc in self.document_registry.values() if doc.vectorized])
            docs_with_errors = len([doc for doc in self.document_registry.values() if doc.error])
            
            return {
                "total_documents_weaviate": total_docs,
                "total_documents_registry": len(self.document_registry),
                "vectorized_documents": vectorized_docs,
                "documents_with_errors": docs_with_errors,
                "registry_file_exists": os.path.exists(self.metadata_file)
            }
        except Exception as e:
            print(f"❌ Error obteniendo estadísticas: {e}")
            return {"error": str(e)}

    def cleanup(self):
        """Limpia recursos"""
        if self.weaviate_client:
            self.weaviate_client.close()
            print("🔌 Conexión a Weaviate cerrada")

def main():
    parser = argparse.ArgumentParser(description="Gestor de documentos Weaviate")
    parser.add_argument("command", choices=["update", "rebuild", "stats", "scan"], 
                       help="Comando a ejecutar")
    parser.add_argument("--path", "-p", default="C:\\Easysoft", 
                       help="Ruta del directorio a procesar")
    parser.add_argument("--api-key", help="API key de OpenAI")
    
    args = parser.parse_args()
    
    try:
        manager = WeaviateManager(args.api_key)
        
        if args.command == "update":
            print("🚀 Actualizando documentos...")
            stats = manager.update_documents(args.path)
            
            print(f"\n📈 Resultados:")
            for key, value in stats.items():
                print(f"   {key}: {value}")
                
        elif args.command == "rebuild":
            print("🔄 Reconstruyendo base de datos completa...")
            stats = manager.update_documents(args.path, force_rebuild=True)
            
            print(f"\n📈 Resultados:")
            for key, value in stats.items():
                print(f"   {key}: {value}")
                
        elif args.command == "stats":
            print("📊 Obteniendo estadísticas...")
            stats = manager.get_statistics()
            
            print(f"\n📈 Estadísticas actuales:")
            for key, value in stats.items():
                print(f"   {key}: {value}")
                
        elif args.command == "scan":
            print("🔍 Escaneando directorio...")
            found_files = manager.scan_directory(args.path)
            changes = manager.detect_changes(found_files)
            
            print(f"\n📊 Análisis de cambios:")
            for change_type, files in changes.items():
                print(f"   {change_type}: {len(files)} archivos")
                if len(files) <= 10:  # Mostrar hasta 10 archivos por tipo
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
