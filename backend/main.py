import logging
import sys
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
import uvicorn

from app.core.config import get_settings
from app.core.monitoring import request_metrics, health_checker, log_performance_summary
from app.api.stocks import router as stocks_router
from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.websocket import router as websocket_router
from app.api.watchlist import router as watchlist_router
from app.api.alerts import router as alerts_router
from app.api.opportunities import router as opportunities_router
from app.api.historical_analysis import router as historical_analysis_router
from app.api.sectors import router as sectors_router
from app.api.earnings import router as earnings_router
from app.api.education import router as education_router
from app.api.export import router as export_router
from app.api.risk_assessment import router as risk_assessment_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("app.log")
    ]
)

logger = logging.getLogger(__name__)

# Load settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Settlers of Stock API",
    description="Conversational stock research application API",
    version="1.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
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

# Global exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP {exc.status_code} error on {request.url}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error on {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "Validation error",
            "details": exc.errors(),
            "status_code": 422,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error on {request.url}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Middleware configuration
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Request logging and monitoring middleware
@app.middleware("http")
async def log_and_monitor_requests(request: Request, call_next):
    start_time = datetime.utcnow()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    # Track metrics
    response = await request_metrics.track_request(request, call_next)
    
    # Log response
    process_time = (datetime.utcnow() - start_time).total_seconds()
    logger.info(f"Response: {response.status_code} - {process_time:.3f}s")
    
    return response

# Include API routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(stocks_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(websocket_router, prefix="/api/v1")
app.include_router(watchlist_router, prefix="/api/v1")
app.include_router(alerts_router, prefix="/api/v1")
app.include_router(opportunities_router, prefix="/api/v1")
app.include_router(historical_analysis_router, prefix="/api/v1/historical", tags=["Historical Analysis"])
app.include_router(sectors_router, prefix="/api/v1")
app.include_router(earnings_router, prefix="/api/v1")
app.include_router(education_router, prefix="/api/v1")
app.include_router(export_router, prefix="/api/v1")
app.include_router(risk_assessment_router, prefix="/api/v1")

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Settlers of Stock API...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Settlers of Stock API...")
    log_performance_summary()

# Health endpoints
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with basic API information."""
    return {
        "message": "Settlers of Stock API is running",
        "version": "1.0.0",
        "docs": "/docs" if settings.environment != "production" else "disabled"
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
        environment=settings.environment
    )

@app.get("/status", response_model=StatusResponse)
async def status_check():
    """
    Detailed status endpoint with dependency checks.
    Provides comprehensive service status information.
    """
    # Check dependencies
    db_health = await health_checker.check_database_health()
    redis_health = await health_checker.check_redis_health()
    apis_health = await health_checker.check_external_apis_health()
    
    dependencies = {
        "database": db_health["status"],
        "redis": redis_health["status"],
        "external_apis": apis_health["status"]
    }
    
    # Calculate overall status
    overall_status = "operational"
    if any(status == "unhealthy" for status in dependencies.values()):
        overall_status = "degraded"
    
    return StatusResponse(
        status=overall_status,
        service="settlers-of-stock-api",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        environment=settings.environment,
        uptime="0m",  # Placeholder - would calculate actual uptime
        dependencies=dependencies
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )