#!/bin/bash

# Zeus EAA Compliance Tool - Setup Verification Script
# Verifies that all components are ready for deployment

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

# Check file structure
check_files() {
    header "Checking File Structure"
    
    local files=(
        "zeus-eaa-compliance-tool.py"
        "zeus-aks-integration/__init__.py"
        "zeus-aks-integration/core.py"
        "zeus-aks-integration/types.py"
        "zeus-aks-integration/interface.py"
        "zeus-web-ui/api/main.py"
        "zeus-web-ui/static/app.js"
        "k8s/base/namespace.yaml"
        "zeus-aks-integration/k8s/namespace.yaml"
        "k8s/base/deployment.yaml"
        "k8s/base/service.yaml"
        "k8s/base/rbac.yaml"
        "k8s/base/configmap.yaml"
        "k8s/base/hpa.yaml"
        "Dockerfile"
        "deploy-to-aks.sh"
        "setup-environment.sh"
    )
    
    local missing_files=0
    for file in "${files[@]}"; do
        if [[ -f "$file" ]]; then
            success "$file exists"
        else
            error "$file is missing"
            ((missing_files++))
        fi
    done
    
    if [[ $missing_files -eq 0 ]]; then
        success "All required files are present"
    else
        error "$missing_files files are missing"
        return 1
    fi
}

# Test Python imports
test_imports() {
    header "Testing Python Imports"
    
    # Create temporary symlink for testing
    ln -sf zeus-aks-integration zeus_aks_integration 2>/dev/null || true
    
    python3 -c "
import sys
sys.path.append('.')
try:
    from zeus_aks_integration import ZeusAksIntegrationModule, ZeusAksIntegrationConfig
    print('✅ Python imports work correctly')
except Exception as e:
    print(f'❌ Import failed: {e}')
    sys.exit(1)
" && success "Python imports successful" || error "Python imports failed"
    
    # Clean up symlink
    rm -f zeus_aks_integration
}

# Check Kubernetes manifests
check_k8s_manifests() {
    header "Validating Kubernetes Manifests"
    
    # Check namespace consistency
    local zeus_eaa_ns=$(grep "name: zeus-eaa" k8s/base/namespace.yaml | wc -l)
    local zeus_processing_ns=$(grep "name: zeus-processing" zeus-aks-integration/k8s/namespace.yaml | wc -l)
    
    if [[ $zeus_eaa_ns -gt 0 ]]; then
        success "zeus-eaa namespace defined"
    else
        error "zeus-eaa namespace not found"
    fi
    
    if [[ $zeus_processing_ns -gt 0 ]]; then
        success "zeus-processing namespace defined"
    else
        error "zeus-processing namespace not found"
    fi
    
    # Validate YAML syntax (if kubectl is available)
    if command -v kubectl &> /dev/null; then
        log "Validating YAML syntax with kubectl..."
        for file in k8s/base/*.yaml zeus-aks-integration/k8s/*.yaml; do
            if kubectl apply --dry-run=client -f "$file" &> /dev/null; then
                success "$(basename "$file") has valid YAML syntax"
            else
                error "$(basename "$file") has invalid YAML syntax"
            fi
        done
    else
        warn "kubectl not found - skipping YAML validation"
    fi
}

# Check deployment script
check_deployment_script() {
    header "Checking Deployment Script"
    
    # Check syntax
    if bash -n deploy-to-aks.sh; then
        success "deploy-to-aks.sh has valid syntax"
    else
        error "deploy-to-aks.sh has syntax errors"
        return 1
    fi
    
    # Check that it includes both namespaces
    if grep -q "zeus-aks-integration/k8s/namespace.yaml" deploy-to-aks.sh; then
        success "Deployment script includes zeus-processing namespace"
    else
        error "Deployment script missing zeus-processing namespace"
    fi
}

# Check Docker configuration
check_docker() {
    header "Checking Docker Configuration"
    
    # Check Dockerfile syntax
    if [[ -f "Dockerfile" ]]; then
        success "Dockerfile exists"
        
        # Check for symlink creation (the fix for imports)
        if grep -q "ln -sf.*zeus_aks_integration" Dockerfile; then
            success "Dockerfile includes symlink fix for imports"
        else
            error "Dockerfile missing symlink fix"
        fi
        
        # Check entrypoint
        if grep -q "ENTRYPOINT.*zeus-web-ui/api/main.py" Dockerfile; then
            success "Dockerfile has correct entrypoint"
        else
            warn "Dockerfile entrypoint might need verification"
        fi
    else
        error "Dockerfile is missing"
    fi
}

# Check requirements
check_requirements() {
    header "Checking Requirements Files"
    
    local req_files=(
        "zeus-web-ui/requirements.txt"
        "zeus-aks-integration/requirements.txt"
    )
    
    for req_file in "${req_files[@]}"; do
        if [[ -f "$req_file" ]]; then
            local package_count=$(grep -v "^#" "$req_file" | grep -v "^$" | wc -l)
            success "$req_file exists with $package_count packages"
        else
            error "$req_file is missing"
        fi
    done
}

# Main verification
main() {
    header "Zeus EAA Compliance Tool - Setup Verification"
    echo "Verifying that all components are ready for deployment..."
    echo ""
    
    local checks_passed=0
    local total_checks=6
    
    check_files && ((checks_passed++))
    echo ""
    
    test_imports && ((checks_passed++))
    echo ""
    
    check_k8s_manifests && ((checks_passed++))
    echo ""
    
    check_deployment_script && ((checks_passed++))
    echo ""
    
    check_docker && ((checks_passed++))
    echo ""
    
    check_requirements && ((checks_passed++))
    echo ""
    
    header "Verification Summary"
    if [[ $checks_passed -eq $total_checks ]]; then
        success "All checks passed! ($checks_passed/$total_checks)"
        success "🎉 Application is ready for deployment!"
        echo ""
        echo "Next steps:"
        echo "1. Run: ./setup-environment.sh (to create Azure resources)"
        echo "2. Set required environment variables"
        echo "3. Run: ./deploy-to-aks.sh staging"
    else
        error "Some checks failed ($checks_passed/$total_checks passed)"
        error "Please fix the issues above before deploying"
        exit 1
    fi
}

main "$@"
