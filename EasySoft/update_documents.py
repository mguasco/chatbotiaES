# update_documents.py - Script simple para actualizar documentos
import sys
import os
from weaviate_manager import WeaviateManager

def main():
    """Script simple para actualizar documentos"""
    
    # Configuración por defecto
    DEFAULT_PATH = "C:\\Local\\Easysoft"  # Cambia esto por tu ruta
    
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
        print("\n" + "="*50)
        print("📈 RESULTADOS DE LA ACTUALIZACIÓN")
        print("="*50)
        print(f"🆕 Documentos nuevos:     {stats.get('new', 0)}")
        print(f"🔄 Documentos modificados: {stats.get('modified', 0)}")
        print(f"🗑️ Documentos eliminados:  {stats.get('deleted', 0)}")
        print(f"✅ Sin cambios:          {stats.get('unchanged', 0)}")
        print(f"❌ Errores:              {stats.get('errors', 0)}")
        
        total_changes = stats.get('new', 0) + stats.get('modified', 0) + stats.get('deleted', 0)
        
        if total_changes == 0:
            print("\n🎉 ¡Base de datos actualizada! No hay cambios nuevos.")
        else:
            print(f"\n🎉 ¡Actualización completada! {total_changes} cambios procesados.")
        
        if stats.get('errors', 0) > 0:
            print("\n⚠️ Algunos archivos tuvieron errores. Revisa los logs arriba.")
            
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        return 1
    finally:
        manager.cleanup()
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    
    # Pausa para que puedas ver los resultados
    if sys.platform.startswith('win'):
        input("\nPresiona Enter para continuar...")
    
    sys.exit(exit_code)
