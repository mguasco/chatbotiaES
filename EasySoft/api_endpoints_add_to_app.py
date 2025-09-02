# api_endpoints_add_to_app.py
# INSTRUCCIONES: Agrega estos endpoints a tu archivo app.py

@app.route('/admin/documents/update', methods=['POST'])
def update_documents():
    """Actualiza documentos en Weaviate"""
    try:
        data = request.get_json() or {}
        document_path = data.get('path', 'C:\\Easysoft')
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
        document_path = data.get('path', 'C:\\Easysoft')
        
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
