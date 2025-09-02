import os
from openai import OpenAI
from bs4 import BeautifulSoup
import weaviate
from weaviate.classes.config import Configure, Property, DataType
from weaviate.connect import ConnectionParams
from weaviate.util import generate_uuid5
import weaviate.classes as wvc
import mimetypes
#import docx  # Para archivos .docx

# Configurar cliente de OpenAI
# ¡ADVERTENCIA DE SEGURIDAD!: No es recomendable mantener la API Key directamente en el código fuente.
# Considera usar variables de entorno para almacenar tu API Key de forma segura.
openai_client = OpenAI(api_key="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")

# Configurar parámetros de conexión para Weaviate
parametros_conexion = ConnectionParams.from_url(
    url="http://localhost:8080",
    grpc_port=50051
)

# Crear el cliente de Weaviate
cliente = weaviate.WeaviateClient(
    connection_params=parametros_conexion,
    additional_config=wvc.init.AdditionalConfig(
        timeout=wvc.init.Timeout(init=30, query=60, insert=120)
    ),
    skip_init_checks=True
)

# Conectar al cliente
try:
    cliente.connect()
    print("Conexión a Weaviate exitosa")
except Exception as e:
    print(f"Error al conectar con Weaviate: {e}")
    cliente.close()
    exit(1)

# **NUEVO: Eliminar y recrear la clase para asegurar una limpieza completa**
# Esto es más robusto que intentar vaciar la colección con filtros.
if cliente.collections.exists("Documento"):
    print("La clase 'Documento' ya existe. Procediendo a eliminarla para recrearla y asegurar una limpieza completa...")
    try:
        cliente.collections.delete("Documento")
        print("Clase 'Documento' eliminada exitosamente.")
    except Exception as e:
        print(f"Error al eliminar la clase 'Documento': {e}")
        # Si no se puede eliminar, el script no podrá continuar limpiamente
        cliente.close()
        exit(1)

# Crear la clase Documento (ahora sabemos que no existe o fue eliminada)
try:
    cliente.collections.create(
        name="Documento",
        properties=[
            Property(name="contenido", data_type=DataType.TEXT),
            Property(name="nombre_archivo", data_type=DataType.TEXT),
            Property(name="ruta_archivo", data_type=DataType.TEXT),
            Property(name="tipo_archivo", data_type=DataType.TEXT),
        ],
        vectorizer_config=Configure.Vectorizer.none()
    )
    print("Clase 'Documento' creada exitosamente")
except Exception as e:
    print(f"Error al crear la clase 'Documento': {e}")
    cliente.close()
    exit(1)


# Lista de extensiones a ignorar
EXTENSIONES_IGNORADAS = {".gz", ".skn", ".ppf", ".ejs", ".docx"} # .py se maneja en ARCHIVOS_IGNORADOS

# Lista de nombres de archivos a ignorar (scripts de Python y similares)
ARCHIVOS_IGNORADOS = {
    "vectorizatodos.py",
    "viewaddupdate.html",
    "fiscalyearaddupdate.html",
    "accountaddupdate.html",
    "accountingentryaddupdate.html",
    "indexandquotesaddupdate.html",
    "app.py",
    "vectorizatodos_borraycarga.py", # Añadir este script a la lista de ignorados
    "vectorizatodos_borraycargaOLD.py", # Si ese archivo existe y quieres ignorarlo
    "consultabasica.py" # Si este archivo debe ser ignorado
}

# Función para estimar tokens y truncar texto
def truncar_texto(texto, max_tokens=8000):
    # Aproximación: 1 token ≈ 4 caracteres
    max_caracteres = max_tokens * 4
    if len(texto) > max_caracteres:
        print(f"Texto truncado: {len(texto)} caracteres reducidos a {max_caracteres}")
        return texto[:max_caracteres]
    return texto

