#!/bin/bash

# Zeus EAA Compliance Tool - AKS Deployment Script
# Complete deployment to Azure Kubernetes Service

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVIRONMENT="${1:-staging}"
RESOURCE_GROUP="${RESOURCE_GROUP:-zeus-rg}"
AKS_CLUSTER="${AKS_CLUSTER:-zeus-aks-cluster}"
ACR_NAME="${ACR_NAME:-zeusregistry}"
IMAGE_TAG="${IMAGE_TAG:-$(git rev-parse --short HEAD)}"
NAMESPACE="zeus-eaa"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

header() {
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}$(echo "$1" | sed 's/./=/g')${NC}"
}

# Check prerequisites
check_prerequisites() {
    header "Checking Prerequisites"
    
    # Check required tools
    for tool in az kubectl docker git; do
        if ! command -v $tool &> /dev/null; then
            error "$tool is required but not installed"
        fi
        log "✓ $tool found"
    done
    
    # Check Azure CLI authentication
    if ! az account show &> /dev/null; then
        error "Please login to Azure CLI: az login"
    fi
    log "✓ Azure CLI authenticated"
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running"
    fi
    log "✓ Docker daemon running"
    
    success "Prerequisites check passed"
}

# Build and push Docker image
build_and_push_image() {
    header "Building and Pushing Docker Image"
    
    # Get ACR login server
    ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --query loginServer --output tsv)
    
    # Login to ACR
    log "Logging into ACR..."
    az acr login --name "$ACR_NAME"
    
    # Build image
    IMAGE_NAME="${ACR_LOGIN_SERVER}/zeus-web-api:${IMAGE_TAG}"
    log "Building image: $IMAGE_NAME"
    docker build -t "$IMAGE_NAME" .
    
    # Push image
    log "Pushing image to ACR..."
    docker push "$IMAGE_NAME"
    
    success "Image built and pushed: $IMAGE_NAME"
    echo "IMAGE_NAME=$IMAGE_NAME" > .env.deploy
}

# Get AKS credentials
get_aks_credentials() {
    header "Getting AKS Credentials"
    az aks get-credentials --resource-group "$RESOURCE_GROUP" --name "$AKS_CLUSTER" --overwrite-existing
    success "AKS credentials obtained"
}

