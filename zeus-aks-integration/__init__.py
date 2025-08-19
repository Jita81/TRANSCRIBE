"""
Zeus AKS Integration Module

Enterprise-scale video subtitle processing using Azure Kubernetes Service (AKS)
with GPU nodes for the Zeus EAA Compliance Tool.

This module provides:
- Video processing job orchestration on AKS
- Azure Blob Storage integration for video input/output  
- GPU-accelerated Whisper transcription with multi-pass processing
- EAA/WCAG compliance validation
- Auto-scaling based on queue depth
- Fault-tolerant processing with retry mechanisms

Example usage:
    from zeus_aks_integration import ZeusAksIntegrationModule, ZeusAksIntegrationConfig
    
    config = ZeusAksIntegrationConfig(
        aks_cluster_name="zeus-aks-cluster",
        resource_group="zeus-rg",
        subscription_id="your-subscription-id",
        storage_account_name="zeusstorage",
        storage_account_key="your-storage-key"
    )
    
    module = ZeusAksIntegrationModule(config)
    await module.initialize()
    
    # Process a video
    request = ZeusAksIntegrationRequest(
        request_id="job-123",
        operation="process_video",
        video_blob_url="https://storage.blob.core.windows.net/input/video.mp4"
    )
    
    result = await module.call_external_service(request)
"""

from .core import ZeusAksIntegrationModule
from .types import (
    ZeusAksIntegrationConfig,
    ZeusAksIntegrationRequest, 
    ZeusAksIntegrationResponse,
    OperationResult,
    ProcessingStatus,
    ComplianceLevel,
    KubernetesJobSpec,
    AzureBlobReference,
    ProcessingMetrics
)
from .interface import ZeusAksIntegrationInterface

__version__ = "1.0.0"
__author__ = "Zeus Network Team"

__all__ = [
    "ZeusAksIntegrationModule",
    "ZeusAksIntegrationConfig",
    "ZeusAksIntegrationRequest",
    "ZeusAksIntegrationResponse", 
    "ZeusAksIntegrationInterface",
    "OperationResult",
    "ProcessingStatus",
    "ComplianceLevel",
    "KubernetesJobSpec",
    "AzureBlobReference",
    "ProcessingMetrics"
]
