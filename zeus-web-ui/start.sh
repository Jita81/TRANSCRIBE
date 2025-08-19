#!/bin/bash

# Zeus EAA Compliance Tool - Web UI Startup Script

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Zeus EAA Compliance Tool - Web UI${NC}"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "api/main.py" ]; then
    echo -e "${RED}❌ Error: Please run this script from the zeus-web-ui directory${NC}"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: Python 3 is required but not installed${NC}"
    exit 1
fi

# Install requirements
echo -e "${YELLOW}📦 Installing requirements...${NC}"
pip3 install -r requirements.txt

# Check if Zeus AKS integration is available
if [ ! -d "../zeus-aks-integration" ]; then
    echo -e "${RED}❌ Error: Zeus AKS Integration module not found${NC}"
    echo "Make sure you're running this from the correct directory structure"
    exit 1
fi

# Set default environment variables if not set
export AKS_CLUSTER_NAME=${AKS_CLUSTER_NAME:-"zeus-aks-cluster"}
export RESOURCE_GROUP=${RESOURCE_GROUP:-"zeus-rg"}
export SUBSCRIPTION_ID=${SUBSCRIPTION_ID:-"your-subscription-id"}
export STORAGE_ACCOUNT_NAME=${STORAGE_ACCOUNT_NAME:-"zeusstorage"}
export STORAGE_ACCOUNT_KEY=${STORAGE_ACCOUNT_KEY:-"your-storage-key"}
export WHISPER_MODEL=${WHISPER_MODEL:-"large-v3"}
export NUM_PASSES=${NUM_PASSES:-"5"}

echo -e "${GREEN}✅ Environment configured:${NC}"
echo "   AKS Cluster: $AKS_CLUSTER_NAME"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   Storage Account: $STORAGE_ACCOUNT_NAME"
echo "   Whisper Model: $WHISPER_MODEL"
echo ""

echo -e "${YELLOW}⚠️  Note: Make sure you have:${NC}"
echo "   • Azure CLI installed and authenticated (az login)"
echo "   • kubectl configured for your AKS cluster"
echo "   • Proper Azure credentials set in environment variables"
echo ""

echo -e "${BLUE}🌐 Starting Web UI...${NC}"
echo "   API Documentation: http://localhost:8000/docs"
echo "   Web Interface: http://localhost:8000"
echo ""

# Change to API directory and start the server
cd api
python3 main.py
