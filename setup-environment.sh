#!/bin/bash

# Zeus EAA Compliance Tool - Environment Setup Script
# Sets up Azure resources for AKS deployment

set -euo pipefail

# Configuration
RESOURCE_GROUP="${RESOURCE_GROUP:-zeus-rg}"
AKS_CLUSTER="${AKS_CLUSTER:-zeus-aks-cluster}"
ACR_NAME="${ACR_NAME:-zeusregistry}"
STORAGE_ACCOUNT="${STORAGE_ACCOUNT:-zeusstorage$(date +%s)}"
LOCATION="${LOCATION:-eastus2}"

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

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

header() {
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}$(echo "$1" | sed 's/./=/g')${NC}"
}

# Create resource group
create_resource_group() {
    header "Creating Resource Group"
    
    if az group show --name "$RESOURCE_GROUP" &>/dev/null; then
        log "Resource group $RESOURCE_GROUP already exists"
    else
        log "Creating resource group: $RESOURCE_GROUP"
        az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
        success "Resource group created"
    fi
}

# Create Azure Container Registry
create_acr() {
    header "Creating Azure Container Registry"
    
    if az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
        log "ACR $ACR_NAME already exists"
    else
        log "Creating Azure Container Registry: $ACR_NAME"
        az acr create \
            --resource-group "$RESOURCE_GROUP" \
            --name "$ACR_NAME" \
            --sku Standard \
            --admin-enabled true
        success "ACR created"
    fi
}

# Create AKS cluster
create_aks_cluster() {
    header "Creating AKS Cluster"
    
    if az aks show --name "$AKS_CLUSTER" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
        log "AKS cluster $AKS_CLUSTER already exists"
    else
        log "Creating AKS cluster: $AKS_CLUSTER (this may take 10-15 minutes)"
        az aks create \
            --resource-group "$RESOURCE_GROUP" \
            --name "$AKS_CLUSTER" \
            --node-count 2 \
            --node-vm-size Standard_D4s_v3 \
            --enable-cluster-autoscaler \
            --min-count 1 \
            --max-count 10 \
            --attach-acr "$ACR_NAME" \
            --enable-managed-identity \
            --enable-workload-identity \
            --enable-oidc-issuer \
            --generate-ssh-keys
        
        success "AKS cluster created"
    fi
    
    # Add GPU node pool
    log "Checking for GPU node pool..."
    if ! az aks nodepool show --cluster-name "$AKS_CLUSTER" --resource-group "$RESOURCE_GROUP" --name gpunodes &>/dev/null; then
        log "Adding GPU node pool for video processing..."
        az aks nodepool add \
            --resource-group "$RESOURCE_GROUP" \
            --cluster-name "$AKS_CLUSTER" \
            --name gpunodes \
            --node-count 0 \
            --min-count 0 \
            --max-count 5 \
            --node-vm-size Standard_NC6s_v3 \
            --enable-cluster-autoscaler \
            --node-taints sku=gpu:NoSchedule
        success "GPU node pool added"
    else
        log "GPU node pool already exists"
    fi
}

# Create storage account
create_storage_account() {
    header "Creating Storage Account"
    
    if az storage account show --name "$STORAGE_ACCOUNT" --resource-group "$RESOURCE_GROUP" &>/dev/null; then
        log "Storage account $STORAGE_ACCOUNT already exists"
    else
        log "Creating storage account: $STORAGE_ACCOUNT"
        az storage account create \
            --name "$STORAGE_ACCOUNT" \
            --resource-group "$RESOURCE_GROUP" \
            --location "$LOCATION" \
            --sku Standard_LRS \
            --kind StorageV2
        success "Storage account created"
    fi
    
    # Create containers
    log "Creating blob containers..."
    STORAGE_KEY=$(az storage account keys list --resource-group "$RESOURCE_GROUP" --account-name "$STORAGE_ACCOUNT" --query '[0].value' --output tsv)
    
    for container in video-input subtitle-output; do
        if ! az storage container show --name "$container" --account-name "$STORAGE_ACCOUNT" --account-key "$STORAGE_KEY" &>/dev/null; then
            az storage container create --name "$container" --account-name "$STORAGE_ACCOUNT" --account-key "$STORAGE_KEY"
            log "Created container: $container"
        else
            log "Container $container already exists"
        fi
    done
}

