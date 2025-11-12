# -*- coding: utf-8 -*-
# app.py - Version corregida con subpath
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import logging
import threading
from config import Config
from services.chatbot_service import ChatbotService
from services.weaviate_service import WeaviateService

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configurar Flask con subpath
BASE_DIR = os.path.abspath(os.getcwd())
app = Flask(__name__, static_url_path='/chatbotia/static')

# ? CONFIGURACIÓN CORS MEJORADA PARA GITHUB PAGES
CORS(app, 
     resources={
         r"/chatbotia/*": {
             "origins": [
                 "https://bas-ar.github.io",      # Tu GitHub Pages
                 "http://localhost:*",             # Desarrollo local
                 "http://127.0.0.1:*",            # Desarrollo local
                 "https://intranetqa.bas.com.ar", # Tu servidor
                 "*"                               # Fallback para desarrollo
             ],
             "methods": ["GET", "POST", "OPTIONS"],
             "allow_headers": ["Content-Type", "X-Session-ID", "Authorization", "Accept", "Origin"]
         },
         r"/chat": {
             "origins": [
                 "https://bas-ar.github.io",
                 "http://localhost:*",
                 "http://127.0.0.1:*", 
                 "https://intranetqa.bas.com.ar",
                 "*"
             ],
             "methods": ["GET", "POST", "OPTIONS"],
             "allow_headers": ["Content-Type", "X-Session-ID", "Authorization", "Accept", "Origin"]
         },
         r"/clear_chat_history": {
             "origins": [
                 "https://bas-ar.github.io",
                 "http://localhost:*",
                 "http://127.0.0.1:*",
                 "https://intranetqa.bas.com.ar",
                 "*"
             ],
             "methods": ["GET", "POST", "OPTIONS"],
             "allow_headers": ["Content-Type", "X-Session-ID", "Authorization", "Accept", "Origin"]
         }
     })

# ? MIDDLEWARE ADICIONAL PARA ASEGURAR CORS
@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    allowed_origins = [
        'https://bas-ar.github.io',
        'http://localhost:3000',
        'http://localhost:5000',
        'http://127.0.0.1:5000',
        'https://intranetqa.bas.com.ar'
    ]
    
    if origin in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Session-ID, Authorization, Accept, Origin'
        response.headers['Access-Control-Allow-Credentials'] = 'false'
    
    return response

# ? MANEJO EXPLÍCITO DE OPTIONS REQUESTS
@app.route('/chat', methods=['OPTIONS'])
@app.route('/clear_chat_history', methods=['OPTIONS'])
@app.route('/chatbotia/chat', methods=['OPTIONS'])
@app.route('/chatbotia/clear_chat_history', methods=['OPTIONS'])
def handle_options():
    response = jsonify({'status': 'ok'})
    origin = request.headers.get('Origin')
    if origin in ['https://bas-ar.github.io', 'http://localhost:3000', 'https://intranetqa.bas.com.ar']:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-Session-ID, Authorization'
    return response

# Inicializar servicios
weaviate_service = WeaviateService()
chatbot_service = ChatbotService(weaviate_service)
chat_history_lock = threading.Lock()

@app.route('/chatbotia/')
@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.htm')

@app.route('/favicon.ico')
def favicon():
    """Maneja solicitudes de favicon"""
    return send_from_directory(BASE_DIR, 'Favicon-EasySoft.svg', mimetype='image/svg+xml')

# También agregar una ruta de bienvenida
@app.route('/api/info')
def api_info():
    """Informacion de la API"""
    return jsonify({
        "name": "Chatbot EasySoft",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "chat": "/chatbotia/chat",
            "health": "/chatbotia/health",
            "admin": "/chatbotia/admin"
        }
    })

