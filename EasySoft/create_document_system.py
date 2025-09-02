#!/usr/bin/env python3
"""
Script para generar el sistema completo de gestión de documentos Weaviate
Ejecuta este script en el directorio de tu proyecto chatbot
"""

import os
import sys

def create_file(filepath, content, description=""):
    """Crea un archivo con el contenido especificado"""
    try:
        # Crear directorio si no existe
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ {description or filepath} creado exitosamente")
    except Exception as e:
        print(f"❌ Error creando {filepath}: {e}")

def main():
    print("🚀 Generando Sistema de Gestión de Documentos Weaviate")
    print("=" * 60)
    
    # 1. weaviate_manager.py - Sistema principal
    weaviate_manager_content = '''# weaviate_manager.py - Sistema completo de gestión de documentos
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
                "fecha_modificacion": datetime.fromtimestamp(doc_info.last_modified).isoformat(),
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
        
        print(f"\\n📊 Resumen de cambios:")
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
    parser.add_argument("--path", "-p", default="C:\\\\Easysoft", 
                       help="Ruta del directorio a procesar")
    parser.add_argument("--api-key", help="API key de OpenAI")
    
    args = parser.parse_args()
    
    try:
        manager = WeaviateManager(args.api_key)
        
        if args.command == "update":
            print("🚀 Actualizando documentos...")
            stats = manager.update_documents(args.path)
            
            print(f"\\n📈 Resultados:")
            for key, value in stats.items():
                print(f"   {key}: {value}")
                
        elif args.command == "rebuild":
            print("🔄 Reconstruyendo base de datos completa...")
            stats = manager.update_documents(args.path, force_rebuild=True)
            
            print(f"\\n📈 Resultados:")
            for key, value in stats.items():
                print(f"   {key}: {value}")
                
        elif args.command == "stats":
            print("📊 Obteniendo estadísticas...")
            stats = manager.get_statistics()
            
            print(f"\\n📈 Estadísticas actuales:")
            for key, value in stats.items():
                print(f"   {key}: {value}")
                
        elif args.command == "scan":
            print("🔍 Escaneando directorio...")
            found_files = manager.scan_directory(args.path)
            changes = manager.detect_changes(found_files)
            
            print(f"\\n📊 Análisis de cambios:")
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
'''

    # 2. update_documents.py - Script simple
    update_documents_content = '''# update_documents.py - Script simple para actualizar documentos
import sys
import os
from weaviate_manager import WeaviateManager

def main():
    """Script simple para actualizar documentos"""
    
    # Configuración por defecto
    DEFAULT_PATH = "C:\\\\Easysoft"  # Cambia esto por tu ruta
    
    # Obtener ruta del argumento o usar la por defecto
    document_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PATH
    
    if not os.path.exists(document_path):
        print(f"❌ Error: La ruta {document_path} no existe")
        print("💡 Uso: python update_documents.py [ruta_documentos]")
        return 1
    
    print("🚀 Iniciando actualización de documentos...")
    print(f"📂 Ruta: {document_path}")
    print("-" * 50)
    
    try:
        manager = WeaviateManager()
        
        # Actualizar documentos
        stats = manager.update_documents(document_path)
        
        if "error" in stats:
            print("❌ Error durante la actualización")
            return 1
        
        # Mostrar resultados
        print("\\n" + "="*50)
        print("📈 RESULTADOS DE LA ACTUALIZACIÓN")
        print("="*50)
        print(f"🆕 Documentos nuevos:     {stats.get('new', 0)}")
        print(f"🔄 Documentos modificados: {stats.get('modified', 0)}")
        print(f"🗑️ Documentos eliminados:  {stats.get('deleted', 0)}")
        print(f"✅ Sin cambios:          {stats.get('unchanged', 0)}")
        print(f"❌ Errores:              {stats.get('errors', 0)}")
        
        total_changes = stats.get('new', 0) + stats.get('modified', 0) + stats.get('deleted', 0)
        
        if total_changes == 0:
            print("\\n🎉 ¡Base de datos actualizada! No hay cambios nuevos.")
        else:
            print(f"\\n🎉 ¡Actualización completada! {total_changes} cambios procesados.")
        
        if stats.get('errors', 0) > 0:
            print("\\n⚠️ Algunos archivos tuvieron errores. Revisa los logs arriba.")
            
    except Exception as e:
        print(f"\\n❌ Error crítico: {e}")
        return 1
    finally:
        manager.cleanup()
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    
    # Pausa para que puedas ver los resultados
    if sys.platform.startswith('win'):
        input("\\nPresiona Enter para continuar...")
    
    sys.exit(exit_code)
'''

    # 3. API endpoints para agregar a app.py
    api_endpoints_content = '''# api_endpoints_add_to_app.py
# INSTRUCCIONES: Agrega estos endpoints a tu archivo app.py

@app.route('/admin/documents/update', methods=['POST'])
def update_documents():
    """Actualiza documentos en Weaviate"""
    try:
        data = request.get_json() or {}
        document_path = data.get('path', 'C:\\\\Easysoft')
        force_rebuild = data.get('force_rebuild', False)
        
        # Verificar permisos (agregar autenticación aquí si es necesario)
        # if not is_admin_user(request):
        #     return jsonify({'error': 'No autorizado'}), 403
        
        from weaviate_manager import WeaviateManager
        
        manager = WeaviateManager()
        try:
            stats = manager.update_documents(document_path, force_rebuild)
            
            if "error" in stats:
                return jsonify({
                    'success': False,
                    'error': 'Error durante la actualización'
                }), 500
            
            return jsonify({
                'success': True,
                'message': 'Documentos actualizados exitosamente',
                'stats': stats
            })
            
        finally:
            manager.cleanup()
            
    except Exception as e:
        logging.error(f"Error en update_documents: {e}")
        return jsonify({
            'success': False,
            'error': f'Error del servidor: {str(e)}'
        }), 500

@app.route('/admin/documents/stats', methods=['GET'])
def get_document_stats():
    """Obtiene estadísticas de documentos"""
    try:
        from weaviate_manager import WeaviateManager
        
        manager = WeaviateManager()
        try:
            stats = manager.get_statistics()
            
            if "error" in stats:
                return jsonify({
                    'success': False,
                    'error': stats['error']
                }), 500
            
            return jsonify({
                'success': True,
                'stats': stats
            })
            
        finally:
            manager.cleanup()
            
    except Exception as e:
        logging.error(f"Error en get_document_stats: {e}")
        return jsonify({
            'success': False,
            'error': f'Error del servidor: {str(e)}'
        }), 500

@app.route('/admin/documents/scan', methods=['POST'])
def scan_documents():
    """Escanea directorio sin actualizar"""
    try:
        data = request.get_json() or {}
        document_path = data.get('path', 'C:\\\\Easysoft')
        
        from weaviate_manager import WeaviateManager
        
        manager = WeaviateManager()
        try:
            found_files = manager.scan_directory(document_path)
            changes = manager.detect_changes(found_files)
            
            # Preparar resumen
            summary = {}
            for change_type, files in changes.items():
                summary[change_type] = {
                    'count': len(files),
                    'files': [os.path.basename(f) for f in files[:10]]  # Primeros 10
                }
            
            return jsonify({
                'success': True,
                'path': document_path,
                'summary': summary,
                'total_files_found': len(found_files)
            })
            
        finally:
            manager.cleanup()
            
    except Exception as e:
        logging.error(f"Error en scan_documents: {e}")
        return jsonify({
            'success': False,
            'error': f'Error del servidor: {str(e)}'
        }), 500

@app.route('/admin')
def admin_panel():
    """Sirve el panel de administración"""
    return send_from_directory('.', 'admin_panel.html')
'''

    # 4. Panel de administración HTML
    admin_panel_content = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Panel de Administración - Documentos</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            color: #333;
        }
        .section {
            margin: 30px 0;
            padding: 20px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
        }
        .section h3 {
            margin-top: 0;
            color: #007bff;
        }
        .button {
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
            font-size: 14px;
        }
        .button:hover {
            background: #0056b3;
        }
        .button.danger {
            background: #dc3545;
        }
        .button.danger:hover {
            background: #c82333;
        }
        .button.success {
            background: #28a745;
        }
        .button.success:hover {
            background: #218838;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #007bff;
        }
        .stat-label {
            color: #666;
            font-size: 0.9em;
        }
        .log-area {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 15px;
            height: 300px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            white-space: pre-wrap;
        }
        .input-group {
            margin: 15px 0;
        }
        .input-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        .input-group input {
            width: 100%;
            padding: 8px;
            border: 1px solid #ccc;
            border-radius: 4px;
            font-size: 14px;
        }
        .loading {
            display: none;
            color: #007bff;
            font-style: italic;
        }
        .success {
            color: #28a745;
            font-weight: bold;
        }
        .error {
            color: #dc3545;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Panel de Administración</h1>
            <h2>Gestión de Documentos Weaviate</h2>
        </div>

        <!-- Estadísticas -->
        <div class="section">
            <h3>📊 Estadísticas Actuales</h3>
            <button class="button" onclick="loadStats()">Actualizar Estadísticas</button>
            <div id="stats-container">
                <div class="stats-grid" id="stats-grid">
                    <!-- Las estadísticas se cargarán aquí -->
                </div>
            </div>
        </div>

        <!-- Escanear Documentos -->
        <div class="section">
            <h3>🔍 Escanear Documentos</h3>
            <p>Analiza qué archivos han cambiado sin actualizar la base de datos.</p>
            <div class="input-group">
                <label for="scan-path">Ruta de documentos:</label>
                <input type="text" id="scan-path" value="C:\\Easysoft" placeholder="Ruta del directorio">
            </div>
            <button class="button" onclick="scanDocuments()">Escanear Cambios</button>
            <div class="loading" id="scan-loading">🔍 Escaneando...</div>
            <div id="scan-results"></div>
        </div>

        <!-- Actualizar Documentos -->
        <div class="section">
            <h3>🔄 Actualizar Documentos</h3>
            <p>Actualiza solo los documentos que han cambiado (recomendado).</p>
            <div class="input-group">
                <label for="update-path">Ruta de documentos:</label>
                <input type="text" id="update-path" value="C:\\Easysoft" placeholder="Ruta del directorio">
            </div>
            <button class="button success" onclick="updateDocuments(false)">Actualizar Cambios</button>
            <button class="button danger" onclick="updateDocuments(true)">Reconstruir Todo</button>
            <div class="loading" id="update-loading">⚙️ Procesando...</div>
            <div id="update-results"></div>
        </div>

        <!-- Log de Actividades -->
        <div class="section">
            <h3>📋 Log de Actividades</h3>
            <button class="button" onclick="clearLog()">Limpiar Log</button>
            <div id="activity-log" class="log-area">Esperando actividad...</div>
        </div>
    </div>

    <script>
        // Funciones JavaScript para el panel
        const API_BASE = window.location.origin;
        
        function log(message, type = 'info') {
            const logArea = document.getElementById('activity-log');
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = `[${timestamp}] ${message}\\n`;
            
            if (logArea.textContent === 'Esperando actividad...') {
                logArea.textContent = '';
            }
            
            logArea.textContent += logEntry;
            logArea.scrollTop = logArea.scrollHeight;
        }
        
        function clearLog() {
            document.getElementById('activity-log').textContent = 'Log limpiado...';
        }
        
        async function loadStats() {
            try {
                log('📊 Cargando estadísticas...');
                
                const response = await fetch(`${API_BASE}/admin/documents/stats`);
                const data = await response.json();
                
                if (data.success) {
                    displayStats(data.stats);
                    log('✅ Estadísticas cargadas exitosamente');
                } else {
                    log(`❌ Error cargando estadísticas: ${data.error}`, 'error');
                }
            } catch (error) {
                log(`❌ Error de conexión: ${error.message}`, 'error');
            }
        }
        
        function displayStats(stats) {
            const statsGrid = document.getElementById('stats-grid');
            statsGrid.innerHTML = `
                <div class="stat-card">
                    <div class="stat-number">${stats.total_documents_weaviate || 0}</div>
                    <div class="stat-label">Documentos en Weaviate</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${stats.total_documents_registry || 0}</div>
                    <div class="stat-label">Documentos en Registro</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${stats.vectorized_documents || 0}</div>
                    <div class="stat-label">Documentos Vectorizados</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${stats.documents_with_errors || 0}</div>
                    <div class="stat-label">Documentos con Errores</div>
                </div>
            `;
        }
        
        async function scanDocuments() {
            const path = document.getElementById('scan-path').value;
            const loadingEl = document.getElementById('scan-loading');
            const resultsEl = document.getElementById('scan-results');
            
            try {
                loadingEl.style.display = 'block';
                resultsEl.innerHTML = '';
                log(`🔍 Iniciando escaneo de: ${path}`);
                
                const response = await fetch(`${API_BASE}/admin/documents/scan`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ path: path })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    displayScanResults(data);
                    log(`✅ Escaneo completado. ${data.total_files_found} archivos encontrados`);
                } else {
                    log(`❌ Error en escaneo: ${data.error}`, 'error');
                    resultsEl.innerHTML = `<div class="error">Error: ${data.error}</div>`;
                }
            } catch (error) {
                log(`❌ Error de conexión: ${error.message}`, 'error');
                resultsEl.innerHTML = `<div class="error">Error de conexión: ${error.message}</div>`;
            } finally {
                loadingEl.style.display = 'none';
            }
        }
        
        function displayScanResults(data) {
            const resultsEl = document.getElementById('scan-results');
            const summary = data.summary;
            
            let html = '<h4>📊 Resumen de Cambios:</h4>';
            html += '<div class="stats-grid">';
            
            for (const [changeType, info] of Object.entries(summary)) {
                const emoji = {
                    'new': '🆕',
                    'modified': '🔄', 
                    'deleted': '🗑️',
                    'unchanged': '✅'
                }[changeType] || '📄';
                
                html += `
                    <div class="stat-card">
                        <div class="stat-number">${info.count}</div>
                        <div class="stat-label">${emoji} ${changeType}</div>
                    </div>
                `;
            }
            
            html += '</div>';
            
            // Mostrar algunos archivos de ejemplo
            for (const [changeType, info] of Object.entries(summary)) {
                if (info.count > 0) {
                    html += `<h5>${changeType.toUpperCase()} (${info.count}):</h5>`;
                    html += '<ul>';
                    info.files.forEach(file => {
                        html += `<li>${file}</li>`;
                    });
                    if (info.count > 10) {
                        html += `<li><em>... y ${info.count - 10} más</em></li>`;
                    }
                    html += '</ul>';
                }
            }
            
            resultsEl.innerHTML = html;
        }
        
        async function updateDocuments(forceRebuild = false) {
            const path = document.getElementById('update-path').value;
            const loadingEl = document.getElementById('update-loading');
            const resultsEl = document.getElementById('update-results');
            
            const action = forceRebuild ? 'Reconstrucción completa' : 'Actualización incremental';
            
            if (forceRebuild && !confirm('⚠️ ¿Estás seguro de que quieres reconstruir toda la base de datos? Esto eliminará todos los datos actuales.')) {
                return;
            }
            
            try {
                loadingEl.style.display = 'block';
                resultsEl.innerHTML = '';
                log(`⚙️ Iniciando ${action.toLowerCase()} de: ${path}`);
                
                const response = await fetch(`${API_BASE}/admin/documents/update`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        path: path,
                        force_rebuild: forceRebuild
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    displayUpdateResults(data.stats);
                    log(`✅ ${action} completada exitosamente`);
                    // Recargar estadísticas
                    loadStats();
                } else {
                    log(`❌ Error en ${action.toLowerCase()}: ${data.error}`, 'error');
                    resultsEl.innerHTML = `<div class="error">Error: ${data.error}</div>`;
                }
            } catch (error) {
                log(`❌ Error de conexión: ${error.message}`, 'error');
                resultsEl.innerHTML = `<div class="error">Error de conexión: ${error.message}</div>`;
            } finally {
                loadingEl.style.display = 'none';
            }
        }
        
        function displayUpdateResults(stats) {
            const resultsEl = document.getElementById('update-results');
            
            let html = '<h4>📈 Resultados de la Actualización:</h4>';
            html += '<div class="stats-grid">';
            
            const statLabels = {
                'new': '🆕 Nuevos',
                'modified': '🔄 Modificados',
                'deleted': '🗑️ Eliminados', 
                'unchanged': '✅ Sin cambios',
                'errors': '❌ Errores'
            };
            
            for (const [key, label] of Object.entries(statLabels)) {
                if (stats.hasOwnProperty(key)) {
                    html += `
                        <div class="stat-card">
                            <div class="stat-number">${stats[key]}</div>
                            <div class="stat-label">${label}</div>
                        </div>
                    `;
                }
            }
            
            html += '</div>';
            
            const totalChanges = (stats.new || 0) + (stats.modified || 0) + (stats.deleted || 0);
            
            if (totalChanges === 0) {
                html += '<div class="success">🎉 ¡Base de datos actualizada! No hay cambios nuevos.</div>';
            } else {
                html += `<div class="success">🎉 ¡Actualización completada! ${totalChanges} cambios procesados.</div>`;
            }
            
            if (stats.errors > 0) {
                html += '<div class="error">⚠️ Algunos archivos tuvieron errores. Revisa los logs del servidor.</div>';
            }
            
            resultsEl.innerHTML = html;
        }
        
        // Cargar estadísticas al inicio
        window.onload = function() {
            loadStats();
            log('🚀 Panel de administración iniciado');
        };
    </script>
</body>
</html>
'''

    # 5. Archivos batch para Windows
    update_bat_content = '''@echo off
echo 🚀 Actualizando documentos de EasySoft...
echo.

python update_documents.py

echo.
echo ✅ Proceso completado
pause
'''

    rebuild_bat_content = '''@echo off
echo ⚠️ RECONSTRUCCIÓN COMPLETA DE LA BASE DE DATOS
echo.
echo Esto eliminará todos los datos actuales y los recreará.
echo.
set /p confirm="¿Estás seguro? (S/N): "
if /i "%confirm%" NEQ "S" goto :cancel

echo.
echo 🔄 Reconstruyendo base de datos completa...
python weaviate_manager.py rebuild

echo.
echo ✅ Reconstrucción completada
goto :end

:cancel
echo ❌ Operación cancelada

:end
pause
'''

    stats_bat_content = '''@echo off
echo 📊 Estadísticas de la base de datos...
echo.

python weaviate_manager.py stats

echo.
pause
'''

    # 6. Requirements adicionales
    additional_requirements = '''# Agregar estas dependencias a requirements.txt

beautifulsoup4==4.12.2
lxml==4.9.3
argparse==1.4.0
'''

    # 7. README para el sistema de documentos
    readme_content = '''# Sistema de Gestión de Documentos Weaviate

## 🚀 Descripción
Sistema inteligente para gestionar y actualizar documentos en Weaviate de forma incremental.

## 📁 Archivos Generados

### Scripts Principales:
- `weaviate_manager.py` - Sistema completo con todas las funciones
- `update_documents.py` - Script simple para actualizaciones diarias
- `admin_panel.html` - Panel web de administración

### Archivos Windows:
- `actualizar_documentos.bat` - Actualización rápida (doble clic)
- `reconstruir_base_datos.bat` - Reconstrucción completa
- `ver_estadisticas.bat` - Ver estadísticas

### API:
- `api_endpoints_add_to_app.py` - Endpoints para agregar a app.py

## 🛠️ Instalación

1. **Instalar dependencias adicionales:**
```bash
pip install beautifulsoup4 lxml
```

2. **Agregar endpoints a app.py:**
   - Copia el contenido de `api_endpoints_add_to_app.py` a tu `app.py`

3. **Configurar rutas:**
   - Edita la variable `DEFAULT_PATH` en `update_documents.py`
   - Cambia `C:\\Easysoft` por tu ruta de documentos

## 📊 Uso Diario

### Actualización Simple:
```bash
python update_documents.py
```

### Gestión Completa:
```bash
# Ver qué ha cambiado
python weaviate_manager.py scan

# Actualizar solo cambios
python weaviate_manager.py update

# Ver estadísticas
python weaviate_manager.py stats

# Reconstruir todo (emergencia)
python weaviate_manager.py rebuild
```

### Panel Web:
1. Asegurar que tu Flask app esté corriendo
2. Abrir `http://localhost:5000/admin` en el navegador
3. Usar la interfaz gráfica

## 🔥 Características

### ✅ Detección Inteligente:
- Solo procesa archivos nuevos o modificados
- Usa hash MD5 para detectar cambios
- Elimina documentos borrados

### ✅ Seguimiento Completo:
- Archivo `document_metadata.json` con historial
- Estadísticas detalladas
- Logs de errores

### ✅ Múltiples Interfaces:
- Línea de comandos
- Panel web
- Archivos batch para Windows

### ✅ Robusto:
- Manejo de errores
- Reintentos automáticos
- Continuación tras fallos

## 📈 Ventajas vs Script Original

| Función | Antes | Ahora |
|---------|-------|-------|
| Velocidad | 🐌 Lenta (todo) | ⚡ Rápida (solo cambios) |
| Detección | ❌ No detecta cambios | ✅ Detección inteligente |
| Errores | ❌ Se detiene | ✅ Continúa y reporta |
| Interface | ❌ Solo terminal | ✅ Terminal + Web |
| Seguimiento | ❌ No hay historial | ✅ Metadatos completos |

## 🚨 Importante

- Siempre usa `update` para uso diario
- Solo usa `rebuild` en emergencias
- El archivo `document_metadata.json` es crítico, no lo borres
- Haz backup de Weaviate antes de `rebuild`

