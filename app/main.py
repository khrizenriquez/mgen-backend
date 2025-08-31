"""
Main FastAPI application with hexagonal architecture
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import time
import logging
import os
import structlog

from app.adapters.controllers.donation_controller import router as donation_router
from app.adapters.controllers.health_controller import router as health_router
from app.infrastructure.database.database import engine, Base
from app.infrastructure.logging import setup_logging, get_logger, LoggingMiddleware
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

# Setup structured logging
setup_logging()
logger = get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('donations_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('donations_request_duration_seconds', 'Request duration')

# Create FastAPI app
app = FastAPI(
    title="Donations Management System",
    description="A donation management system with hexagonal architecture",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add logging middleware first (before CORS)
app.add_middleware(LoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware for metrics
@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    
    # Count request
    REQUEST_COUNT.labels(
        method=request.method, 
        endpoint=request.url.path
    ).inc()
    
    response = await call_next(request)
    
    # Record duration
    process_time = time.time() - start_time
    REQUEST_DURATION.observe(process_time)
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# Create database tables
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup with retry until DB is ready"""
    max_retries = int(os.getenv("DB_STARTUP_MAX_RETRIES", "30"))
    wait_seconds = float(os.getenv("DB_STARTUP_WAIT_SECONDS", "2"))

    for attempt in range(1, max_retries + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            # Create all tables
            Base.metadata.create_all(bind=engine)
            logger.info("Database connected and tables ensured")
            break
        except OperationalError as e:
            logger.warning(
                f"Database not ready (attempt {attempt}/{max_retries}): {e}. "
                f"Retrying in {wait_seconds}s..."
            )
            time.sleep(wait_seconds)
        except Exception as e:
            logger.error(f"Unexpected error ensuring database: {e}")
            raise
    else:
        # Exhausted retries
        raise RuntimeError("Database not ready after retries. Startup aborted.")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Application shutting down")

# Include routers
app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(donation_router, prefix="/api/v1", tags=["donations"])

# Metrics endpoint for Prometheus
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Donations Management System API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with structured logging"""
    # Get request ID from headers if available
    request_id = request.headers.get("x-request-id", "unknown")
    
    # Log the exception with context
    logger.error(
        "Unhandled exception occurred",
        error=str(exc),
        error_type=type(exc).__name__,
        method=request.method,
        path=request.url.path,
        request_id=request_id,
        exc_info=True
    )
    
    # Return error response (don't expose internal details in production)
    if os.getenv("ENVIRONMENT", "development") == "development":
        detail = str(exc)
    else:
        detail = "An internal error occurred"
    
    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal server error", 
            "detail": detail,
            "request_id": request_id
        },
        headers={"x-request-id": request_id}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
        access_log=True,
        use_colors=False,  # Disable colors for better JSON logging
        log_config=None   # Use our custom logging config
    )