@app.route('/config.js')
def serve_config():
    """Genera un archivo de configuracion JavaScript dinamico"""
    config_js = f"""
window.CHATBOT_CONFIG = {{
    SERVER_URL: '{Config.BASE_URL}',
    API_VERSION: 'v1',
    SUBPATH: '/chatbotia'
}};
"""
    return config_js, 200, {'Content-Type': 'application/javascript'}

# Rutas para archivos estaticos con subpath
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    assets_path = os.path.join(BASE_DIR, 'assets')
    file_path = os.path.join(assets_path, filename)
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        directory = os.path.dirname(file_path)
        filename_only = os.path.basename(file_path)
        return send_from_directory(directory, filename_only)
    else:
        return f"Archivo no encontrado: assets/{filename}", 404

@app.route('/template/<path:filename>')
def serve_template(filename):
    template_path = os.path.join(BASE_DIR, 'template')
    file_path = os.path.join(template_path, filename)
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        directory = os.path.dirname(file_path)
        filename_only = os.path.basename(file_path)
        return send_from_directory(directory, filename_only)
    else:
        return f"Archivo no encontrado: template/{filename}", 404

@app.route('/whxdata/<path:filename>')
def serve_whxdata(filename):
    whxdata_path = os.path.join(BASE_DIR, 'whxdata')
    file_path = os.path.join(whxdata_path, filename)
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        directory = os.path.dirname(file_path)
        filename_only = os.path.basename(file_path)
        return send_from_directory(directory, filename_only)
    else:
        return f"Archivo no encontrado: whxdata/{filename}", 404

@app.route('/<path:filename>')
def serve_static_files(filename):
    try:
        full_path = os.path.join(BASE_DIR, filename)
        allowed_extensions = (
            '.htm', '.html', '.css', '.js', '.svg', '.jpg', '.jpeg', 
            '.png', '.gif', '.ico', '.bmp', '.webp', '.tiff', '.pdf',
            '.json', '.xml', '.txt', '.md'
        )
        
        if os.path.isfile(full_path):
            file_extension = os.path.splitext(filename)[1].lower()
            if file_extension in allowed_extensions:
                directory = os.path.dirname(full_path)
                filename_only = os.path.basename(full_path)
                return send_from_directory(directory, filename_only)
            else:
                return "Tipo de archivo no permitido", 403
        else:
            return "Archivo no encontrado", 404
            
    except Exception as e:
        logging.error(f"Error sirviendo archivo estatico {filename}: {e}")
        return "Error interno del servidor", 500

# RUTA PRINCIPAL DEL CHATBOT con subpath
@app.route('/chat', methods=['POST'])
def chat():
    try:
        session_id = request.headers.get('X-Session-ID', 'default_session')
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No se enviaron datos JSON'}), 400
            
        user_question = data.get('question')
        if not user_question:
            return jsonify({'error': 'No se proporciono pregunta'}), 400

        with chat_history_lock:
            response_data = chatbot_service.process_question(user_question, session_id)
        
        return jsonify(response_data)

    except Exception as e:
        logging.error(f"Error general en /chat: {e}")
        return jsonify({'error': f'Error del servidor: {str(e)}'}), 500

@app.route('/clear_chat_history', methods=['POST'])
def clear_chat_history():
    session_id = request.headers.get('X-Session-ID', 'default_session')
    
    success = chatbot_service.clear_chat_history(session_id)
    
    if success:
        return jsonify({"status": "success", "message": "Historial limpiado."})
    else:
        return jsonify({"status": "error", "message": "Error al limpiar historial."}), 500

@app.route('/health', methods=['GET'])
def health_check():
    health_status = chatbot_service.get_health_status()
    status_code = 200 if health_status.get("status") == "ok" else 503
    return jsonify(health_status), status_code

