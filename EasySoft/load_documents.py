# load_documents.py
from weaviate_manager import WeaviateManager
import os

def load_documents():
    # Ruta de documentos
    document_path = "C:\\Local\\EasySoft"
    
    # Verificar que la ruta exista
    if not os.path.exists(document_path):
        print(f"❌ La ruta {document_path} no existe")
        return
    
    print(f"🔍 Escaneando documentos en: {document_path}")
    
    # Inicializar el manager
    manager = WeaviateManager()
    
    try:
        # Escanear directorio
        found_files = manager.scan_directory(document_path)
        print(f"📄 Encontrados {len(found_files)} archivos")
        
        # Actualizar documentos
        print("🔄 Actualizando documentos en Weaviate...")
        stats = manager.update_documents(document_path)
        
        print("\n📊 Resultados:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Verificar estadísticas finales
        print("\n📈 Estadísticas finales:")
        final_stats = manager.get_statistics()
        for key, value in final_stats.items():
            print(f"  {key}: {value}")
            
    finally:
        manager.cleanup()

if __name__ == "__main__":
    load_documents()