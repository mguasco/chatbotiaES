# check_weaviate_fixed.py
from config import Config
import weaviate
import json

def check_weaviate():
    print("Conectando a Weaviate...")
    
    try:
        # Intentar conexión
        if Config.WEAVIATE_HTTP_SECURE:
            client = weaviate.connect_to_custom(
                http_host=Config.WEAVIATE_HOST,
                http_port=Config.WEAVIATE_HTTP_PORT,
                http_secure=Config.WEAVIATE_HTTP_SECURE,
                grpc_host=Config.WEAVIATE_HOST,
                grpc_port=Config.WEAVIATE_GRPC_PORT,
                grpc_secure=Config.WEAVIATE_GRPC_SECURE
            )
        else:
            client = weaviate.connect_to_local(
                host=Config.WEAVIATE_HOST,
                port=Config.WEAVIATE_HTTP_PORT,
                grpc_port=Config.WEAVIATE_GRPC_PORT
            )
        
        if not client.is_ready():
            print("❌ Weaviate no está listo")
            return
            
        print("✅ Conexión a Weaviate exitosa")
        
        # Verificar colecciones existentes
        collection_names = client.collections.list_all().keys()
        print(f"Colecciones disponibles: {list(collection_names)}")
        
        # Verificar si existe la colección Documento
        if "Documento" not in collection_names:
            print("❌ La colección 'Documento' no existe")
            return
            
        # Obtener información de la colección
        collection = client.collections.get("Documento")
        count_result = collection.aggregate.over_all(total_count=True)
        
        print(f"Total de documentos en Weaviate: {count_result.total_count}")
        
        # Verificar schema (forma alternativa de obtener propiedades)
        try:
            schema = client.schema.get("Documento")
            if schema:
                print("\nEsquema de la colección:")
                properties = schema.get('properties', [])
                for prop in properties:
                    print(f"  - {prop.get('name')} ({prop.get('dataType')})")
        except Exception as e:
            print(f"⚠️ No se pudo obtener el esquema: {e}")
        
        # Verificar si hay documentos
        if count_result.total_count > 0:
            # Obtener algunos documentos de ejemplo
            objects = collection.query.fetch_objects(limit=3)
            print(f"\nEjemplos de documentos ({len(objects.objects)}):")
            
            for i, obj in enumerate(objects.objects, 1):
                print(f"\nDocumento #{i}:")
                print(f"  UUID: {obj.uuid}")
                print(f"  Nombre: {obj.properties.get('nombre_archivo', 'N/A')}")
                print(f"  Ruta: {obj.properties.get('ruta_archivo', 'N/A')}")
                print(f"  Fecha: {obj.properties.get('fecha_modificacion', 'N/A')}")
        
        # Verificar archivo de metadatos
        try:
            with open("document_metadata.json", "r") as f:
                metadata = json.load(f)
                print(f"\nArchivo de metadatos contiene {len(metadata)} registros")
        except Exception as e:
            print(f"❌ Error leyendo archivo de metadatos: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'client' in locals():
            client.close()
            print("Conexión cerrada")

if __name__ == "__main__":
    check_weaviate()