#!/usr/bin/env python3
"""
Zeus EAA Compliance Tool - Web API
FastAPI backend for the Zeus video processing system
"""

import os
import uuid
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

# Import our Zeus integration module
import sys
sys.path.append('..')
from zeus_aks_integration import (
    ZeusAksIntegrationModule,
    ZeusAksIntegrationConfig,
    ZeusAksIntegrationRequest,
    ProcessingStatus
)

# Pydantic models for API
class VideoProcessRequest(BaseModel):
    video_url: str
    priority: str = "normal"
    compliance_level: str = "eaa"
    whisper_model: Optional[str] = None
    num_passes: Optional[int] = None
    user_id: Optional[str] = None
    organization: Optional[str] = None

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: Optional[float] = None
    created_at: str
    updated_at: Optional[str] = None
    estimated_completion: Optional[str] = None
    outputs: Optional[Dict[str, str]] = None
    metrics: Optional[Dict[str, float]] = None
    error_details: Optional[str] = None

class ClusterStatusResponse(BaseModel):
    cluster_name: str
    node_count: int
    active_jobs: int
    queue_depth: int
    health_status: str

# Initialize FastAPI app
app = FastAPI(
    title="Zeus EAA Compliance Tool API",
    description="Enterprise video processing for EAA compliance",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global variables
zeus_module: Optional[ZeusAksIntegrationModule] = None
config: Optional[ZeusAksIntegrationConfig] = None

@app.on_event("startup")
async def startup_event():
    """Initialize Zeus AKS Integration on startup"""
    global zeus_module, config
    
    # Configuration from environment variables
    config = ZeusAksIntegrationConfig(
        aks_cluster_name=os.getenv("AKS_CLUSTER_NAME", "zeus-aks-cluster"),
        resource_group=os.getenv("RESOURCE_GROUP", "zeus-rg"),
        subscription_id=os.getenv("SUBSCRIPTION_ID", "your-subscription-id"),
        storage_account_name=os.getenv("STORAGE_ACCOUNT_NAME", "zeusstorage"),
        storage_account_key=os.getenv("STORAGE_ACCOUNT_KEY", "your-storage-key"),
        whisper_model=os.getenv("WHISPER_MODEL", "large-v3"),
        num_passes=int(os.getenv("NUM_PASSES", "5"))
    )
    
    zeus_module = ZeusAksIntegrationModule(config)
    
    # Initialize the module
    try:
        result = await zeus_module.initialize()
        if result.success:
            print("✅ Zeus AKS Integration initialized successfully")
        else:
            print(f"❌ Failed to initialize Zeus integration: {result.error}")
    except Exception as e:
        print(f"❌ Startup error: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global zeus_module
    if zeus_module:
        await zeus_module.shutdown()

# API Routes

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main UI page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Zeus EAA Compliance Tool</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    </head>
    <body>
        <div id="app"></div>
        <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
        <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
        <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
        <script src="/static/app.js" type="text/babel"></script>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if not zeus_module:
        raise HTTPException(status_code=503, detail="Zeus module not initialized")
    
    health = await zeus_module.get_health_status()
    return {
        "status": "healthy" if health["status"] == "healthy" else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "module_status": health
    }

@app.post("/api/v1/process")
async def process_video(request: VideoProcessRequest, background_tasks: BackgroundTasks):
    """Submit a video for processing"""
    if not zeus_module:
        raise HTTPException(status_code=503, detail="Zeus module not initialized")
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Create Zeus integration request
    zeus_request = ZeusAksIntegrationRequest(
        request_id=job_id,
        operation="process_video",
        video_blob_url=request.video_url,
        priority=request.priority,
        compliance_level=request.compliance_level,
        whisper_model=request.whisper_model,
        num_passes=request.num_passes,
        user_id=request.user_id,
        organization=request.organization
    )
    
    # Submit to Zeus
    result = await zeus_module.call_external_service(zeus_request)
    
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    
    return {
        "job_id": job_id,
        "status": result.data.status,
        "message": "Video processing started successfully",
        "kubernetes_job": result.data.kubernetes_job_name,
        "created_at": result.data.created_at
    }

@app.get("/api/v1/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a processing job"""
    if not zeus_module:
        raise HTTPException(status_code=503, detail="Zeus module not initialized")
    
    zeus_request = ZeusAksIntegrationRequest(
        request_id=job_id,
        operation="get_status"
    )
    
    result = await zeus_module.call_external_service(zeus_request)
    
    if not result.success:
        raise HTTPException(status_code=404, detail=result.error)
    
    return JobStatusResponse(
        job_id=job_id,
        status=result.data.status,
        created_at=result.data.created_at or datetime.now().isoformat(),
        updated_at=result.data.updated_at,
        estimated_completion=result.data.estimated_completion,
        outputs=result.data.subtitle_formats,
        metrics=result.data.processing_metrics,
        error_details=result.data.error_details
    )

@app.get("/api/v1/jobs")
async def list_jobs():
    """List all processing jobs"""
    if not zeus_module:
        raise HTTPException(status_code=503, detail="Zeus module not initialized")
    
    zeus_request = ZeusAksIntegrationRequest(
        request_id="list-jobs-" + str(uuid.uuid4()),
        operation="list_jobs"
    )
    
    result = await zeus_module.call_external_service(zeus_request)
    
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    
    return {
        "jobs": result.data.data["jobs"],
        "total": result.data.data["total"]
    }

@app.get("/api/v1/cluster/status")
async def get_cluster_status():
    """Get cluster status and metrics"""
    if not zeus_module:
        raise HTTPException(status_code=503, detail="Zeus module not initialized")
    
    health = await zeus_module.get_health_status()
    
    return ClusterStatusResponse(
        cluster_name=config.aks_cluster_name,
        node_count=2,  # This would come from actual cluster query
        active_jobs=health["active_jobs"],
        queue_depth=0,  # This would come from job queue
        health_status=health["status"]
    )

@app.post("/api/v1/cluster/scale")
async def scale_cluster(node_count: int):
    """Scale the cluster"""
    if not zeus_module:
        raise HTTPException(status_code=503, detail="Zeus module not initialized")
    
    if node_count < 1 or node_count > 50:
        raise HTTPException(status_code=400, detail="Node count must be between 1 and 50")
    
    zeus_request = ZeusAksIntegrationRequest(
        request_id="scale-" + str(uuid.uuid4()),
        operation="scale_cluster",
        node_count=node_count
    )
    
    result = await zeus_module.call_external_service(zeus_request)
    
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    
    return {
        "message": f"Cluster scaling to {node_count} nodes initiated",
        "status": result.data.status
    }

if __name__ == "__main__":
    print("🚀 Starting Zeus EAA Compliance Tool Web API...")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🎬 Web Interface: http://localhost:8000")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
