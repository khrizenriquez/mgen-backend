"""
Logging middleware for request correlation and unified access logging
"""
import time
import uuid
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .config import get_logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for adding correlation IDs and logging HTTP requests/responses
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.logger = get_logger("middleware.logging")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add logging context
        
        Args:
            request: The incoming HTTP request
            call_next: The next middleware/endpoint in the chain
            
        Returns:
            HTTP response with correlation headers
        """
        # Generate or extract correlation ID
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        
        # Skip logging for health checks and metrics endpoints to reduce log volume
        skip_paths = {"/health", "/health/", "/metrics", "/metrics/"}
        should_log = request.url.path not in skip_paths
        
        # Add to structlog context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            user_agent=request.headers.get("user-agent", ""),
            remote_addr=self._get_client_ip(request)
        )
        
        # Start timing
        start_time = time.time()
        
        # Log incoming request (skip health checks and metrics)
        if should_log:
            self.logger.info(
                "Request started",
                method=request.method,
                path=request.url.path,
                query_params=str(request.query_params) if request.query_params else None,
                user_agent=request.headers.get("user-agent", ""),
                remote_addr=self._get_client_ip(request),
                request_id=request_id
            )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate latency
            latency_ms = round((time.time() - start_time) * 1000, 2)
            
            # Add correlation ID to response headers
            response.headers["x-request-id"] = request_id
            
            # Log successful response (skip health checks and metrics)
            if should_log:
                self.logger.info(
                    "Request completed",
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    latency_ms=latency_ms,
                    request_id=request_id
                )
            
            return response
            
        except Exception as exc:
            # Calculate latency for failed requests too
            latency_ms = round((time.time() - start_time) * 1000, 2)
            
            # Log error
            self.logger.error(
                "Request failed",
                method=request.method,
                path=request.url.path,
                latency_ms=latency_ms,
                error=str(exc),
                error_type=type(exc).__name__,
                request_id=request_id,
                exc_info=True
            )
            
            # Re-raise the exception to be handled by FastAPI
            raise
        
        finally:
            # Clear context variables after request
            structlog.contextvars.clear_contextvars()
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request headers
        
        Args:
            request: The HTTP request
            
        Returns:
            Client IP address
        """
        # Check for forwarded headers (common in load balancers)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct client address
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"


class AccessLogFormatter:
    """
    Formatter for unified access logs in JSON format
    """
    
    @staticmethod
    def format_access_log(
        method: str,
        path: str,
        status_code: int,
        latency_ms: float,
        request_id: str,
        user_agent: str = "",
        remote_addr: str = "",
        user_id: str = None
    ) -> dict:
        """
        Format access log entry
        
        Args:
            method: HTTP method
            path: Request path
            status_code: HTTP status code
            latency_ms: Request latency in milliseconds
            request_id: Correlation ID
            user_agent: User agent string
            remote_addr: Client IP address
            user_id: Authenticated user ID if available
            
        Returns:
            Formatted log entry as dictionary
        """
        return {
            "type": "access",
            "method": method,
            "path": path,
            "status_code": status_code,
            "latency_ms": latency_ms,
            "request_id": request_id,
            "user_agent": user_agent,
            "remote_addr": remote_addr,
            "user_id": user_id
        }
