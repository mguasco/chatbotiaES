# Sistema de Gestión de Documentos Weaviate

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
   - Cambia `C:\Easysoft` por tu ruta de documentos

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
