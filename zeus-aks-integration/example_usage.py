#!/usr/bin/env python3
"""
Example usage of Zeus AKS Integration Module

This script demonstrates how to use the Zeus AKS Integration Module
to process videos for EAA compliance on Azure Kubernetes Service.
"""

import asyncio
import logging
from zeus_aks_integration import (
    ZeusAksIntegrationModule,
    ZeusAksIntegrationConfig,
    ZeusAksIntegrationRequest,
    ProcessingStatus
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Main example function"""
    
    # Configuration - Update these values for your environment
    config = ZeusAksIntegrationConfig(
        aks_cluster_name="zeus-aks-cluster",
        resource_group="zeus-rg", 
        subscription_id="your-subscription-id",
        storage_account_name="zeusstorage",
        storage_account_key="your-storage-key",
        whisper_model="large-v3",
        num_passes=5
    )
    
    # Initialize the module
    module = ZeusAksIntegrationModule(config)
    
    logger.info("Initializing Zeus AKS Integration...")
    init_result = await module.initialize()
    
    if not init_result.success:
        logger.error(f"Failed to initialize: {init_result.error}")
        return
    
    logger.info("✅ Module initialized successfully")
    
    # Check health status
    health = await module.get_health_status()
    logger.info(f"Health Status: {health['status']}")
    
    # Example 1: Process a video
    logger.info("\n🎬 Example 1: Processing a video")
    
    process_request = ZeusAksIntegrationRequest(
        request_id="example-video-001",
        operation="process_video",
        video_blob_url="https://zeusstorage.blob.core.windows.net/video-input/sample.mp4",
        priority="normal",
        compliance_level="eaa",
        whisper_model="large-v3",
        num_passes=5,
        user_id="demo-user",
        organization="demo-org"
    )
    
    result = await module.call_external_service(process_request)
    
    if result.success:
        logger.info(f"✅ Video processing started")
        logger.info(f"   Job ID: {result.data.job_id}")
        logger.info(f"   Status: {result.data.status}")
        logger.info(f"   Kubernetes Job: {result.data.kubernetes_job_name}")
    else:
        logger.error(f"❌ Failed to start processing: {result.error}")
        return
    
    # Example 2: Check job status
    logger.info("\n📊 Example 2: Checking job status")
    
    status_request = ZeusAksIntegrationRequest(
        request_id="example-video-001",
        operation="get_status"
    )
    
    # Simulate checking status multiple times
    for i in range(3):
        await asyncio.sleep(2)  # Wait a bit between checks
        
        result = await module.call_external_service(status_request)
        
        if result.success:
            logger.info(f"   Check {i+1}: Status = {result.data.status}")
            if result.data.processing_metrics:
                metrics = result.data.processing_metrics
                logger.info(f"   Metrics: CPU={metrics.get('cpu_usage', 0):.1f}%, GPU={metrics.get('gpu_utilization', 0):.1f}%")
            
            # If completed, show outputs
            if result.data.status == ProcessingStatus.COMPLETED.value and result.data.subtitle_formats:
                logger.info("   📁 Output files:")
                for format_type, url in result.data.subtitle_formats.items():
                    logger.info(f"      {format_type.upper()}: {url}")
        else:
            logger.error(f"   ❌ Status check failed: {result.error}")
    
    # Example 3: List all jobs
    logger.info("\n📋 Example 3: Listing all jobs")
    
    list_request = ZeusAksIntegrationRequest(
        request_id="list-all-jobs",
        operation="list_jobs"
    )
    
    result = await module.call_external_service(list_request)
    
    if result.success:
        jobs = result.data.data["jobs"]
        logger.info(f"   Found {len(jobs)} jobs:")
        for job in jobs:
            logger.info(f"      {job['name']}: {job['status']} (Priority: {job['priority']})")
    else:
        logger.error(f"   ❌ Failed to list jobs: {result.error}")
    
    # Example 4: Scale cluster (be careful with this in production!)
    logger.info("\n⚖️  Example 4: Cluster scaling (demo only)")
    
    scale_request = ZeusAksIntegrationRequest(
        request_id="scale-demo",
        operation="scale_cluster",
        node_count=2  # Scale to 2 nodes
    )
    
    # Uncomment the following lines to actually scale (use with caution!)
    # result = await module.call_external_service(scale_request)
    # 
    # if result.success:
    #     logger.info(f"✅ Cluster scaling initiated")
    #     logger.info(f"   Requested nodes: {result.data.cluster_status['requested_nodes']}")
    # else:
    #     logger.error(f"❌ Scaling failed: {result.error}")
    
    logger.info("   (Scaling skipped in demo - uncomment to enable)")
    
    # Shutdown
    logger.info("\n🔄 Shutting down module...")
    shutdown_result = await module.shutdown()
    
    if shutdown_result.success:
        logger.info("✅ Module shutdown completed")
    else:
        logger.error(f"❌ Shutdown failed: {shutdown_result.error}")

def run_example():
    """Run the example with proper error handling"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⚠️  Example interrupted by user")
    except Exception as e:
        logger.error(f"❌ Example failed with error: {e}")
        raise

if __name__ == "__main__":
    print("🚀 Zeus AKS Integration Module - Example Usage")
    print("=" * 50)
    print()
    print("This example demonstrates:")
    print("• Module initialization and health checking")
    print("• Video processing job submission")
    print("• Job status monitoring")
    print("• Job listing")
    print("• Cluster scaling (demo)")
    print()
    print("⚠️  Make sure you have:")
    print("• Azure CLI installed and authenticated (az login)")
    print("• kubectl configured for your AKS cluster")
    print("• Updated the configuration values in this script")
    print()
    
    input("Press Enter to continue...")
    print()
    
    run_example()
