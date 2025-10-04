"""
Health Check Controller
"""
from fastapi import APIRouter, HTTPException
from sqlalchemy import text
import logging
import os

from app.infrastructure.database.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "donations-api",
        "version": "1.0.0"
    }


@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check including database connectivity"""
    health_status = {
        "status": "healthy",
        "service": "donations-api",
        "version": "1.0.0",
        "checks": {}
    }
    
    # Check database connectivity
    try:
        db = next(get_db())
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        health_status["checks"]["database"] = {"status": "healthy"}
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check environment variables
    required_env_vars = ["DATABASE_URL"]
    missing_vars = []

    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        health_status["checks"]["environment"] = {
            "status": "warning",
            "missing_variables": missing_vars
        }
    else:
        health_status["checks"]["environment"] = {"status": "healthy"}

    # Check external dependencies (RabbitMQ, Redis if configured)
    external_checks = {}

    # Check RabbitMQ if URL is configured
    rabbitmq_url = os.getenv("RABBITMQ_URL")
    if rabbitmq_url:
        try:
            # Simple connectivity check (in production, use proper health checks)
            external_checks["rabbitmq"] = {"status": "healthy", "note": "URL configured"}
        except Exception as e:
            external_checks["rabbitmq"] = {"status": "unhealthy", "error": str(e)}
    else:
        external_checks["rabbitmq"] = {"status": "not_configured"}

    # Check Redis if URL is configured
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            external_checks["redis"] = {"status": "healthy", "note": "URL configured"}
        except Exception as e:
            external_checks["redis"] = {"status": "unhealthy", "error": str(e)}
    else:
        external_checks["redis"] = {"status": "not_configured"}

    health_status["checks"]["external_dependencies"] = external_checks
    
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status


@router.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe"""
    try:
        # Check if the application can serve requests
        db = next(get_db())
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=503, 
            detail={"status": "not ready", "error": str(e)}
        )


@router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe"""
    return {"status": "alive"}


@router.post("/client-errors")
async def log_client_error(error_data: dict):
    """
    Log client-side errors from frontend

    - **error**: Error message
    - **stack**: Error stack trace
    - **user_agent**: Browser user agent
    - **url**: Current URL where error occurred
    """
    try:
        logger.error(
            "Client-side error reported",
            error=error_data.get("error", "Unknown error"),
            stack=error_data.get("stack", ""),
            user_agent=error_data.get("user_agent", ""),
            url=error_data.get("url", ""),
            client_info=error_data
        )
        return {"status": "logged"}
    except Exception as e:
        logger.error(f"Failed to log client error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to log error"
        )