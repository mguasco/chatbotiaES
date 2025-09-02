#!/usr/bin/env python3
# create_documento_class.py - Crear clase Documento en Weaviate
import weaviate
from config import Config

def create_documento_class():
    # Conectar a Weaviate
    client = weaviate.Client(url=f"http://{Config.WEAVIATE_HOST}:{Config.WEAVIATE_HTTP_PORT}")
    
    if not client.is_ready():
        print("ERROR: Weaviate no esta listo")
        return False
    
    # Verificar si ya existe
    schema = client.schema.get()
    classes = [cls['class'] for cls in schema.get('classes', [])]
    
    if "Documento" in classes:
        print("OK: Clase 'Documento' ya existe")
        return True
    
    # Crear la clase
    class_schema = {
        "class": "Documento",
        "properties": [
            {"name": "contenido", "dataType": ["text"]},
            {"name": "nombre_archivo", "dataType": ["string"]},
            {"name": "ruta_archivo", "dataType": ["string"]},
            {"name": "tipo_archivo", "dataType": ["string"]},
            {"name": "hash_archivo", "dataType": ["string"]},
            {"name": "fecha_modificacion", "dataType": ["date"]},
            {"name": "tamano_archivo", "dataType": ["int"]}
        ],
        "vectorizer": "none"
    }
    
    try:
        client.schema.create_class(class_schema)
        print("OK: Clase 'Documento' creada exitosamente")
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    create_documento_class()