# Create service principal
create_service_principal() {
    header "Creating Service Principal"
    
    SP_NAME="zeus-eaa-sp"
    
    # Check if service principal already exists
    if az ad sp list --display-name "$SP_NAME" --query '[0].appId' -o tsv | grep -q .; then
        log "Service principal $SP_NAME already exists"
        CLIENT_ID=$(az ad sp list --display-name "$SP_NAME" --query '[0].appId' -o tsv)
    else
        log "Creating service principal: $SP_NAME"
        SP_INFO=$(az ad sp create-for-rbac --name "$SP_NAME" --role Contributor --scopes "/subscriptions/$(az account show --query id -o tsv)")
        CLIENT_ID=$(echo "$SP_INFO" | jq -r '.appId')
        success "Service principal created"
    fi
    
    # Get additional info
    TENANT_ID=$(az account show --query tenantId -o tsv)
    SUBSCRIPTION_ID=$(az account show --query id -o tsv)
    
    echo ""
    echo -e "${GREEN}Service Principal Information:${NC}"
    echo "CLIENT_ID: $CLIENT_ID"
    echo "TENANT_ID: $TENANT_ID"
    echo "SUBSCRIPTION_ID: $SUBSCRIPTION_ID"
    echo ""
    echo -e "${YELLOW}Note: You'll need to get the CLIENT_SECRET from the Azure portal or regenerate it.${NC}"
}

# Display environment information
show_environment_info() {
    header "Environment Information"
    
    # Get storage key
    STORAGE_KEY=$(az storage account keys list --resource-group "$RESOURCE_GROUP" --account-name "$STORAGE_ACCOUNT" --query '[0].value' --output tsv)
    
    echo "Resource Group: $RESOURCE_GROUP"
    echo "Location: $LOCATION"
    echo "AKS Cluster: $AKS_CLUSTER"
    echo "ACR Name: $ACR_NAME"
    echo "Storage Account: $STORAGE_ACCOUNT"
    echo ""
    
    echo -e "${GREEN}Environment Variables for Deployment:${NC}"
    echo "export RESOURCE_GROUP=\"$RESOURCE_GROUP\""
    echo "export AKS_CLUSTER=\"$AKS_CLUSTER\""
    echo "export ACR_NAME=\"$ACR_NAME\""
    echo "export STORAGE_ACCOUNT_NAME=\"$STORAGE_ACCOUNT\""
    echo "export STORAGE_ACCOUNT_KEY=\"$STORAGE_KEY\""
    echo "export AZURE_SUBSCRIPTION_ID=\"$(az account show --query id -o tsv)\""
    echo "export AZURE_TENANT_ID=\"$(az account show --query tenantId -o tsv)\""
    echo ""
    
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "1. Set the environment variables above"
    echo "2. Set AZURE_CLIENT_ID and AZURE_CLIENT_SECRET for your service principal"
    echo "3. Run: ./deploy-to-aks.sh staging"
}

# Main setup flow
main() {
    header "Zeus EAA Compliance Tool - Environment Setup"
    echo "This will create Azure resources for the Zeus EAA Compliance Tool"
    echo ""
    echo "Resources to create:"
    echo "- Resource Group: $RESOURCE_GROUP"
    echo "- AKS Cluster: $AKS_CLUSTER"
    echo "- Container Registry: $ACR_NAME"
    echo "- Storage Account: $STORAGE_ACCOUNT"
    echo "- Location: $LOCATION"
    echo ""
    
    read -p "Continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Setup cancelled"
        exit 0
    fi
    
    create_resource_group
    create_acr
    create_aks_cluster
    create_storage_account
    create_service_principal
    show_environment_info
    
    success "🎉 Environment setup completed!"
}

# Check prerequisites
if ! command -v az &> /dev/null; then
    echo -e "${RED}Error: Azure CLI is required but not installed${NC}"
    exit 1
fi

if ! az account show &> /dev/null; then
    echo -e "${RED}Error: Please login to Azure CLI: az login${NC}"
    exit 1
fi

# Run main function
main "$@"
