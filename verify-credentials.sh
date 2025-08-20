#!/bin/bash

# Zeus EAA Compliance Tool - Credentials Verification Script
# Verifies all required credentials are set and working

set -euo pipefail

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
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

header() {
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}$(echo "$1" | sed 's/./=/g')${NC}"
}

# Check if environment variable is set
check_env_var() {
    local var_name=$1
    local description=$2
    
    if [[ -n "${!var_name:-}" ]]; then
        success "$description is set"
        return 0
    else
        error "$description is not set (${var_name})"
        return 1
    fi
}

# Check Azure CLI authentication
check_azure_cli() {
    header "Checking Azure CLI Authentication"
    
    if ! command -v az &> /dev/null; then
        error "Azure CLI is not installed"
        echo "Install: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
        return 1
    fi
    success "Azure CLI is installed"
    
    if az account show &> /dev/null; then
        local account_name=$(az account show --query name --output tsv)
        local subscription_id=$(az account show --query id --output tsv)
        success "Azure CLI authenticated as: $account_name"
        success "Using subscription: $subscription_id"
        return 0
    else
        error "Azure CLI not authenticated. Run: az login"
        return 1
    fi
}

# Check required environment variables
check_environment_variables() {
    header "Checking Environment Variables"
    
    local required_vars=(
        "AZURE_SUBSCRIPTION_ID:Azure Subscription ID"
        "AZURE_CLIENT_ID:Azure Service Principal Client ID" 
        "AZURE_CLIENT_SECRET:Azure Service Principal Secret"
        "AZURE_TENANT_ID:Azure Tenant ID"
        "STORAGE_ACCOUNT_NAME:Azure Storage Account Name"
        "STORAGE_ACCOUNT_KEY:Azure Storage Account Key"
        "RESOURCE_GROUP:Azure Resource Group"
        "AKS_CLUSTER:AKS Cluster Name"
        "ACR_NAME:Azure Container Registry Name"
    )
    
    local missing_vars=0
    for var_desc in "${required_vars[@]}"; do
        local var_name="${var_desc%%:*}"
        local description="${var_desc##*:}"
        
        if ! check_env_var "$var_name" "$description"; then
            ((missing_vars++))
        fi
    done
    
    if [[ $missing_vars -eq 0 ]]; then
        success "All required environment variables are set"
        return 0
    else
        error "$missing_vars environment variables are missing"
        echo ""
        echo "To set them, run:"
        echo "export AZURE_SUBSCRIPTION_ID=\"your-subscription-id\""
        echo "export AZURE_CLIENT_ID=\"your-client-id\""
        echo "export AZURE_CLIENT_SECRET=\"your-client-secret\""
        echo "# ... etc"
        return 1
    fi
}

# Test service principal authentication
test_service_principal() {
    header "Testing Service Principal Authentication"
    
    if [[ -z "${AZURE_CLIENT_ID:-}" || -z "${AZURE_CLIENT_SECRET:-}" || -z "${AZURE_TENANT_ID:-}" ]]; then
        error "Service principal credentials not set"
        return 1
    fi
    
    # Test service principal login (in subshell to not affect current session)
    if (az login --service-principal \
        --username "$AZURE_CLIENT_ID" \
        --password "$AZURE_CLIENT_SECRET" \
        --tenant "$AZURE_TENANT_ID" &> /dev/null); then
        success "Service principal authentication works"
        
        # Switch back to user login
        az login &> /dev/null
        return 0
    else
        error "Service principal authentication failed"
        echo "Check your AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, and AZURE_TENANT_ID"
        return 1
    fi
}