# Create secrets
create_secrets() {
    header "Creating Kubernetes Secrets"
    
    # Check if required environment variables are set
    required_vars=(
        "AZURE_SUBSCRIPTION_ID"
        "AZURE_CLIENT_ID" 
        "AZURE_CLIENT_SECRET"
        "AZURE_TENANT_ID"
        "STORAGE_ACCOUNT_NAME"
        "STORAGE_ACCOUNT_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error "Environment variable $var is required but not set"
        fi
    done
    
    # Create zeus-secrets
    kubectl create secret generic zeus-secrets \
        --from-literal=AKS_CLUSTER_NAME="$AKS_CLUSTER" \
        --from-literal=RESOURCE_GROUP="$RESOURCE_GROUP" \
        --from-literal=SUBSCRIPTION_ID="$AZURE_SUBSCRIPTION_ID" \
        --from-literal=STORAGE_ACCOUNT_NAME="$STORAGE_ACCOUNT_NAME" \
        --from-literal=STORAGE_ACCOUNT_KEY="$STORAGE_ACCOUNT_KEY" \
        --namespace="$NAMESPACE" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Create azure-service-principal secret
    kubectl create secret generic azure-service-principal \
        --from-literal=CLIENT_ID="$AZURE_CLIENT_ID" \
        --from-literal=CLIENT_SECRET="$AZURE_CLIENT_SECRET" \
        --from-literal=TENANT_ID="$AZURE_TENANT_ID" \
        --namespace="$NAMESPACE" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    success "Secrets created/updated"
}

# Deploy Kubernetes manifests
deploy_manifests() {
    header "Deploying Kubernetes Manifests"
    
    # Apply base manifests in order
    log "Applying namespace..."
    kubectl apply -f k8s/base/namespace.yaml
    
    log "Applying RBAC..."
    kubectl apply -f k8s/base/rbac.yaml
    
    log "Applying ConfigMap..."
    kubectl apply -f k8s/base/configmap.yaml
    
    log "Creating secrets..."
    create_secrets
    
    # Update deployment with new image
    if [ -f ".env.deploy" ]; then
        source .env.deploy
        log "Updating deployment with image: $IMAGE_NAME"
        sed "s|zeus-web-api:latest|$IMAGE_NAME|g" k8s/base/deployment.yaml | kubectl apply -f -
    else
        log "Applying deployment with latest tag..."
        kubectl apply -f k8s/base/deployment.yaml
    fi
    
    log "Applying service..."
    kubectl apply -f k8s/base/service.yaml
    
    log "Applying HPA and PDB..."
    kubectl apply -f k8s/base/hpa.yaml
    
    success "Manifests deployed"
}

# Wait for deployment
wait_for_deployment() {
    header "Waiting for Deployment"
    
    log "Waiting for deployment to be ready..."
    kubectl rollout status deployment/zeus-web-api -n "$NAMESPACE" --timeout=600s
    
    log "Waiting for pods to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/component=web-api -n "$NAMESPACE" --timeout=300s
    
    success "Deployment is ready"
}

# Run health check
health_check() {
    header "Running Health Check"
    
    # Get service external IP
    log "Getting service external IP..."
    for i in {1..30}; do
        EXTERNAL_IP=$(kubectl get service zeus-web-api -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
        if [ -n "$EXTERNAL_IP" ] && [ "$EXTERNAL_IP" != "null" ]; then
            break
        fi
        log "Waiting for external IP... ($i/30)"
        sleep 10
    done
    
    if [ -z "$EXTERNAL_IP" ] || [ "$EXTERNAL_IP" == "null" ]; then
        warn "External IP not yet assigned, checking internal service..."
        kubectl port-forward service/zeus-web-api-internal 8080:8000 -n "$NAMESPACE" &
        PORT_FORWARD_PID=$!
        sleep 5
        
        if curl -f http://localhost:8080/health; then
            success "Health check passed (internal)"
        else
            error "Health check failed"
        fi
        
        kill $PORT_FORWARD_PID 2>/dev/null || true
    else
        log "Testing external endpoint: http://$EXTERNAL_IP/health"
        if curl -f "http://$EXTERNAL_IP/health"; then
            success "Health check passed (external IP: $EXTERNAL_IP)"
        else
            error "Health check failed"
        fi
    fi
}

# Display deployment info
show_deployment_info() {
    header "Deployment Information"
    
    echo "Environment: $ENVIRONMENT"
    echo "Resource Group: $RESOURCE_GROUP"
    echo "AKS Cluster: $AKS_CLUSTER"
    echo "Namespace: $NAMESPACE"
    echo "Image: ${IMAGE_NAME:-zeus-web-api:latest}"
    echo ""
    
    log "Service Information:"
    kubectl get services -n "$NAMESPACE"
    echo ""
    
    log "Pod Status:"
    kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/component=web-api
    echo ""
    
    log "HPA Status:"
    kubectl get hpa -n "$NAMESPACE"
    echo ""
    
    # Get external IP
    EXTERNAL_IP=$(kubectl get service zeus-web-api -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    if [ -n "$EXTERNAL_IP" ] && [ "$EXTERNAL_IP" != "null" ]; then
        echo -e "${GREEN}🌐 Web Interface: http://$EXTERNAL_IP${NC}"
        echo -e "${GREEN}📖 API Documentation: http://$EXTERNAL_IP/docs${NC}"
    else
        echo -e "${YELLOW}⏳ External IP still being assigned...${NC}"
        echo "   Check with: kubectl get service zeus-web-api -n $NAMESPACE"
    fi
    
    success "Deployment completed successfully!"
}

# Cleanup function
cleanup() {
    if [ -f ".env.deploy" ]; then
        rm -f .env.deploy
    fi
}
trap cleanup EXIT

# Main deployment flow
main() {
    header "Zeus EAA Compliance Tool - AKS Deployment"
    echo "Environment: $ENVIRONMENT"
    echo "AKS Cluster: $AKS_CLUSTER"
    echo "Resource Group: $RESOURCE_GROUP"
    echo "ACR: $ACR_NAME"
    echo ""
    
    check_prerequisites
    build_and_push_image
    get_aks_credentials
    deploy_manifests
    wait_for_deployment
    health_check
    show_deployment_info
    
    success "🎉 Zeus EAA Compliance Tool deployed successfully to AKS!"
}

# Show usage
usage() {
    echo "Usage: $0 [staging|production]"
    echo ""
    echo "Environment variables required:"
    echo "  AZURE_SUBSCRIPTION_ID  - Azure subscription ID"
    echo "  AZURE_CLIENT_ID        - Service principal client ID"
    echo "  AZURE_CLIENT_SECRET    - Service principal client secret"
    echo "  AZURE_TENANT_ID        - Azure tenant ID"
    echo "  STORAGE_ACCOUNT_NAME   - Azure storage account name"
    echo "  STORAGE_ACCOUNT_KEY    - Azure storage account key"
    echo ""
    echo "Optional environment variables:"
    echo "  RESOURCE_GROUP         - Azure resource group (default: zeus-rg)"
    echo "  AKS_CLUSTER           - AKS cluster name (default: zeus-aks-cluster)"
    echo "  ACR_NAME              - Azure Container Registry name (default: zeusregistry)"
    echo "  IMAGE_TAG             - Docker image tag (default: git commit hash)"
}

# Handle arguments
case "${1:-staging}" in
    staging|production)
        main "$@"
        ;;
    -h|--help|help)
        usage
        ;;
    *)
        error "Invalid environment: $1. Use 'staging' or 'production'"
        ;;
esac
