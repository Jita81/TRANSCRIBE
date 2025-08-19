"""
Type definitions for Zeus AKS Integration
"""

from typing import Dict, Any, List, Optional, Generic, TypeVar
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

T = TypeVar('T')

@dataclass
class ZeusAksIntegrationConfig:
    """Configuration for Zeus AKS Integration module"""
    
    # Azure AKS Configuration
    aks_cluster_name: str
    resource_group: str
    subscription_id: str
    
    # Azure Blob Storage Configuration
    storage_account_name: str
    storage_account_key: str
    input_container: str = "video-input"
    output_container: str = "subtitle-output"
    
    # Kubernetes Configuration
    namespace: str = "zeus-processing"
    service_account: str = "zeus-worker"
    
    # Processing Configuration
    whisper_model: str = "large-v3"
    num_passes: int = 5
    gpu_node_selector: Optional[Dict[str, str]] = None
    
    # External service configuration (Azure APIs)
    base_url: str = "https://management.azure.com"
    api_key: str = ""
    timeout_seconds: int = 300  # Longer timeout for video processing
    circuit_breaker_config: Optional[Dict[str, Any]] = None
    retry_config: Optional[Dict[str, Any]] = None
    rate_limit_config: Optional[Dict[str, Any]] = None

@dataclass
class ZeusAksIntegrationRequest:
    """Request data for Zeus EAA compliance processing"""
    request_id: str
    operation: str  # 'process_video', 'get_status', 'list_jobs', 'scale_cluster'
    
    # Video processing fields
    video_blob_url: Optional[str] = None
    video_filename: Optional[str] = None
    priority: str = "normal"  # 'low', 'normal', 'high', 'urgent'
    
    # Processing options
    whisper_model: Optional[str] = None
    num_passes: Optional[int] = None
    target_languages: Optional[List[str]] = None
    compliance_level: str = "eaa"  # 'wcag_aa', 'eaa', 'section_508'
    
    # Kubernetes scaling
    desired_replicas: Optional[int] = None
    node_count: Optional[int] = None
    
    # Metadata
    user_id: Optional[str] = None
    organization: Optional[str] = None
    callback_url: Optional[str] = None

@dataclass
class ZeusAksIntegrationResponse:
    """Response data from Zeus AKS processing"""
    response_id: str
    status: str  # 'queued', 'processing', 'completed', 'failed', 'scaling'
    
    # Job information
    job_id: Optional[str] = None
    kubernetes_job_name: Optional[str] = None
    
    # Processing results
    subtitle_formats: Optional[Dict[str, str]] = None  # {'srt': 'blob_url', 'vtt': 'blob_url'}
    processing_metrics: Optional[Dict[str, Any]] = None
    compliance_report: Optional[Dict[str, Any]] = None
    
    # Resource information
    cluster_status: Optional[Dict[str, Any]] = None
    node_utilization: Optional[Dict[str, Any]] = None
    estimated_completion: Optional[str] = None
    
    # Error information
    error_details: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    
    # Metadata
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class OperationResult(Generic[T]):
    """Standard result wrapper for all operations"""
    
    def __init__(self, success: bool, data: T = None, error: str = None, error_code: str = None):
        self.success = success
        self.data = data
        self.error = error
        self.error_code = error_code
        self.timestamp = datetime.utcnow()
    
    @classmethod
    def success(cls, data: T = None) -> 'OperationResult[T]':
        """Create a successful result"""
        return cls(success=True, data=data)
    
    @classmethod
    def error(cls, error: str, error_code: str = None) -> 'OperationResult[T]':
        """Create an error result"""
        return cls(success=False, error=error, error_code=error_code)
    
    def __bool__(self) -> bool:
        return self.success

class ModuleStatus(Enum):
    """Module status enumeration"""
    INITIALIZING = "initializing"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"

class ProcessingStatus(Enum):
    """Video processing status enumeration"""
    QUEUED = "queued"
    EXTRACTING_AUDIO = "extracting_audio"
    TRANSCRIBING = "transcribing"
    CONSOLIDATING = "consolidating"
    VALIDATING_TIMING = "validating_timing"
    EXPORTING = "exporting"
    COMPLETED = "completed"
    FAILED = "failed"

class ComplianceLevel(Enum):
    """EAA compliance level enumeration"""
    WCAG_AA = "wcag_aa"
    EAA = "eaa"
    SECTION_508 = "section_508"

@dataclass
class KubernetesJobSpec:
    """Kubernetes job specification for video processing"""
    job_name: str
    namespace: str
    image: str = "zeus-eaa-processor:latest"
    cpu_request: str = "1000m"
    cpu_limit: str = "4000m"
    memory_request: str = "4Gi"
    memory_limit: str = "16Gi"
    gpu_request: int = 1
    node_selector: Optional[Dict[str, str]] = None
    env_vars: Optional[Dict[str, str]] = None
    
@dataclass
class AzureBlobReference:
    """Azure Blob Storage reference"""
    account_name: str
    container_name: str
    blob_name: str
    sas_url: Optional[str] = None
    
@dataclass
class ProcessingMetrics:
    """Video processing metrics"""
    duration_seconds: float
    segments_created: int
    average_confidence: float
    processing_time_seconds: float
    cpu_usage_percent: float
    memory_usage_mb: float
    gpu_utilization_percent: Optional[float] = None