## 📞 Troubleshooting

### Error de conexión a Weaviate:
```bash
# Verificar que Docker esté corriendo
docker-compose ps

# Reiniciar Weaviate si es necesario
docker-compose restart weaviate
```

### Error de OpenAI API:
- Verificar API key en `.env`
- Revisar cuota y límites

### Metadatos corruptos:
```bash
# Respaldar metadatos
cp document_metadata.json document_metadata.json.backup

# Recrear metadatos
python weaviate_manager.py scan
```
'''

    # Crear todos los archivos
    files_to_create = [
        ('weaviate_manager.py', weaviate_manager_content, 'Sistema principal de gestión'),
        ('update_documents.py', update_documents_content, 'Script simple de actualización'),
        ('api_endpoints_add_to_app.py', api_endpoints_content, 'Endpoints para agregar a app.py'),
        ('admin_panel.html', admin_panel_content, 'Panel web de administración'),
        ('actualizar_documentos.bat', update_bat_content, 'Batch de actualización Windows'),
        ('reconstruir_base_datos.bat', rebuild_bat_content, 'Batch de reconstrucción Windows'),
        ('ver_estadisticas.bat', stats_bat_content, 'Batch de estadísticas Windows'),
        ('requirements_additional.txt', additional_requirements, 'Dependencias adicionales'),
        ('README_DocumentManagement.md', readme_content, 'Documentación del sistema')
    ]
    
    print(f"\n📝 Creando {len(files_to_create)} archivos del sistema...")
    
    for filepath, content, description in files_to_create:
        create_file(filepath, content, description)
    
    print("\n" + "="*60)
    print("🎉 ¡Sistema de Gestión de Documentos generado exitosamente!")
    print("\n📚 Próximos pasos:")
    print("1. Instalar dependencias: pip install beautifulsoup4 lxml")
    print("2. Editar rutas en update_documents.py (cambiar C:\\Easysoft)")
    print("3. Copiar endpoints de api_endpoints_add_to_app.py a tu app.py")
    print("4. Probar: python weaviate_manager.py stats")
    print("5. Primera actualización: python update_documents.py")
    print("\n🌐 Panel web: http://localhost:5000/admin")
    print("📖 Documentación completa: README_DocumentManagement.md")
    print("\n🚀 ¡Listo para usar!")

if __name__ == "__main__":
    main()