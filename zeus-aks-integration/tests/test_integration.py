"""
Integration tests for Zeus AKS Integration Module
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from zeus_aks_integration import (
    ZeusAksIntegrationModule,
    ZeusAksIntegrationConfig,
    ZeusAksIntegrationRequest,
    ZeusAksIntegrationResponse,
    ProcessingStatus
)

@pytest.fixture
def config():
    """Test configuration"""
    return ZeusAksIntegrationConfig(
        aks_cluster_name="test-cluster",
        resource_group="test-rg",
        subscription_id="test-subscription",
        storage_account_name="teststorage",
        storage_account_key="test-key"
    )

@pytest.fixture
def module(config):
    """Test module instance"""
    return ZeusAksIntegrationModule(config)

@pytest.mark.asyncio
class TestZeusAksIntegration:
    """Test cases for Zeus AKS Integration"""
    
    async def test_module_initialization(self, module):
        """Test module initialization"""
        with patch.object(module, '_run_command', new_callable=AsyncMock) as mock_run:
            # Mock successful Azure and kubectl commands
            mock_run.side_effect = [
                {"success": True, "output": "test-account", "error": "", "returncode": 0},  # az account show
                {"success": True, "output": "test-context", "error": "", "returncode": 0},  # kubectl config
                {"success": True, "output": "namespace exists", "error": "", "returncode": 0},  # kubectl get namespace
                {"success": True, "output": "cluster-info", "error": "", "returncode": 0},  # kubectl cluster-info
                {"success": True, "output": "account-info", "error": "", "returncode": 0}   # az account show
            ]
            
            result = await module.initialize()
            
            assert result.success
            assert module._initialized
            assert module._health_status == "healthy"
    
    async def test_process_video_request(self, module):
        """Test video processing request"""
        # Mock initialization
        module._initialized = True
        
        request = ZeusAksIntegrationRequest(
            request_id="test-123",
            operation="process_video",
            video_blob_url="https://storage.blob.core.windows.net/input/test.mp4",
            compliance_level="eaa"
        )
        
        with patch.object(module, '_run_command', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {"success": True, "output": "job created", "error": "", "returncode": 0}
            
            result = await module.call_external_service(request)
            
            assert result.success
            assert isinstance(result.data, ZeusAksIntegrationResponse)
            assert result.data.status == ProcessingStatus.QUEUED.value
            assert result.data.job_id == "test-123"
    
    async def test_get_job_status(self, module):
        """Test job status retrieval"""
        # Mock initialization and add a job
        module._initialized = True
        module._active_jobs["test-123"] = {
            "job_name": "zeus-process-test123-1234567890",
            "kubernetes_job": "zeus-process-test123-1234567890",
            "status": ProcessingStatus.QUEUED.value,
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        request = ZeusAksIntegrationRequest(
            request_id="test-123",
            operation="get_status"
        )
        
        job_status_json = '''
        {
            "metadata": {"name": "test-job"},
            "status": {"active": 1}
        }
        '''
        
        with patch.object(module, '_run_command', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {"success": True, "output": job_status_json, "error": "", "returncode": 0}
            
            result = await module.call_external_service(request)
            
            assert result.success
            assert result.data.status == ProcessingStatus.TRANSCRIBING.value
    
    async def test_list_jobs(self, module):
        """Test job listing"""
        module._initialized = True
        
        request = ZeusAksIntegrationRequest(
            request_id="list-request",
            operation="list_jobs"
        )
        
        jobs_json = '''
        {
            "items": [
                {
                    "metadata": {
                        "name": "zeus-job-1",
                        "creationTimestamp": "2024-01-01T00:00:00Z",
                        "labels": {
                            "request-id": "req-1",
                            "priority": "normal"
                        }
                    },
                    "status": {"succeeded": 1}
                }
            ]
        }
        '''
        
        with patch.object(module, '_run_command', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {"success": True, "output": jobs_json, "error": "", "returncode": 0}
            
            result = await module.call_external_service(request)
            
            assert result.success
            assert result.data.data["total"] == 1
            assert result.data.data["jobs"][0]["status"] == ProcessingStatus.COMPLETED.value
    
    async def test_scale_cluster(self, module):
        """Test cluster scaling"""
        module._initialized = True
        
        request = ZeusAksIntegrationRequest(
            request_id="scale-request",
            operation="scale_cluster",
            node_count=5
        )
        
        with patch.object(module, '_run_command', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {"success": True, "output": "scaling initiated", "error": "", "returncode": 0}
            
            result = await module.call_external_service(request)
            
            assert result.success
            assert result.data.status == "scaling"
            assert result.data.cluster_status["requested_nodes"] == 5
    
    async def test_health_status(self, module):
        """Test health status reporting"""
        module._initialized = True
        module._health_status = "healthy"
        
        health = await module.get_health_status()
        
        assert health["module_name"] == "zeus-aks-integration"
        assert health["type"] == "INTEGRATION"
        assert health["status"] == "healthy"
        assert health["initialized"] == True
    
    async def test_error_handling(self, module):
        """Test error handling for failed operations"""
        module._initialized = True
        
        request = ZeusAksIntegrationRequest(
            request_id="test-error",
            operation="process_video",
            video_blob_url="https://storage.blob.core.windows.net/input/test.mp4"
        )
        
        with patch.object(module, '_run_command', new_callable=AsyncMock) as mock_run:
            mock_run.return_value = {"success": False, "output": "", "error": "kubectl failed", "returncode": 1}
            
            result = await module.call_external_service(request)
            
            assert not result.success
            assert "Failed to create job" in result.error
    
    async def test_unknown_operation(self, module):
        """Test handling of unknown operations"""
        module._initialized = True
        
        request = ZeusAksIntegrationRequest(
            request_id="test-unknown",
            operation="unknown_operation"
        )
        
        result = await module.call_external_service(request)
        
        assert not result.success
        assert "Unknown operation" in result.error
    
    async def test_uninitialized_module(self, module):
        """Test that uninitialized module returns error"""
        request = ZeusAksIntegrationRequest(
            request_id="test-uninit",
            operation="process_video"
        )
        
        result = await module.call_external_service(request)
        
        assert not result.success
        assert "Integration not initialized" in result.error

if __name__ == "__main__":
    pytest.main([__file__])
