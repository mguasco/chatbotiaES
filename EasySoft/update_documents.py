# update_documents.py - Script con chunking inteligente y logging
import sys
import os
from datetime import datetime
from weaviate_manager import WeaviateManager

def print_banner():
    """Imprime banner de inicio"""
    print("="*70)
    print("🤖 SISTEMA DE VECTORIZACIÓN EASYSOFT - CON CHUNKING INTELIGENTE")
    print("="*70)
    print(f"⏰ Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

def print_help():
    """Imprime ayuda de uso"""
    print("💡 USO:")
    print("   python update_documents.py [opciones]")
    print()
    print("🔧 OPCIONES:")
    print("   --reset     : Limpia completamente la base de datos antes de procesar")
    print("   --rebuild   : Reconstruye toda la base de datos desde cero")
    print("   --stats     : Solo muestra estadísticas actuales")
    print("   --report    : Solo genera reporte detallado")
    print("   --help      : Muestra esta ayuda")
    print()
    print("📂 RUTA POR DEFECTO: /home/chatbotia_BAS/EasySoft")
    print("   Para cambiar: python update_documents.py /tu/ruta/personalizada")
    print()

def main():
    """Script principal con chunking inteligente"""
    
    # Configuración
    DEFAULT_PATH = "/home/chatbotia_BAS/EasySoft"
    
    # Procesar argumentos
    args = sys.argv[1:]
    document_path = DEFAULT_PATH
    options = []
    
    for arg in args:
        if arg.startswith('--'):
            options.append(arg)
        elif not arg.startswith('-') and os.path.exists(arg):
            document_path = arg
    
    # Manejar opciones especiales
    if '--help' in options:
        print_banner()
        print_help()
        return 0
    
    print_banner()
    
    if not os.path.exists(document_path):
        print(f"❌ Error: La ruta {document_path} no existe")
        print_help()
        return 1
    
    print(f"📂 Ruta de documentos: {document_path}")
    print(f"🔧 Opciones: {', '.join(options) if options else 'Actualización estándar'}")
    print("-" * 70)
    
    try:
        manager = WeaviateManager()
        
        # Solo estadísticas
        if '--stats' in options:
            print("📊 Obteniendo estadísticas actuales...")
            stats = manager.get_statistics()
            
            print("\n📈 ESTADÍSTICAS ACTUALES:")
            print("="*50)
            for key, value in stats.items():
                formatted_key = key.replace('_', ' ').title()
                print(f"   {formatted_key}: {value:,}" if isinstance(value, int) else f"   {formatted_key}: {value}")
            
            return 0
        
        # Solo reporte
        if '--report' in options:
            print("📊 Generando reporte detallado...")
            report_file = manager.generate_vectorization_report()
            if report_file:
                print(f"✅ Reporte generado: {report_file}")
                return 0
            else:
                print("❌ Error generando reporte")
                return 1
        
        # Reset de base de datos
        if '--reset' in options:
            print("🗑️ RESET: Limpiando base de datos completamente...")
            if input("⚠️  ¿Estás seguro? Esto eliminará TODOS los datos (s/N): ").lower() == 's':
                manager.reset_database()
                print("✅ Base de datos reseteada")
            else:
                print("❌ Operación cancelada")
                return 0
        
        # Procesamiento principal
        print("🚀 Iniciando procesamiento con chunking inteligente...")
        
        force_rebuild = '--rebuild' in options
        if force_rebuild:
            print("🔄 Modo REBUILD: Reconstruyendo toda la base de datos...")
            if input("⚠️  Esto recreará toda la base de datos. ¿Continuar? (s/N): ").lower() != 's':
                print("❌ Operación cancelada")
                return 0
        
        # Ejecutar actualización
        stats = manager.update_documents(document_path, force_rebuild=force_rebuild)
        
        if "error" in stats:
            print("\n❌ ERROR DURANTE EL PROCESAMIENTO")
            print("💡 Soluciones:")
            print("   1. Verifica que Weaviate esté corriendo: docker ps | grep weaviate")
            print("   2. Si hay duplicados: python update_documents.py --reset")
            print("   3. Revisa los logs generados")
            return 1
        
        # Mostrar resultados
        print("\n" + "="*70)
        print("📈 RESULTADOS DEL PROCESAMIENTO")
        print("="*70)
        print(f"🆕 Documentos nuevos:       {stats.get('new', 0):,}")
        print(f"🔄 Documentos modificados:  {stats.get('modified', 0):,}")
        print(f"🗑️ Documentos eliminados:   {stats.get('deleted', 0):,}")
        print(f"✅ Sin cambios:            {stats.get('unchanged', 0):,}")
        print(f"❌ Errores:                {stats.get('errors', 0):,}")
        print()
        print("🧩 CHUNKING INTELIGENTE:")
        print(f"📄 Archivos con chunks:    {stats.get('chunked_files', 0):,}")
        print(f"🔢 Total chunks creados:   {stats.get('total_chunks', 0):,}")
        print(f"🎯 Documentos vectorizados: {stats.get('vectorized_documents', 0):,}")
        
        total_changes = stats.get('new', 0) + stats.get('modified', 0) + stats.get('deleted', 0)
        
        print("\n" + "="*70)
        if total_changes == 0:
            print("🎉 ¡BASE DE DATOS ACTUALIZADA! No hay cambios nuevos.")
        else:
            print(f"🎉 ¡PROCESAMIENTO COMPLETADO! {total_changes:,} cambios procesados.")
        
        if stats.get('errors', 0) > 0:
            print(f"\n⚠️  {stats.get('errors')} archivos tuvieron errores.")
            print("   📋 Revisa el archivo de log para más detalles")
        
        if stats.get('chunked_files', 0) > 0:
            print(f"\n📄 {stats.get('chunked_files')} archivos grandes fueron divididos en chunks")
            print(f"   🔢 Total de {stats.get('total_chunks')} chunks creados para mejor búsqueda")
        
        # Generar reporte automáticamente
        print("\n📊 Generando reporte detallado...")
        report_file = manager.generate_vectorization_report()
        if report_file:
            print(f"✅ Reporte completo generado: {report_file}")
        
        # Consejos finales
        print("\n💡 PRÓXIMOS PASOS:")
        print("   1. Revisa el archivo de log para detalles técnicos")
        print("   2. Revisa el reporte generado para análisis completo")
        print("   3. Prueba el chatbot para verificar que funciona correctamente")
        
        # Estadísticas finales
        final_stats = manager.get_statistics()
        print(f"\n📊 ESTADO FINAL:")
        print(f"   Total documentos en Weaviate: {final_stats.get('total_documents_weaviate', 0):,}")
        print(f"   Documentos vectorizados: {final_stats.get('vectorized_documents', 0):,}")
        
    except KeyboardInterrupt:
        print("\n⏹️ Procesamiento interrumpido por el usuario")
        return 1
        
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        print("\n🔧 DIAGNÓSTICO:")
        print("   1. ¿Está Weaviate corriendo?")
        print("      docker ps | grep weaviate")
        print("   2. ¿Es correcto el API key de OpenAI?")
        print("      Revisa el archivo .env")
        print("   3. ¿Hay permisos de escritura?")
        print("      ls -la document_metadata.json")
        print("\n💡 Si persisten los errores:")
        print("   python update_documents.py --reset")
        return 1
    finally:
        try:
            manager.cleanup()
        except:
            pass
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    
    print(f"\n⏰ Finalizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Pausa en Windows
    if sys.platform.startswith('win'):
        input("\nPresiona Enter para continuar...")
    
    sys.exit(exit_code)