# Test Azure resource access
test_azure_resources() {
    header "Testing Azure Resource Access"
    
    local tests_passed=0
    local total_tests=4
    
    # Test resource group access
    if az group show --name "${RESOURCE_GROUP:-}" &> /dev/null; then
        success "Resource group '$RESOURCE_GROUP' exists and is accessible"
        ((tests_passed++))
    else
        error "Cannot access resource group '$RESOURCE_GROUP'"
    fi
    
    # Test storage account access
    if az storage account show --name "${STORAGE_ACCOUNT_NAME:-}" --resource-group "${RESOURCE_GROUP:-}" &> /dev/null; then
        success "Storage account '$STORAGE_ACCOUNT_NAME' exists"
        ((tests_passed++))
    else
        error "Cannot access storage account '$STORAGE_ACCOUNT_NAME'"
    fi
    
    # Test storage account key
    if az storage container list --account-name "${STORAGE_ACCOUNT_NAME:-}" --account-key "${STORAGE_ACCOUNT_KEY:-}" &> /dev/null; then
        success "Storage account key is valid"
        ((tests_passed++))
    else
        error "Storage account key is invalid"
    fi
    
    # Test AKS cluster access
    if az aks show --name "${AKS_CLUSTER:-}" --resource-group "${RESOURCE_GROUP:-}" &> /dev/null; then
        success "AKS cluster '$AKS_CLUSTER' exists and is accessible"
        ((tests_passed++))
    else
        warn "AKS cluster '$AKS_CLUSTER' not found (may not be created yet)"
        ((tests_passed++))  # Don't fail if cluster doesn't exist yet
    fi
    
    if [[ $tests_passed -eq $total_tests ]]; then
        success "All Azure resources are accessible"
        return 0
    else
        error "Some Azure resources are not accessible ($tests_passed/$total_tests passed)"
        return 1
    fi
}

# Check Docker access
check_docker() {
    header "Checking Docker"
    
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        return 1
    fi
    success "Docker is installed"
    
    if docker info &> /dev/null; then
        success "Docker daemon is running"
        return 0
    else
        error "Docker daemon is not running"
        return 1
    fi
}

# Check kubectl
check_kubectl() {
    header "Checking kubectl"
    
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed"
        echo "Install: https://kubernetes.io/docs/tasks/tools/"
        return 1
    fi
    success "kubectl is installed"
    
    # Try to get AKS credentials if cluster exists
    if [[ -n "${AKS_CLUSTER:-}" && -n "${RESOURCE_GROUP:-}" ]]; then
        if az aks get-credentials --resource-group "$RESOURCE_GROUP" --name "$AKS_CLUSTER" --overwrite-existing &> /dev/null; then
            success "AKS credentials configured"
            
            if kubectl cluster-info &> /dev/null; then
                success "kubectl can connect to AKS cluster"
                return 0
            else
                warn "kubectl configured but cannot connect to cluster"
                return 0  # Don't fail, cluster might not be fully ready
            fi
        else
            warn "Cannot get AKS credentials (cluster may not exist yet)"
            return 0  # Don't fail if cluster doesn't exist
        fi
    else
        warn "AKS cluster info not provided, skipping kubectl test"
        return 0
    fi
}

# Main verification
main() {
    header "Zeus EAA Compliance Tool - Credentials Verification"
    echo "Verifying all required credentials and access..."
    echo ""
    
    local checks_passed=0
    local total_checks=6
    
    check_azure_cli && ((checks_passed++))
    echo ""
    
    check_environment_variables && ((checks_passed++))
    echo ""
    
    test_service_principal && ((checks_passed++))
    echo ""
    
    test_azure_resources && ((checks_passed++))
    echo ""
    
    check_docker && ((checks_passed++))
    echo ""
    
    check_kubectl && ((checks_passed++))
    echo ""
    
    header "Verification Summary"
    if [[ $checks_passed -eq $total_checks ]]; then
        success "All credential checks passed! ($checks_passed/$total_checks)"
        success "🎉 Ready for deployment!"
        echo ""
        echo "Next steps:"
        echo "1. Run: ./verify-setup.sh (to verify application components)"
        echo "2. Run: ./deploy-to-aks.sh staging"
    else
        error "Some credential checks failed ($checks_passed/$total_checks passed)"
        error "Please fix the issues above before deploying"
        echo ""
        echo "Need help? Check CREDENTIALS_SETUP.md for detailed instructions"
        exit 1
    fi
}

main "$@"
