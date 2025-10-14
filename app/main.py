"""
Main FastAPI application with hexagonal architecture
"""
# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

import os
import sys
import subprocess
from pathlib import Path

# Validate configuration before starting (only in development)
if os.getenv("ENVIRONMENT", "development") == "development":
    print("🔍 Running configuration validation...")
    result = subprocess.run([sys.executable, "scripts/validate_config.py"],
                           capture_output=True, text=True, cwd=Path(__file__).parent.parent)

    if result.returncode != 0:
        print("❌ Configuration validation failed!")
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        sys.exit(1)
    else:
        print("✅ Configuration validation passed!")
else:
    print("⚡ Production mode - skipping configuration validation script")

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import time
import logging
import os
import structlog
from datetime import datetime

# Apitally monitoring (optional - only if configured and available)
APITALLY_AVAILABLE = False
ApitallyMiddleware = None

apitally_client_id = os.getenv("APITALLY_CLIENT_ID")
if apitally_client_id:
    try:
        # Try to import apitally dynamically
        from apitally.fastapi import ApitallyMiddleware
        APITALLY_AVAILABLE = True
        print("✅ Apitally package available")
    except ImportError:
        print("⚠️  Apitally package not installed - run 'pip install apitally[fastapi]' to enable monitoring")
else:
    print("📊 Apitally not configured (optional)")

from app.adapters.controllers.auth_controller import router as auth_router
from app.adapters.controllers.dashboard_controller import router as dashboard_router
from app.adapters.controllers.donation_controller import router as donation_router
from app.adapters.controllers.health_controller import router as health_router
from app.adapters.controllers.organization_controller import router as organization_router
from app.adapters.controllers.user_controller import router as user_router
from app.infrastructure.database.database import engine, Base
from app.infrastructure.database.seeders import run_seeders
from app.infrastructure.logging import setup_logging, get_logger, LoggingMiddleware
from app.infrastructure.middleware.rate_limit import RateLimitMiddleware
from app.infrastructure.monitoring import (
    REQUEST_COUNT, REQUEST_DURATION, USER_REGISTRATION_COUNT,
    LOGIN_ATTEMPTS, DONATION_COUNT, ACTIVE_USERS, DATABASE_CONNECTIONS
)
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

# Setup structured logging
setup_logging()
logger = get_logger(__name__)

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

# Apitally monitoring middleware (enabled for Railway and production)
if APITALLY_AVAILABLE and apitally_client_id:
    try:
        apitally_env = os.getenv("APITALLY_ENV", "prod")

        # Use only basic parameters compatible with Railway's Apitally version
        app.add_middleware(
            ApitallyMiddleware,
            client_id=apitally_client_id,
            env=apitally_env,
        )
        print(f"📊 Apitally monitoring enabled (env: {apitally_env})")
    except Exception as e:
        print(f"⚠️  Failed to initialize Apitally monitoring: {e}")
        print("📊 Continuing without Apitally monitoring")
elif apitally_client_id and not APITALLY_AVAILABLE:
    print("⚠️  APITALLY_CLIENT_ID configured but apitally package not available")
else:
    print("📊 Apitally not configured")

# Rate limiting middleware (before CORS for auth endpoints)
app.add_middleware(
    RateLimitMiddleware,
    max_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "10")),
    window_seconds=int(os.getenv("RATE_LIMIT_WINDOW", "60"))
)

# CORS middleware - Restrictive configuration for security
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
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
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(process_time)
    response.headers["X-Process-Time"] = str(process_time)
    
    return response

# Create database tables
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup with retry until DB is ready"""
    try:
        logger.info("Starting application startup sequence...")

        # Increased retries and wait time for Railway deployments
        max_retries = int(os.getenv("DB_STARTUP_MAX_RETRIES", "60"))
        wait_seconds = float(os.getenv("DB_STARTUP_WAIT_SECONDS", "5"))

        logger.info(f"Attempting database connection (max_retries: {max_retries}, wait_seconds: {wait_seconds})")

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Database connection attempt {attempt}/{max_retries}")
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                # Create all tables
                Base.metadata.create_all(bind=engine)
                logger.info("Database connected and tables ensured")

                # Update database connections metric
                try:
                    with engine.connect() as conn:
                        result = conn.execute(text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"))
                        active_connections = result.fetchone()[0]
                        DATABASE_CONNECTIONS.set(active_connections)
                        logger.info(f"Database connections metric updated: {active_connections}")
                except Exception as e:
                    logger.warning(f"Could not update database connections metric: {e}")

                # Run seeders only in development mode
                if os.getenv("ENVIRONMENT") == "development":
                    logger.info("Running database seeders...")
                    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
                    db = SessionLocal()
                    try:
                        run_seeders(db)
                    except Exception as e:
                        logger.error(f"Error running seeders: {e}")
                    finally:
                        db.close()

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
    except Exception as e:
        logger.error(f"Critical error during startup: {e}")
        logger.error("Application startup failed, but continuing to serve requests")
        # Don't re-raise - allow app to start even with startup errors

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Application shutting down")

# Include routers
logger.info("Including API routers...")
app.include_router(health_router)
app.include_router(auth_router, prefix="/api/v1", tags=["authentication"])
app.include_router(dashboard_router, prefix="/api/v1", tags=["dashboard"])
app.include_router(organization_router, prefix="/api/v1", tags=["organizations"])
app.include_router(donation_router, prefix="/api/v1", tags=["donations"])
# app.include_router(user_router, prefix="/api/v1", tags=["users"])
logger.info("All routers included successfully")

# Debug endpoint to verify app is responding
@app.get("/debug")
async def debug():
    """Debug endpoint to verify application is responding"""
    logger.info("Debug endpoint called - application is alive")
    return {
        "status": "ok",
        "message": "Application is responding correctly",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "donations-api"
    }

# Metrics endpoint for Prometheus
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Business metrics endpoint (less frequent updates)
@app.get("/metrics/business")
async def business_metrics():
    """Business-specific metrics endpoint for slower-refreshing data"""
    try:
        # Import here to avoid circular imports
        from app.infrastructure.monitoring.business_metrics import generate_business_metrics

        business_data = await generate_business_metrics()
        return JSONResponse(content=business_data, media_type="application/json")
    except Exception as e:
        logger.error("Error generating business metrics", error=str(e))
        return JSONResponse(
            content={"error": "Failed to generate business metrics"},
            status_code=500
        )

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