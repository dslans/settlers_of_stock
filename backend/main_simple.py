"""
Simple version of main.py for initial Cloud Run deployment.
This version starts without external dependencies to verify the deployment works.
"""

import logging
import sys
from datetime import datetime
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Settlers of Stock API",
    description="Conversational stock research application API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Response models
class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: datetime
    environment: str

class StatusResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: datetime
    environment: str
    uptime: str
    dependencies: Dict[str, str]

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Settlers of Stock API (Simple Mode)...")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Settlers of Stock API...")

# Health endpoints
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with basic API information."""
    return {
        "message": "Settlers of Stock API is running (Simple Mode)",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    Returns basic service health information.
    """
    return HealthResponse(
        status="healthy",
        service="settlers-of-stock-api",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        environment="production"
    )

@app.get("/status", response_model=StatusResponse)
async def status_check():
    """
    Detailed status endpoint with dependency checks.
    Provides comprehensive service status information.
    """
    dependencies = {
        "database": "not_configured",
        "redis": "not_configured",
        "external_apis": "not_configured"
    }
    
    return StatusResponse(
        status="operational",
        service="settlers-of-stock-api",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        environment="production",
        uptime="running",
        dependencies=dependencies
    )

if __name__ == "__main__":
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )