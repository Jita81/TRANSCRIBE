# Zeus EAA Compliance Tool - Enterprise Video Processing Platform

<div align="center">

![Zeus Network](https://img.shields.io/badge/Zeus-Network-blue?style=for-the-badge)
![EAA Compliant](https://img.shields.io/badge/EAA-Compliant-green?style=for-the-badge)
![Azure AKS](https://img.shields.io/badge/Azure-AKS-0078d4?style=for-the-badge)
![GPU Accelerated](https://img.shields.io/badge/GPU-Accelerated-76b900?style=for-the-badge)

**Enterprise-scale video subtitle processing with AI-powered transcription and EAA compliance validation**

[🚀 Quick Start](#quick-start) • [📖 Documentation](#documentation) • [🏗️ Architecture](#architecture) • [🐳 Deployment](#deployment) • [🔧 Development](#development)

</div>

## 🌟 Overview

The Zeus EAA Compliance Tool is a production-ready, enterprise-scale video processing platform that transforms videos into accessible subtitles compliant with European Accessibility Act (EAA) and WCAG 2.1 AA standards. Built on Azure Kubernetes Service (AKS) with GPU acceleration, it processes thousands of videos with fault tolerance and automatic scaling.

### ✨ Key Features

- **🎯 EAA/WCAG 2.1 AA Compliance** - Automated validation and scoring
- **🚀 Enterprise Scale** - Azure AKS with GPU nodes and auto-scaling
- **🤖 AI-Powered** - Multi-pass Whisper transcription with confidence consolidation
- **🔄 Fault Tolerant** - Circuit breakers, retries, and automatic recovery
- **💰 Cost Optimized** - Spot instances and intelligent resource management
- **🔒 Secure** - Enterprise security with RBAC and workload identity
- **📊 Observable** - Comprehensive monitoring and metrics

## 🏗️ Architecture

```mermaid
graph TB
    subgraph "Input Layer"
        A[Video Upload] --> B[Azure Blob Storage]
    end
    
    subgraph "Processing Layer"
        B --> C[Zeus Integration API]
        C --> D[Kubernetes Job Queue]
        D --> E[GPU Processing Pods]
        E --> F[Multi-Pass Whisper]
        F --> G[AI Consolidation]
        G --> H[EAA Validation]
    end
    
    subgraph "Output Layer"
        H --> I[Subtitle Export]
        I --> J[Azure Blob Storage]
        J --> K[CDN Distribution]
    end
    
    subgraph "Infrastructure"
        L[Auto Scaler] --> D
        M[Load Balancer] --> C
        N[Monitoring] --> E
        O[Security] --> C
    end
    
    style E fill:#e1f5fe
    style F fill:#f3e5f5
    style H fill:#e8f5e8
```

### 🎬 Processing Pipeline

1. **Video Ingestion** - Upload to Azure Blob Storage with automatic detection
2. **Job Orchestration** - Kubernetes-based job scheduling with priority queues
3. **GPU Processing** - NVIDIA Tesla T4/V100 accelerated transcription
4. **Multi-Pass Analysis** - 5-pass Whisper transcription with temperature variation
5. **AI Consolidation** - Confidence-weighted text consolidation and timing optimization
6. **Compliance Validation** - Automated EAA/WCAG scoring and quality assurance
7. **Format Export** - SRT, WebVTT, and JSON with metadata
8. **Distribution** - CDN-ready output with secure access

## 📦 Project Structure

```
zeus-eaa-compliance-tool/
├── 🐍 zeus-eaa-compliance-tool.tsx      # Core processing engine
├── 🔧 zeus-aks-integration/             # Enterprise AKS integration
│   ├── 📋 core.py                       # Integration orchestration
│   ├── 📝 types.py                      # Type definitions
│   ├── 🐳 Dockerfile                    # Production container
│   ├── 📊 k8s/                          # Kubernetes manifests
│   │   ├── deployment.yaml              # API deployment
│   │   ├── service.yaml                 # Load balancing
│   │   ├── hpa.yaml                     # Auto-scaling
│   │   ├── rbac.yaml                    # Security policies
│   │   └── secrets.yaml                 # Credential management
│   ├── 🚀 scripts/deploy.sh             # Deployment automation
│   └── 📖 README.md                     # Integration documentation
├── 🏗️ Standardized-Modules-Framework/   # Enterprise framework
└── 📚 docs/                             # Complete documentation
```

## 🚀 Quick Start

### Prerequisites

- **Azure Subscription** with AKS and ACR access
- **Azure CLI** installed and configured
- **kubectl** for Kubernetes management
- **Docker** for local development
- **Python 3.9+** with GPU support (optional for local testing)

### 1. Azure Setup

```bash
# Login to Azure
az login

# Set environment variables
export RESOURCE_GROUP="zeus-rg"
export AKS_CLUSTER="zeus-aks-cluster"
export ACR_NAME="zeusregistry"
export STORAGE_ACCOUNT="zeusstorage"
export LOCATION="eastus2"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION
```

### 2. Infrastructure Deployment

```bash
# Create AKS cluster with GPU nodes
az aks create \
    --resource-group $RESOURCE_GROUP \
    --name $AKS_CLUSTER \
    --node-count 2 \
    --node-vm-size Standard_NC6s_v3 \
    --enable-cluster-autoscaler \
    --min-count 1 \
    --max-count 10 \
    --attach-acr $ACR_NAME

# Create storage account
az storage account create \
    --name $STORAGE_ACCOUNT \
    --resource-group $RESOURCE_GROUP \
    --sku Standard_LRS
```

### 3. Deploy Zeus Platform

```bash
# Clone and navigate
git clone https://github.com/zeus-network/eaa-compliance-tool.git
cd eaa-compliance-tool/zeus-aks-integration

# Deploy to AKS
./scripts/deploy.sh production

# Verify deployment
kubectl get pods -n zeus-processing
```

### 4. Process Your First Video

```bash
# Upload video to Azure Blob Storage
az storage blob upload \
    --account-name $STORAGE_ACCOUNT \
    --container-name video-input \
    --name test-video.mp4 \
    --file ./test-video.mp4

# Submit processing job
curl -X POST https://your-zeus-api-endpoint/api/v1/process \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://zeusstorage.blob.core.windows.net/video-input/test-video.mp4",
    "compliance_level": "eaa",
    "priority": "normal"
  }'
```

## 🐳 Deployment Options

### Production (Azure AKS)

**Recommended for enterprise workloads**

```bash
# Production deployment with full monitoring
./scripts/deploy.sh production

# Features:
# ✅ Auto-scaling (2-20 replicas)
# ✅ GPU node pools with spot instances
# ✅ Load balancing with SSL termination
# ✅ Monitoring and alerting
# ✅ Backup and disaster recovery
```

### Staging (Azure AKS)

**For testing and validation**

```bash
# Staging deployment with reduced resources
./scripts/deploy.sh staging

# Features:
# ✅ Single replica deployment
# ✅ Smaller GPU nodes
# ✅ Basic monitoring
# ✅ Cost-optimized configuration
```

### Local Development

**For development and testing**

```bash
# Local Docker Compose setup
docker-compose up -d

# Features:
# ✅ Local GPU access (if available)
# ✅ Hot reload for development
# ✅ Local storage simulation
# ✅ Debug logging enabled
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `AKS_CLUSTER_NAME` | Azure AKS cluster name | ✅ | - |
| `RESOURCE_GROUP` | Azure resource group | ✅ | - |
| `STORAGE_ACCOUNT_NAME` | Azure storage account | ✅ | - |
| `WHISPER_MODEL` | Whisper model size | ❌ | `large-v3` |
| `NUM_PASSES` | Transcription passes | ❌ | `5` |
| `COMPLIANCE_LEVEL` | Default compliance level | ❌ | `eaa` |
| `MAX_CONCURRENT_JOBS` | Max parallel jobs | ❌ | `10` |
| `GPU_NODE_SELECTOR` | GPU node selection | ❌ | `nvidia-tesla-t4` |

### Processing Configuration

```yaml
# zeus-config.yaml
processing:
  whisper_model: "large-v3"      # Model size: tiny, base, small, medium, large, large-v2, large-v3
  num_passes: 5                  # Multi-pass transcription (1-10)
  temperature_range: [0.0, 0.8] # Temperature variation for passes
  beam_size: 5                   # Beam search width
  
compliance:
  target_level: "eaa"            # EAA, WCAG_AA, Section_508
  reading_speed_wpm: 160         # Words per minute target
  min_duration_seconds: 1.0      # Minimum subtitle duration
  max_duration_seconds: 7.0      # Maximum subtitle duration
  max_chars_per_subtitle: 80     # Character limit per subtitle

scaling:
  min_replicas: 2                # Minimum API replicas
  max_replicas: 20               # Maximum API replicas
  target_cpu_percent: 70         # CPU scaling threshold
  target_memory_percent: 80      # Memory scaling threshold
  gpu_nodes_min: 1               # Minimum GPU nodes
  gpu_nodes_max: 50              # Maximum GPU nodes
```

## 📊 Monitoring & Observability

### Health Checks

```bash
# Check API health
curl https://your-zeus-api/health

# Check processing status
curl https://your-zeus-api/api/v1/status

# View cluster metrics
kubectl top nodes
kubectl top pods -n zeus-processing
```

### Metrics Dashboard

The platform includes comprehensive monitoring:

- **📈 Processing Metrics** - Jobs, throughput, success rates
- **🖥️ Resource Metrics** - CPU, memory, GPU utilization
- **🎯 Quality Metrics** - Compliance scores, confidence levels
- **💰 Cost Metrics** - Resource costs, optimization opportunities
- **🚨 Alerting** - Automated alerts for failures and thresholds

### Logging

Structured JSON logging with correlation IDs:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "zeus-processor",
  "request_id": "req-abc123",
  "video_url": "https://storage.blob.core.windows.net/input/video.mp4",
  "job_name": "zeus-process-abc123-1705315800",
  "stage": "transcription",
  "progress": 0.75,
  "message": "Multi-pass transcription in progress"
}
```

## 🔒 Security

### Authentication & Authorization

- **🔐 Azure AD Integration** - Workload Identity for pod authentication
- **🎫 RBAC Policies** - Kubernetes role-based access control
- **🔑 Managed Identities** - Secure Azure resource access
- **🛡️ Network Policies** - Pod-to-pod communication restrictions

### Data Security

- **🔒 Encryption at Rest** - Azure Storage encryption
- **🚀 Encryption in Transit** - TLS 1.3 for all communications
- **🗝️ Key Management** - Azure Key Vault integration
- **📋 Audit Logging** - Complete audit trail for compliance

### Container Security

- **🐳 Non-root Containers** - Security contexts with minimal privileges
- **📦 Distroless Images** - Minimal attack surface
- **🔍 Vulnerability Scanning** - Automated security scanning
- **🚫 Read-only Filesystems** - Immutable container filesystems

## 💰 Cost Optimization

### Scaling Strategies

```yaml
# Horizontal Pod Autoscaler
hpa:
  min_replicas: 2
  max_replicas: 20
  metrics:
    - cpu: 70%
    - memory: 80%
    - custom: queue_depth

# Vertical Pod Autoscaler
vpa:
  update_mode: "Auto"
  resource_policy:
    cpu: 100m-4000m
    memory: 512Mi-8Gi
```

### Cost Monitoring

- **💸 Spot Instances** - Up to 90% savings on GPU nodes
- **⚡ Auto-scaling** - Scale to zero during low usage
- **📊 Resource Optimization** - Right-sizing based on actual usage
- **🎯 Efficient Scheduling** - Bin-packing for optimal resource utilization

### Estimated Costs

| Configuration | Monthly Cost | Use Case |
|---------------|--------------|----------|
| **Development** | $50-100 | Single developer, basic testing |
| **Staging** | $200-500 | Team testing, integration validation |
| **Production (Small)** | $500-1,500 | Small enterprise, <1000 videos/month |
| **Production (Large)** | $2,000-10,000 | Large enterprise, >10,000 videos/month |

*Costs include AKS cluster, GPU nodes, storage, and networking. Actual costs vary by usage patterns and Azure region.*

## 🧪 Testing

### Unit Tests

```bash
# Run all tests
pytest zeus-aks-integration/tests/ -v

# Run with coverage
pytest --cov=zeus_aks_integration --cov-report=html

# Run specific test categories
pytest -k "test_processing" -v
```

### Integration Tests

```bash
# End-to-end processing test
python3 tests/integration/test_e2e_processing.py

# Load testing
python3 tests/performance/test_load.py --concurrent-jobs=10
```

### Compliance Testing

```bash
# EAA compliance validation
python3 tests/compliance/test_eaa_validation.py

# WCAG 2.1 AA testing
python3 tests/compliance/test_wcag_validation.py
```

## 📖 API Reference

### Process Video

```http
POST /api/v1/process
Content-Type: application/json

{
  "video_url": "https://storage.blob.core.windows.net/input/video.mp4",
  "compliance_level": "eaa",
  "priority": "normal",
  "callback_url": "https://your-app.com/webhook",
  "metadata": {
    "user_id": "user123",
    "organization": "acme-corp"
  }
}
```

### Get Job Status

```http
GET /api/v1/jobs/{job_id}

Response:
{
  "job_id": "job-abc123",
  "status": "processing",
  "progress": 0.75,
  "estimated_completion": "2024-01-15T10:45:00Z",
  "outputs": {
    "srt": "https://storage.blob.core.windows.net/output/job-abc123.srt",
    "vtt": "https://storage.blob.core.windows.net/output/job-abc123.vtt"
  },
  "compliance_report": {
    "score": 95,
    "level": "eaa",
    "issues": [],
    "warnings": ["Reading speed slightly high in segment 3"]
  }
}
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone repository
git clone https://github.com/zeus-network/eaa-compliance-tool.git
cd eaa-compliance-tool

# Setup development environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt

# Run pre-commit hooks
pre-commit install
```

### Code Standards

- **🐍 Python 3.9+** with type hints
- **🔍 Linting** with flake8 and mypy
- **🧪 Testing** with pytest (>90% coverage)
- **📝 Documentation** with comprehensive docstrings
- **🔒 Security** following OWASP guidelines

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation

- **📖 [Full Documentation](https://docs.zeus-network.com/eaa-compliance)**
- **🏗️ [Architecture Guide](docs/architecture.md)**
- **🚀 [Deployment Guide](docs/deployment.md)**
- **🔧 [API Reference](docs/api.md)**

### Community

- **💬 [Discord Community](https://discord.gg/zeus-network)**
- **📧 [Mailing List](https://groups.google.com/g/zeus-eaa-compliance)**
- **🐛 [Issue Tracker](https://github.com/zeus-network/eaa-compliance-tool/issues)**

### Enterprise Support

For enterprise support, custom deployments, and SLA agreements:

- **📧 Email**: enterprise@zeus-network.com
- **📞 Phone**: +1 (555) 123-ZEUS
- **🌐 Website**: [zeus-network.com/enterprise](https://zeus-network.com/enterprise)

---

<div align="center">

**Built with ❤️ by the Zeus Network Team**

[🌟 Star us on GitHub](https://github.com/zeus-network/eaa-compliance-tool) • [🐦 Follow us on Twitter](https://twitter.com/zeus_network) • [💼 Visit our Website](https://zeus-network.com)

</div>
