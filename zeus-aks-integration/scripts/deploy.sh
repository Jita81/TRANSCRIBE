#!/bin/bash

# Zeus AKS Integration Deployment Script
# Deploys the Zeus EAA Compliance Tool to Azure Kubernetes Service

set -euo pipefail

# Configuration
ENVIRONMENT="${1:-staging}"
RESOURCE_GROUP="${RESOURCE_GROUP:-zeus-rg}"
AKS_CLUSTER="${AKS_CLUSTER:-zeus-aks-cluster}"
ACR_NAME="${ACR_NAME:-zeusregistry}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Azure CLI
    if ! command -v az &> /dev/null; then
        error "Azure CLI is required but not installed"
    fi
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is required but not installed"
    fi
    
    # Check if logged into Azure
    if ! az account show &> /dev/null; then
        error "Please login to Azure CLI: az login"
    fi
    
    success "Prerequisites check passed"
}

# Get AKS credentials
get_aks_credentials() {
    log "Getting AKS credentials..."
    az aks get-credentials --resource-group "$RESOURCE_GROUP" --name "$AKS_CLUSTER" --overwrite-existing
    success "AKS credentials obtained"
}

# Deploy Kubernetes manifests
deploy_manifests() {
    log "Deploying Kubernetes manifests..."
    
    # Apply manifests in order (if they exist)
    if [ -f "k8s/namespace.yaml" ]; then
        kubectl apply -f k8s/namespace.yaml
    fi
    
    if [ -f "k8s/rbac.yaml" ]; then
        kubectl apply -f k8s/rbac.yaml
    fi
    
    if [ -f "k8s/secrets.yaml" ]; then
        kubectl apply -f k8s/secrets.yaml
    fi
    
    if [ -f "k8s/deployment.yaml" ]; then
        kubectl apply -f k8s/deployment.yaml
    fi
    
    if [ -f "k8s/service.yaml" ]; then
        kubectl apply -f k8s/service.yaml
    fi
    
    if [ -f "k8s/hpa.yaml" ]; then
        kubectl apply -f k8s/hpa.yaml
    fi
    
    success "Manifests deployed"
}

# Display deployment info
show_deployment_info() {
    log "Deployment Information:"
    echo "========================="
    echo "Environment: $ENVIRONMENT"
    echo "Resource Group: $RESOURCE_GROUP"
    echo "AKS Cluster: $AKS_CLUSTER"
    echo "Namespace: zeus-processing"
    echo ""
    
    log "Service Information:"
    kubectl get services -n zeus-processing 2>/dev/null || echo "No services found"
    echo ""
    
    log "Pod Status:"
    kubectl get pods -n zeus-processing 2>/dev/null || echo "No pods found"
    echo ""
    
    log "Deployment completed successfully!"
}

# Main deployment flow
main() {
    log "Starting Zeus AKS Integration deployment to $ENVIRONMENT..."
    
    check_prerequisites
    get_aks_credentials
    deploy_manifests
    show_deployment_info
    
    success "Deployment completed successfully!"
}

# Run main function
main "$@"
