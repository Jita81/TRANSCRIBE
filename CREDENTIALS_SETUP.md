# Zeus EAA Compliance Tool - Credentials Setup Guide

## 🔐 Required Credentials & Access

### Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Azure Subscription** with Contributor or Owner access
- [ ] **Azure CLI** installed and working
- [ ] **kubectl** installed
- [ ] **Docker** installed and running
- [ ] **Sufficient Azure quotas** for GPU VMs (Standard_NC6s_v3)

### Step 1: Azure CLI Authentication

```bash
# Login to Azure
az login

# List available subscriptions
az account list --output table

# Set the correct subscription
az account set --subscription "your-subscription-id"

# Verify authentication
az account show
```

### Step 2: Check Azure Quotas

GPU nodes require special quotas. Check your limits:

```bash
# Check GPU quota in your region
az vm list-usage --location "eastus2" --query "[?contains(name.value, 'Standard_NC')]"

# If quota is 0, request increase through Azure portal:
# Portal > Subscriptions > Usage + quotas > Compute > Request increase
```

### Step 3: Run Environment Setup

```bash
# This creates all Azure resources and service principal
./setup-environment.sh
```

The script will output something like:
```bash
Service Principal Information:
CLIENT_ID: 12345678-1234-1234-1234-123456789abc
TENANT_ID: 87654321-4321-4321-4321-cba987654321
SUBSCRIPTION_ID: abcdef12-3456-7890-abcd-ef1234567890
```

### Step 4: Get Service Principal Secret

The setup script creates the service principal but doesn't show the secret. You need to:

**Option A: Generate new secret (Recommended)**
```bash
# Get the service principal app ID from setup output
SP_APP_ID="your-client-id-from-setup"

# Create new secret
az ad app credential reset --id $SP_APP_ID --query password --output tsv
```

**Option B: Use Azure Portal**
1. Go to Azure Portal > Azure Active Directory > App registrations
2. Find "zeus-eaa-sp" application
3. Go to Certificates & secrets
4. Create new client secret
5. Copy the secret value (you can only see it once!)

### Step 5: Set Environment Variables

```bash
# From setup script output
export RESOURCE_GROUP="zeus-rg"
export AKS_CLUSTER="zeus-aks-cluster"
export ACR_NAME="zeusregistry"
export STORAGE_ACCOUNT_NAME="zeusstorage123456789"
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
export AZURE_TENANT_ID="your-tenant-id"

# From service principal setup
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"

# Get storage key
export STORAGE_ACCOUNT_KEY=$(az storage account keys list \
  --resource-group $RESOURCE_GROUP \
  --account-name $STORAGE_ACCOUNT_NAME \
  --query '[0].value' --output tsv)
```

### Step 6: Verify Credentials

```bash
# Test Azure authentication
az account show

# Test service principal
az login --service-principal \
  --username $AZURE_CLIENT_ID \
  --password $AZURE_CLIENT_SECRET \
  --tenant $AZURE_TENANT_ID

# Switch back to your user account
az login

# Test storage access
az storage container list \
  --account-name $STORAGE_ACCOUNT_NAME \
  --account-key $STORAGE_ACCOUNT_KEY
```

## 🔒 Security Best Practices

### Environment Variables Management

**For Development:**
```bash
# Create .env file (add to .gitignore!)
cat > .env << EOF
RESOURCE_GROUP=zeus-rg
AKS_CLUSTER=zeus-aks-cluster
ACR_NAME=zeusregistry
STORAGE_ACCOUNT_NAME=zeusstorage123456789
STORAGE_ACCOUNT_KEY=your-storage-key
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
EOF

# Load environment
source .env
```

**For Production:**
- Use Azure Key Vault for secrets
- Use Managed Identity where possible
- Rotate secrets regularly
- Use least-privilege access

### Service Principal Security

```bash
# List service principal permissions
az role assignment list --assignee $AZURE_CLIENT_ID --output table

# The service principal should have:
# - Contributor role on the resource group
# - AcrPush role on the container registry
```

## 🚨 Common Issues & Solutions

### Issue: "Insufficient quota for GPU VMs"
```bash
# Check current quota
az vm list-usage --location eastus2 --query "[?contains(name.value, 'Standard_NC')]"

# Solution: Request quota increase in Azure Portal
# Portal > Subscriptions > Usage + quotas > Compute
```

### Issue: "Service principal authentication failed"
```bash
# Verify service principal exists
az ad sp show --id $AZURE_CLIENT_ID

# Test authentication
az login --service-principal \
  --username $AZURE_CLIENT_ID \
  --password $AZURE_CLIENT_SECRET \
  --tenant $AZURE_TENANT_ID
```

### Issue: "Container registry access denied"
```bash
# Check ACR permissions
az acr show --name $ACR_NAME --query loginServer
az role assignment list --scope "/subscriptions/$AZURE_SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ContainerRegistry/registries/$ACR_NAME"

# Fix: Assign AcrPush role
az role assignment create \
  --assignee $AZURE_CLIENT_ID \
  --role AcrPush \
  --scope "/subscriptions/$AZURE_SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ContainerRegistry/registries/$ACR_NAME"
```

### Issue: "Storage account access denied"
```bash
# Verify storage account exists
az storage account show --name $STORAGE_ACCOUNT_NAME --resource-group $RESOURCE_GROUP

# Test access
az storage container list --account-name $STORAGE_ACCOUNT_NAME --account-key $STORAGE_ACCOUNT_KEY
```

## 💰 Cost Management

### Monitor Costs
```bash
# Check current costs
az consumption usage list --start-date 2024-01-01 --end-date 2024-01-31

# Set up budget alerts in Azure Portal
# Cost Management + Billing > Budgets
```

### GPU Node Cost Optimization
- Use **Spot instances** for GPU nodes (up to 90% savings)
- Set **auto-scaling to 0 minimum** when not processing
- Use **smaller GPU VMs** for development (Standard_NC6s_v3 vs Standard_NC24s_v3)

## 📋 Credentials Checklist

Before deployment, verify you have:

- [ ] Azure CLI authenticated (`az account show` works)
- [ ] Correct subscription selected
- [ ] Service principal created with CLIENT_ID and CLIENT_SECRET
- [ ] All environment variables set
- [ ] Storage account key obtained
- [ ] GPU quota available in your region
- [ ] Docker running locally
- [ ] kubectl installed

## 🔄 Credential Rotation

For production environments, rotate credentials regularly:

```bash
# Rotate service principal secret
az ad app credential reset --id $AZURE_CLIENT_ID

# Update Kubernetes secrets
kubectl create secret generic azure-service-principal \
  --from-literal=CLIENT_ID="$AZURE_CLIENT_ID" \
  --from-literal=CLIENT_SECRET="$AZURE_CLIENT_SECRET" \
  --from-literal=TENANT_ID="$AZURE_TENANT_ID" \
  --namespace=zeus-eaa \
  --dry-run=client -o yaml | kubectl apply -f -
```

---

**🔐 Keep your credentials secure and never commit them to version control!**
