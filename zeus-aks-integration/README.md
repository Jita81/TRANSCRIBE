# Zeus AKS Integration Module

## Overview

The Zeus AKS Integration Module provides enterprise-scale video subtitle processing using Azure Kubernetes Service (AKS) with GPU nodes. This integration module orchestrates the Zeus EAA Compliance Tool for high-throughput, fault-tolerant video processing with automatic scaling capabilities.

## Features

### 🚀 Enterprise Scale Processing
- **Azure Kubernetes Service (AKS)** with GPU node pools
- **Horizontal Pod Autoscaling** based on queue depth and resource utilization
- **Spot instance support** for cost optimization
- **Multi-zone deployment** for high availability

### 🎯 EAA Compliance
- **WCAG 2.1 AA** compliance validation
- **EAA (European Accessibility Act)** standards
- **Section 508** compliance support
- **Automated quality scoring** and reporting

### 🔧 Processing Pipeline
- **Multi-pass Whisper transcription** with confidence consolidation
- **GPU-accelerated processing** using NVIDIA Tesla T4/V100
- **Fault-tolerant job execution** with automatic retry
- **Real-time progress tracking** and metrics

### ☁️ Azure Integration
- **Azure Blob Storage** for video input/output
- **Azure Container Registry** for image management
- **Azure Monitor** integration for observability
- **Azure Active Directory** for authentication

## Quick Start

### Prerequisites

- Azure CLI installed and configured
- kubectl installed
- Docker installed
- Access to an Azure subscription with AKS and ACR

### 1. Environment Setup

```bash
# Set environment variables
export RESOURCE_GROUP="zeus-rg"
export AKS_CLUSTER="zeus-aks-cluster"
export ACR_NAME="zeusregistry"
export STORAGE_ACCOUNT="zeusstorage"

# Azure authentication
az login
```

### 2. Deploy to AKS

```bash
# Deploy to staging
./scripts/deploy.sh staging

# Deploy to production
./scripts/deploy.sh production
```

### 3. Local Development

```bash
# Start local development environment
docker-compose up -d

# Run tests
pytest tests/

# Process a test video
python3 -c "
from zeus_aks_integration import ZeusAksIntegrationModule, ZeusAksIntegrationConfig, ZeusAksIntegrationRequest
import asyncio

async def test_processing():
    config = ZeusAksIntegrationConfig(
        aks_cluster_name='zeus-aks-cluster',
        resource_group='zeus-rg',
        subscription_id='your-subscription-id',
        storage_account_name='zeusstorage',
        storage_account_key='your-storage-key'
    )
    
    module = ZeusAksIntegrationModule(config)
    await module.initialize()
    
    request = ZeusAksIntegrationRequest(
        request_id='test-001',
        operation='process_video',
        video_blob_url='https://zeusstorage.blob.core.windows.net/input/test.mp4',
        priority='normal',
        compliance_level='eaa'
    )
    
    result = await module.call_external_service(request)
    print(f'Processing result: {result.data}')

asyncio.run(test_processing())
"
```

## API Operations

### Process Video

```python
request = ZeusAksIntegrationRequest(
    request_id='unique-id',
    operation='process_video',
    video_blob_url='https://storage.blob.core.windows.net/input/video.mp4',
    priority='high',  # 'low', 'normal', 'high', 'urgent'
    compliance_level='eaa',  # 'wcag_aa', 'eaa', 'section_508'
    whisper_model='large-v3',
    num_passes=5
)
```

### Get Job Status

```python
request = ZeusAksIntegrationRequest(
    request_id='unique-id',
    operation='get_status'
)
```

### List Jobs

```python
request = ZeusAksIntegrationRequest(
    request_id='list-request',
    operation='list_jobs'
)
```

### Scale Cluster

```python
request = ZeusAksIntegrationRequest(
    request_id='scale-request',
    operation='scale_cluster',
    node_count=10
)
```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `AKS_CLUSTER_NAME` | AKS cluster name | Yes | - |
| `RESOURCE_GROUP` | Azure resource group | Yes | - |
| `SUBSCRIPTION_ID` | Azure subscription ID | Yes | - |
| `STORAGE_ACCOUNT_NAME` | Azure storage account | Yes | - |
| `STORAGE_ACCOUNT_KEY` | Storage account key | Yes | - |
| `WHISPER_MODEL` | Whisper model size | No | `large-v3` |
| `NUM_PASSES` | Transcription passes | No | `5` |
| `NAMESPACE` | Kubernetes namespace | No | `zeus-processing` |

## Deployment

The module includes complete Kubernetes manifests for production deployment:

- **Namespace**: Isolated environment for Zeus processing
- **RBAC**: Service accounts and permissions for job management
- **Secrets**: Secure storage for Azure credentials
- **Deployment**: API service with rolling updates
- **Service**: Load balancer and internal communication
- **HPA**: Automatic scaling based on CPU/memory
- **Job Templates**: GPU-enabled processing pods

## Monitoring

### Health Checks

- **Liveness Probe**: `/health` endpoint
- **Readiness Probe**: `/ready` endpoint
- **Startup Probe**: Initial container health

### Metrics

The module exposes Prometheus metrics:

- `zeus_jobs_total` - Total jobs processed
- `zeus_jobs_duration_seconds` - Job processing time
- `zeus_jobs_active` - Currently active jobs
- `zeus_gpu_utilization` - GPU utilization percentage
- `zeus_compliance_score` - Average compliance scores

## Security

### Authentication & Authorization

- **Azure AD Integration** - Workload Identity for pod authentication
- **RBAC Policies** - Kubernetes role-based access control
- **Managed Identities** - Secure Azure resource access
- **Network Policies** - Pod-to-pod communication restrictions

### Container Security

- **Non-root Containers** - Security contexts with minimal privileges
- **Read-only Filesystems** - Immutable container filesystems
- **Vulnerability Scanning** - Automated security scanning
- **Image Signing** - Signed container images

## Cost Optimization

### Scaling Strategies

- **Spot Instances** - Up to 90% savings on GPU nodes
- **Auto-scaling** - Scale to zero during low usage
- **Resource Optimization** - Right-sizing based on actual usage
- **Efficient Scheduling** - Bin-packing for optimal resource utilization

## License

MIT License - see LICENSE file for details.

## Support

For support and questions:

- **Documentation**: [Zeus AKS Integration Docs](https://docs.zeus-network.com/aks-integration)
- **Issues**: [GitHub Issues](https://github.com/zeus-network/aks-integration/issues)
- **Contact**: devops@zeus-network.com