@app.route('/debug/files', methods=['GET'])
def debug_files():
    try:
        files_info = {}
        important_dirs = ['assets', 'template', 'whxdata']
        
        for dir_name in important_dirs:
            dir_path = os.path.join(BASE_DIR, dir_name)
            if os.path.exists(dir_path):
                files_info[dir_name] = []
                for root, dirs, files in os.walk(dir_path):
                    rel_path = os.path.relpath(root, dir_path)
                    if rel_path == '.':
                        rel_path = dir_name
                    files_info[f"{dir_name}/{rel_path}"] = files
            else:
                files_info[dir_name] = "DIRECTORIO NO ENCONTRADO"
        
        root_files = [f for f in os.listdir(BASE_DIR) if os.path.isfile(os.path.join(BASE_DIR, f))]
        files_info['root'] = root_files
        
        return jsonify(files_info)
    except Exception as e:
        return jsonify({"error": str(e)})

# Rutas de administracion con subpath
@app.route('/admin/documents/update', methods=['POST'])
def update_documents():
    """Actualiza documentos en Weaviate"""
    try:
        data = request.get_json() or {}
        document_path = data.get('path', 'C:\\Easysoft')
        force_rebuild = data.get('force_rebuild', False)
        
        # Verificar permisos (agregar autenticacion aqui si es necesario)
        # if not is_admin_user(request):
        #     return jsonify({'error': 'No autorizado'}), 403
        
        from weaviate_manager import WeaviateManager
        
        manager = WeaviateManager()
        try:
            stats = manager.update_documents(document_path, force_rebuild)
            
            if "error" in stats:
                return jsonify({
                    'success': False,
                    'error': 'Error durante la actualizacion'
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
    '''Obtiene estadisticas de documentos con mejor manejo de errores'''
    try:
        logging.info("Obteniendo estadisticas de documentos...")
        from weaviate_manager import WeaviateManager
        
        manager = WeaviateManager()
        try:
            # Verificar conexion a Weaviate
            if not manager.weaviate_client or not manager.weaviate_client.is_ready():
                logging.error("Weaviate no esta conectado o no esta listo")
                return jsonify({
                    'success': False,
                    'error': 'No se pudo conectar a Weaviate',
                    'stats': {
                        'total_documents_weaviate': 0,
                        'total_documents_registry': 0,
                        'connection_status': 'disconnected'
                    }
                })
            
            # Verificar si la coleccion existe
            if not manager.weaviate_client.collections.exists("Documento"):
                logging.warning("La coleccion 'Documento' no existe")
                return jsonify({
                    'success': True,
                    'stats': {
                        'total_documents_weaviate': 0,
                        'total_documents_registry': len(manager.document_registry),
                        'vectorized_documents': 0,
                        'documents_with_errors': 0,
                        'collection_exists': False
                    }
                })
            
            # Obtener estadisticas
            stats = manager.get_statistics()
            
            # Agregar informacion adicional
            stats['connection_status'] = 'connected'
            stats['collection_exists'] = True
            
            if "error" in stats:
                logging.error(f"Error en estadisticas: {stats['error']}")
                return jsonify({
                    'success': False,
                    'error': stats['error'],
                    'stats': {
                        'total_documents_weaviate': 0,
                        'total_documents_registry': 0
                    }
                })
            
            logging.info(f"Estadisticas obtenidas exitosamente: {stats}")
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
            'error': f'Error del servidor: {str(e)}',
            'stats': {
                'total_documents_weaviate': 0,
                'total_documents_registry': 0,
                'error': str(e)
            }
        })

@app.route('/admin/documents/scan', methods=['POST'])
def scan_documents():
    '''Escanea directorio sin actualizar'''
    try:
        data = request.get_json() or {}
        document_path = data.get('path', 'C:\\Local\\EasySoft')
        
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
    return send_from_directory('.', 'admin_panel.html')

if __name__ == '__main__':
    try:
        print(f" Iniciando servidor en http://{Config.FLASK_HOST}:{Config.FLASK_PORT}/")
        app.run(debug=Config.FLASK_DEBUG, host=Config.FLASK_HOST, port=Config.FLASK_PORT)
    finally:
        chatbot_service.cleanup()