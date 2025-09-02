#!/bin/bash
# deploy-azure-improved.sh - Script completo de despliegue

set -e  # Salir si hay errores

# Variables configurables
RESOURCE_GROUP="chatbot-rg"
LOCATION="East US"
ACR_NAME="chatbotregistry$(date +%s)"  # Nombre único
CONTAINER_APP_ENV="chatbot-env"
STORAGE_ACCOUNT="chatbotstorage$(date +%s)"
WEAVIATE_APP="weaviate-app"
CHATBOT_APP="chatbot-app"

echo " Iniciando despliegue completo en Azure..."
echo " Configuración:"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   Location: $LOCATION"
echo "   ACR: $ACR_NAME"
echo "   Storage: $STORAGE_ACCOUNT"
echo ""

# Verificar Azure CLI
if ! command -v az &> /dev/null; then
    echo " Azure CLI no está instalado"
    exit 1
fi

# Login check
echo " Verificando login de Azure..."
if ! az account show &> /dev/null; then
    echo "Please login to Azure:"
    az login
fi

# Crear grupo de recursos
echo " Creando grupo de recursos..."
az group create \
    --name $RESOURCE_GROUP \
    --location "$LOCATION" \
    --output table

# Crear Azure Container Registry
echo " Creando Azure Container Registry..."
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $ACR_NAME \
    --sku Basic \
    --admin-enabled true \
    --output table

# Obtener credenciales ACR
echo " Obteniendo credenciales de ACR..."
ACR_SERVER=$(az acr show --name $ACR_NAME --resource-group $RESOURCE_GROUP --query loginServer --output tsv)
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username --output tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value --output tsv)

echo "   ACR Server: $ACR_SERVER"

# Build y push de la imagen del chatbot
echo " Construyendo y subiendo imagen del chatbot..."
az acr build \
    --registry $ACR_NAME \
    --image chatbot:latest \
    --file Dockerfile \
    . \
    --output table

# Crear cuenta de almacenamiento
echo " Creando cuenta de almacenamiento..."
az storage account create \
    --name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --location "$LOCATION" \
    --sku Standard_LRS \
    --output table

# Crear Container Apps Environment
echo " Creando Container Apps Environment..."
az containerapp env create \
    --name $CONTAINER_APP_ENV \
    --resource-group $RESOURCE_GROUP \
    --location "$LOCATION" \
    --output table

# Esperar a que el environment esté listo
echo " Esperando que el environment esté listo..."
sleep 30

# Desplegar Weaviate Container App
echo " Desplegando Weaviate..."
az containerapp create \
    --name $WEAVIATE_APP \
    --resource-group $RESOURCE_GROUP \
    --environment $CONTAINER_APP_ENV \
    --image semitechnologies/weaviate:1.30.7 \
    --target-port 8080 \
    --ingress internal \
    --min-replicas 1 \
    --max-replicas 1 \
    --cpu 1.0 \
    --memory 2Gi \
    --env-vars \
        QUERY_DEFAULTS_LIMIT=25 \
        AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
        PERSISTENCE_DATA_PATH=/var/lib/weaviate \
        DEFAULT_VECTORIZER_MODULE=none \
        ENABLE_MODULES="" \
        CLUSTER_HOSTNAME=node1 \
    --output table

# Esperar a que Weaviate esté listo
echo " Esperando que Weaviate esté listo..."
sleep 60

# Desplegar Chatbot Container App
echo " Desplegando Chatbot..."
az containerapp create \
    --name $CHATBOT_APP \
    --resource-group $RESOURCE_GROUP \
    --environment $CONTAINER_APP_ENV \
    --image $ACR_SERVER/chatbot:latest \
    --target-port 80 \
    --ingress external \
    --min-replicas 1 \
    --max-replicas 3 \
    --cpu 0.5 \
    --memory 1Gi \
    --registry-server $ACR_SERVER \
    --registry-username $ACR_USERNAME \
    --registry-password $ACR_PASSWORD \
    --env-vars \
        WEAVIATE_HOST=$WEAVIATE_APP \
        WEAVIATE_HTTP_PORT=8080 \
        WEAVIATE_GRPC_PORT=50051 \
        WEAVIATE_HTTP_SECURE=false \
        WEAVIATE_GRPC_SECURE=false \
        FLASK_HOST=0.0.0.0 \
        FLASK_PORT=80 \
        FLASK_DEBUG=false \
        OPENAI_API_KEY="$OPENAI_API_KEY" \
    --output table

# Obtener URL de la aplicación
echo " Obteniendo URL de la aplicación..."
CHATBOT_URL=$(az containerapp show \
    --name $CHATBOT_APP \
    --resource-group $RESOURCE_GROUP \
    --query properties.configuration.ingress.fqdn \
    --output tsv)

echo ""
echo " Despliegue completado exitosamente!"
echo "="*50
echo " Informacion del despliegue:"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   Chatbot URL: https://$CHATBOT_URL"
echo "   Panel Admin: https://$CHATBOT_URL/admin"
echo "   Health Check: https://$CHATBOT_URL/health"
echo ""
echo " Variables de entorno necesarias:"
echo "   BASE_URL=https://$CHATBOT_URL"
echo "   WEAVIATE_HOST=$WEAVIATE_APP"
echo ""
echo " Para actualizar la aplicación:"
echo "   az acr build --registry $ACR_NAME --image chatbot:latest ."
echo "   az containerapp revision restart --name $CHATBOT_APP --resource-group $RESOURCE_GROUP"
echo ""
echo " Para eliminar todo:"
echo "   az group delete --name $RESOURCE_GROUP --yes --no-wait"