# Función para extraer texto según el tipo de archivo
def extraer_texto(ruta_archivo):
    try:
        extension = os.path.splitext(ruta_archivo)[1].lower()
        if extension in EXTENSIONES_IGNORADAS:
            return None  # Ignorar archivos con estas extensiones
        
        # **CORREGIDO: Incluir .htm junto a .html**
        if extension in (".html", ".htm", ".css", ".js", ".txt", ".py"):
            with open(ruta_archivo, "r", encoding="utf-8", errors='ignore') as archivo:
                if extension in (".html", ".htm"): # Ambos se procesan como HTML
                    sopa = BeautifulSoup(archivo, "html.parser")
                    return sopa.get_text()
                return archivo.read()
        elif extension == ".xml":
            with open(ruta_archivo, "r", encoding="utf-8", errors='ignore') as archivo:
                sopa = BeautifulSoup(archivo, "lxml")
                return sopa.get_text()
        #elif extension == ".docx":
        #    doc = docx.Document(ruta_archivo)
        #    return "\n".join([parrafo.text for parrafo in doc.paragraphs])
        elif extension in (".jpg", ".png", ".mp4", ".svg", ".gif"):
            return ""  # Archivos no textuales, devolvemos vacío
        else:
            print(f"Tipo de archivo no soportado para extracción de texto: {ruta_archivo}")
            return ""
    except Exception as e:
        print(f"Error al extraer texto de {ruta_archivo}: {e}")
        return ""

# Función para obtener embeddings de OpenAI
def obtener_embeddings(texto):
    if not texto or texto.strip() == "Archivo no textual" or texto.strip() == "Archivo sin contenido extraíble":
        return None
    try:
        texto_a_embeddar = truncar_texto(texto)
        respuesta = openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=texto_a_embeddar
        )
        return respuesta.data[0].embedding
    except Exception as e:
        print(f"Error al obtener embeddings para un texto de {len(texto)} caracteres: {e}")
        return None

# Función para cargar los documentos a Weaviate
def cargar_a_weaviate(ruta_archivo):
    try:
        nombre_archivo = os.path.basename(ruta_archivo)
        if nombre_archivo in ARCHIVOS_IGNORADOS:
            print(f"Archivo ignorado (en lista de ignorados): {ruta_archivo}")
            return
        
        if not os.path.splitext(ruta_archivo)[1]:
            print(f"Archivo sin extensión ignorado: {ruta_archivo}")
            return
        
        texto = extraer_texto(ruta_archivo)
        if texto is None:
            print(f"Archivo ignorado por extensión: {ruta_archivo}")
            return
        
        tipo_archivo = mimetypes.guess_type(ruta_archivo)[0] or "desconocido"
        
        if texto == "" and tipo_archivo != "desconocido" and not nombre_archivo.endswith((".htm", ".html")):
            # Si el archivo es no textual y se extrajo como cadena vacía, no intentar obtener embedding
            # Y no es un .htm o .html que debería tener contenido
            vector = None
            contenido_a_guardar = "Archivo no textual o sin contenido extraíble"
        else:
            vector = obtener_embeddings(texto)
            contenido_a_guardar = texto if texto else "Archivo sin contenido extraíble"
        
        coleccion = cliente.collections.get("Documento")
        propiedades = {
            "contenido": contenido_a_guardar,
            "nombre_archivo": nombre_archivo,
            "ruta_archivo": ruta_archivo,
            "tipo_archivo": tipo_archivo
        }
        
        if vector is not None:
            coleccion.data.insert(
                properties=propiedades,
                vector=vector,
                uuid=generate_uuid5(ruta_archivo)
            )
            print(f"Documento {nombre_archivo} cargado exitosamente con embedding")
        else:
            coleccion.data.insert(
                properties=propiedades,
                uuid=generate_uuid5(ruta_archivo)
            )
            print(f"Documento {nombre_archivo} cargado exitosamente (sin embedding)")
    except Exception as e:
        print(f"Error al cargar {ruta_archivo} a Weaviate: {e}. Asegúrate de que el ID no exista si la limpieza falló.")

# Ruta de la carpeta principal
carpeta_raiz = r"C:\Easysoft"

# Subir todos los archivos recursivamente
try:
    if os.path.exists(carpeta_raiz):
        for raiz, directorios, archivos in os.walk(carpeta_raiz):
            for nombre_archivo in archivos:
                ruta_archivo = os.path.join(raiz, nombre_archivo)
                cargar_a_weaviate(ruta_archivo)
    else:
        print(f"La carpeta {carpeta_raiz} no existe. Verifica la ruta.")
finally:
    cliente.close()
    print("Conexión a Weaviate cerrada")