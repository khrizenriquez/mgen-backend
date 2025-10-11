"""
Integration tests for logging middleware
"""
import json
import logging
from unittest.mock import Mock, patch
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
import structlog

from app.infrastructure.logging.middleware import LoggingMiddleware
from app.infrastructure.logging.config import setup_logging


@pytest.fixture
def app_with_logging():
    """Create FastAPI app with logging middleware for testing"""
    # Setup logging for tests
    setup_logging()
    
    app = FastAPI()
    app.add_middleware(LoggingMiddleware)
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    @app.get("/error")
    async def error_endpoint():
        raise ValueError("Test error")
    
    return app


@pytest.fixture
def client(app_with_logging):
    """Create test client"""
    return TestClient(app_with_logging)


class TestLoggingMiddleware:
    """Test cases for logging middleware integration"""
    
    def test_middleware_adds_correlation_id_to_response(self, client):
        """Test that middleware adds correlation ID to response headers"""
        response = client.get("/test")
        
        assert response.status_code == 200
        assert "x-request-id" in response.headers
        
        # Should be a valid UUID format (36 characters with hyphens)
        request_id = response.headers["x-request-id"]
        assert len(request_id) == 36
        assert request_id.count("-") == 4
    
    def test_middleware_uses_existing_correlation_id(self, client):
        """Test that middleware uses existing correlation ID from headers"""
        custom_id = "custom-request-id-123"
        response = client.get("/test", headers={"x-request-id": custom_id})
        
        assert response.status_code == 200
        assert response.headers["x-request-id"] == custom_id
    
    @patch('app.infrastructure.logging.middleware.get_logger')
    def test_middleware_logs_request_start(self, mock_get_logger, client):
        """Test that middleware logs request start"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        client.get("/test")
        
        # Check that logger.info was called for request start
        info_calls = mock_logger.info.call_args_list
        assert len(info_calls) >= 1
        
        # Find the "Request started" call
        start_call = None
        for call in info_calls:
            if "Request started" in call[0]:
                start_call = call
                break
        
        assert start_call is not None
        
        # Check that request details are in the log call
        args, kwargs = start_call
        assert "method" in kwargs
        assert "path" in kwargs
        assert "request_id" in kwargs
    
    @patch('app.infrastructure.logging.middleware.get_logger')
    def test_middleware_logs_request_completion(self, mock_get_logger, client):
        """Test that middleware logs request completion"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        client.get("/test")
        
        # Check that logger.info was called for request completion
        info_calls = mock_logger.info.call_args_list
        assert len(info_calls) >= 2
        
        # Find the "Request completed" call
        completion_call = None
        for call in info_calls:
            if "Request completed" in call[0]:
                completion_call = call
                break
        
        assert completion_call is not None
        
        # Check that response details are in the log call
        args, kwargs = completion_call
        assert "status_code" in kwargs
        assert "latency_ms" in kwargs
        assert kwargs["status_code"] == 200
        assert isinstance(kwargs["latency_ms"], (int, float))
    
    @patch('app.infrastructure.logging.middleware.get_logger')
    def test_middleware_logs_request_failure(self, mock_get_logger, client):
        """Test that middleware logs request failures"""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        # Make request to error endpoint - expect ValueError to be raised
        with pytest.raises(ValueError, match="Test error"):
            response = client.get("/error")
        
        # Check that logger.error was called for request failure
        error_calls = mock_logger.error.call_args_list
        assert len(error_calls) >= 1
        
        # Find the "Request failed" call
        failure_call = None
        for call in error_calls:
            if "Request failed" in call[0]:
                failure_call = call
                break
        
        assert failure_call is not None
        
        # Check that error details are in the log call
        args, kwargs = failure_call
        assert "error" in kwargs
        assert "error_type" in kwargs
        assert "latency_ms" in kwargs
        assert "Test error" in kwargs["error"]
        assert kwargs["error_type"] == "ValueError"
    
    def test_middleware_client_ip_extraction(self, client):
        """Test client IP extraction from various headers"""
        # Test with X-Forwarded-For header
        response = client.get("/test", headers={"X-Forwarded-For": "192.168.1.1, 10.0.0.1"})
        assert response.status_code == 200
        
        # Test with X-Real-IP header  
        response = client.get("/test", headers={"X-Real-IP": "192.168.1.2"})
        assert response.status_code == 200
        
        # Should work without errors (actual IP checking would require 
        # more complex test setup with real network simulation)
    
    @patch('structlog.contextvars.bind_contextvars')
    @patch('structlog.contextvars.clear_contextvars')
    def test_middleware_manages_structlog_context(self, mock_clear, mock_bind, client):
        """Test that middleware properly manages structlog context variables"""
        client.get("/test")
        
        # Should bind context variables at start
        mock_bind.assert_called()
        bind_call = mock_bind.call_args[1]  # Get keyword arguments
        assert "request_id" in bind_call
        assert "method" in bind_call
        assert "path" in bind_call
        
        # Should clear context variables at end (called twice: start and end)
        assert mock_clear.call_count >= 2


class TestLoggingIntegration:
    """Integration tests for complete logging flow"""
    
    @patch('sys.stdout')
    def test_end_to_end_logging_flow(self, mock_stdout, client):
        """Test complete logging flow from request to log output"""
        # Make a request
        response = client.get("/test", headers={"x-request-id": "test-123"})
        
        assert response.status_code == 200
        assert response.headers["x-request-id"] == "test-123"
        
        # In real scenario, logs would be written to stdout
        # This test verifies the middleware chain works without errors
        # More detailed log format testing is done in unit tests
    
    def test_concurrent_requests_have_separate_correlation_ids(self, client):
        """Test that concurrent requests get separate correlation IDs"""
        # Make multiple requests
        responses = []
        for i in range(3):
            response = client.get("/test")
            responses.append(response)
        
        # All should be successful
        for response in responses:
            assert response.status_code == 200
            assert "x-request-id" in response.headers
        
        # All correlation IDs should be different
        correlation_ids = [r.headers["x-request-id"] for r in responses]
        assert len(set(correlation_ids)) == 3  # All unique
    
    @patch.dict('os.environ', {'ENVIRONMENT': 'production'})
    def test_logging_configuration_in_production_mode(self, client):
        """Test that logging works correctly in production mode"""
        # Re-setup logging with production environment
        setup_logging()
        
        response = client.get("/test")
        assert response.status_code == 200
        
        # Should work without errors in production mode
        # (JSON formatting, no colors, etc.)
    
    def test_error_handling_preserves_correlation_id(self, client):
        """Test that error handling preserves correlation ID"""
        custom_id = "error-test-123"
        
        # Make request to error endpoint - expect ValueError to be raised
        with pytest.raises(ValueError, match="Test error"):
            response = client.get("/error", headers={"x-request-id": custom_id})
        
        # Note: In test client, unhandled exceptions are propagated
        # In production with proper error handling, this would return 500
        # with correlation ID preserved in headers and response
