#!/bin/bash
# setup_utf8.sh - Configurar y validar UTF-8 en Docker

echo "?? Configurando UTF-8 y vectorizando base de datos..."

# Paso 1: Verificar que Docker esté corriendo
echo "1?? Verificando servicios Docker..."
docker-compose ps

# Paso 2: Parar servicios actuales
echo "2?? Deteniendo servicios actuales..."
docker-compose down

# Paso 3: Limpiar volúmenes si es necesario (OPCIONAL)
read -p "¿Limpiar volúmenes existentes? (s/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo "?? Limpiando volúmenes..."
    docker-compose down -v
    docker volume prune -f
fi

# Paso 4: Construir con caché limpio
echo "3?? Construyendo imagen Docker..."
docker-compose build --no-cache

# Paso 5: Iniciar servicios
echo "4?? Iniciando servicios..."
docker-compose up -d

# Paso 6: Esperar a que Weaviate esté listo
echo "5?? Esperando a que Weaviate esté listo..."
sleep 10

# Verificar que Weaviate esté corriendo
if ! docker-compose exec -T weaviate curl -f http://localhost:8080/v1/.well-known/ready >/dev/null 2>&1; then
    echo "? Weaviate no está listo. Esperando más tiempo..."
    sleep 20
fi

# Paso 7: Validar codificación UTF-8
echo "6?? Validando y corrigiendo codificación UTF-8..."
docker-compose exec chatbot python validate_encoding.py /app --fix

# Paso 8: Inicializar base de datos
echo "7?? Inicializando base de datos Weaviate..."
docker-compose exec chatbot python init_weaviate.py

# Paso 9: Verificar que todo funciona
echo "8?? Verificando la instalación..."
docker-compose exec chatbot python diagnose_weaviate.py

# Paso 10: Mostrar logs si hay errores
echo "9?? Mostrando logs recientes..."
docker-compose logs --tail=20 chatbot

echo "? Configuración completada!"
echo ""
echo "?? Acceder al chatbot: http://localhost:5000"
echo "?? Panel admin: http://localhost:5000/admin"
echo "?? Ver logs: docker-compose logs -f chatbot"
echo ""
echo "?? Comandos útiles:"
echo "  docker-compose logs chatbot          # Ver logs"
echo "  docker-compose exec chatbot bash     # Acceder al contenedor"
echo "  docker-compose restart chatbot       # Reiniciar chatbot"