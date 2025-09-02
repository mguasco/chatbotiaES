# init_weaviate.py - Inicialización automática de Weaviate
import time
import os
import sys
from weaviate_manager import WeaviateManager

def wait_for_weaviate(max_attempts=30, delay=2):
    """Espera a que Weaviate esté disponible"""
    print("? Esperando que Weaviate esté disponible...")
    
    for attempt in range(max_attempts):
        try:
            manager = WeaviateManager()
            if manager.weaviate_client and manager.weaviate_client.is_ready():
                print("? Weaviate está listo")
                manager.cleanup()
                return True
        except Exception as e:
            print(f"Intento {attempt + 1}/{max_attempts}: {e}")
            time.sleep(delay)
    
    print("? Weaviate no está disponible después de esperar")
    return False

def initialize_database():
    """Inicializa la base de datos si está vacía"""
    print("?? Inicializando base de datos de Weaviate...")
    
    try:
        manager = WeaviateManager()
        
        # Verificar si la colección existe
        if not manager.weaviate_client.collections.exists("Documento"):
            print("?? Colección 'Documento' no existe, creando...")
            if not manager._ensure_collection_exists():
                print("? Error creando colección")
                return False
        
        # Verificar si hay documentos
        collection = manager.weaviate_client.collections.get("Documento")
        count_result = collection.aggregate.over_all(total_count=True)
        
        print(f"?? Documentos actuales: {count_result.total_count}")
        
        # Si no hay documentos, cargar desde el directorio
        if count_result.total_count == 0:
            # Buscar directorio de documentos
            possible_paths = [
                "/app",  # Docker
                "/app/EasySoft",
                "C:\\Local\\EasySoft",  # Windows (por si acaso)
                "./",  # Directorio actual
            ]
            
            document_path = None
            for path in possible_paths:
                if os.path.exists(path) and os.path.isdir(path):
                    # Verificar que tenga archivos de documentación
                    files = []
                    for root, dirs, filenames in os.walk(path):
                        for filename in filenames:
                            if filename.endswith(('.html', '.htm', '.txt', '.py', '.js', '.css')):
                                files.append(filename)
                                break
                        if files:
                            break
                    
                    if files:
                        document_path = path
                        break
            
            if document_path:
                print(f"?? Cargando documentos desde: {document_path}")
                
                # Validar codificación antes de cargar
                print("?? Validando codificación de archivos...")
                try:
                    from validate_encoding import EncodingValidator
                    validator = EncodingValidator()
                    encoding_stats = validator.fix_encoding_issues(document_path, auto_convert=True)
                    
                    if encoding_stats['converted'] > 0:
                        print(f"? Convertidos {encoding_stats['converted']} archivos a UTF-8")
                    if encoding_stats['errors'] > 0:
                        print(f"?? {encoding_stats['errors']} archivos con errores de conversión")
                        
                except ImportError:
                    print("?? Validador de codificación no disponible, continuando...")
                except Exception as e:
                    print(f"?? Error validando codificación: {e}")
                
                # Cargar documentos
                stats = manager.update_documents(document_path)
                
                print("?? Resultados de la carga inicial:")
                for key, value in stats.items():
                    print(f"   {key}: {value}")
                    
                if stats.get("new", 0) > 0:
                    print("? Base de datos inicializada correctamente")
                else:
                    print("?? No se cargaron documentos nuevos")
            else:
                print("?? No se encontró directorio de documentos")
        else:
            print("? Base de datos ya contiene documentos")
        
        manager.cleanup()
        return True
        
    except Exception as e:
        print(f"? Error inicializando base de datos: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("?? Inicializador de Weaviate para Docker")
    print("=" * 50)
    
    # Paso 1: Esperar a que Weaviate esté disponible
    if not wait_for_weaviate():
        sys.exit(1)
    
    # Paso 2: Inicializar base de datos
    if not initialize_database():
        sys.exit(1)
    
    print("?? Inicialización completada exitosamente")

if __name__ == "__main__":
    main()