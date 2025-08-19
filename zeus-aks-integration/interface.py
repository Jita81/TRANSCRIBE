"""
Interface definition for Zeus AKS Integration
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

from .types import ZeusAksIntegrationConfig, ZeusAksIntegrationRequest, ZeusAksIntegrationResponse, OperationResult

class ZeusAksIntegrationInterface(ABC):
    """
    Interface for Zeus AKS Integration module
    Type: INTEGRATION
    
    Defines the contract that all Zeus AKS integration implementations must follow.
    """
    
    @abstractmethod
    async def initialize(self) -> OperationResult:
        """
        Initialize the module
        
        Returns:
            OperationResult indicating success or failure
        """
        pass
    
    @abstractmethod
    async def call_external_service(self, request: ZeusAksIntegrationRequest) -> OperationResult[ZeusAksIntegrationResponse]:
        """
        Make a call to the external service
        
        Args:
            request: Request data for the external service
            
        Returns:
            OperationResult containing the service response or error
        """
        pass
    
    @abstractmethod
    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get the current health status of the module
        
        Returns:
            Dictionary containing health status information
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> OperationResult:
        """
        Gracefully shutdown the module
        
        Returns:
            OperationResult indicating shutdown success or failure
        """
        pass
