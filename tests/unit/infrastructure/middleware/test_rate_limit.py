"""
Unit tests for rate limiting middleware
"""
import pytest
import time
from unittest.mock import Mock, AsyncMock
from fastapi import HTTPException, Request

from app.infrastructure.middleware.rate_limit import RateLimitMiddleware


@pytest.fixture
def rate_limit_middleware():
    """Rate limit middleware instance with default settings"""
    return RateLimitMiddleware(None, max_requests=5, window_seconds=60)


@pytest.fixture
def mock_request():
    """Mock FastAPI request"""
    request = Mock(spec=Request)
    request.client = Mock()
    request.client.host = "192.168.1.100"
    request.headers = {}
    return request


@pytest.fixture
def mock_call_next():
    """Mock call_next function"""
    return AsyncMock(return_value=Mock())


class TestRateLimitMiddlewareInit:
    """Test middleware initialization"""

    def test_init_default_values(self):
        """Test initialization with default values"""
        middleware = RateLimitMiddleware(None)

        assert middleware.max_requests == 10
        assert middleware.window_seconds == 60
        assert isinstance(middleware.requests, dict)

    def test_init_custom_values(self):
        """Test initialization with custom values"""
        middleware = RateLimitMiddleware(None, max_requests=20, window_seconds=120)

        assert middleware.max_requests == 20
        assert middleware.window_seconds == 120
        assert isinstance(middleware.requests, dict)


class TestRateLimitMiddlewareGetClientIP:
    """Test client IP extraction functionality"""

    def test_get_client_ip_x_forwarded_for(self, rate_limit_middleware, mock_request):
        """Test getting IP from X-Forwarded-For header"""
        mock_request.headers = {"X-Forwarded-For": "203.0.113.1, 198.51.100.1"}

        ip = rate_limit_middleware._get_client_ip(mock_request)

        assert ip == "203.0.113.1"

    def test_get_client_ip_x_real_ip(self, rate_limit_middleware, mock_request):
        """Test getting IP from X-Real-IP header"""
        mock_request.headers = {"X-Real-IP": "198.51.100.1"}

        ip = rate_limit_middleware._get_client_ip(mock_request)

        assert ip == "198.51.100.1"

    def test_get_client_ip_fallback_to_client_host(self, rate_limit_middleware, mock_request):
        """Test fallback to client host when no headers"""
        mock_request.headers = {}

        ip = rate_limit_middleware._get_client_ip(mock_request)

        assert ip == "192.168.1.100"

    def test_get_client_ip_no_client(self, rate_limit_middleware, mock_request):
        """Test handling when request.client is None"""
        mock_request.client = None

        ip = rate_limit_middleware._get_client_ip(mock_request)

        assert ip == "unknown"

    def test_get_client_ip_multiple_x_forwarded_for(self, rate_limit_middleware, mock_request):
        """Test handling multiple IPs in X-Forwarded-For"""
        mock_request.headers = {"X-Forwarded-For": "203.0.113.1, 198.51.100.1, 192.0.2.1"}

        ip = rate_limit_middleware._get_client_ip(mock_request)

        assert ip == "203.0.113.1"


class TestRateLimitMiddlewareDispatch:
    """Test main dispatch functionality"""

    @pytest.mark.asyncio
    async def test_dispatch_under_limit(self, rate_limit_middleware, mock_request, mock_call_next):
        """Test request processing when under rate limit"""
        mock_response = Mock()
        mock_call_next.return_value = mock_response

        response = await rate_limit_middleware.dispatch(mock_request, mock_call_next)

        assert response == mock_response
        mock_call_next.assert_called_once_with(mock_request)

        # Check that request was recorded
        client_ip = rate_limit_middleware._get_client_ip(mock_request)
        assert client_ip in rate_limit_middleware.requests
        assert len(rate_limit_middleware.requests[client_ip]) == 1

    @pytest.mark.asyncio
    async def test_dispatch_at_limit_boundary(self, rate_limit_middleware, mock_request, mock_call_next):
        """Test request processing exactly at limit"""
        # Set up 4 previous requests (limit is 5)
        client_ip = rate_limit_middleware._get_client_ip(mock_request)
        current_time = time.time()
        rate_limit_middleware.requests[client_ip] = [
            current_time - 30, current_time - 20, current_time - 10, current_time - 5
        ]

        mock_response = Mock()
        mock_call_next.return_value = mock_response

        response = await rate_limit_middleware.dispatch(mock_request, mock_call_next)

        assert response == mock_response
        assert len(rate_limit_middleware.requests[client_ip]) == 5

    @pytest.mark.asyncio
    async def test_dispatch_over_limit(self, rate_limit_middleware, mock_request, mock_call_next):
        """Test rate limit exceeded"""
        # Set up 5 requests already (at limit)
        client_ip = rate_limit_middleware._get_client_ip(mock_request)
        current_time = time.time()
        rate_limit_middleware.requests[client_ip] = [
            current_time - 50, current_time - 40, current_time - 30,
            current_time - 20, current_time - 10
        ]

        with pytest.raises(HTTPException) as exc_info:
            await rate_limit_middleware.dispatch(mock_request, mock_call_next)

        assert exc_info.value.status_code == 429
        assert "Too many requests" in str(exc_info.value.detail)
        mock_call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_dispatch_cleans_old_requests(self, rate_limit_middleware, mock_request, mock_call_next):
        """Test that old requests are cleaned up"""
        client_ip = rate_limit_middleware._get_client_ip(mock_request)

        # Add some old requests (beyond window)
        old_time = time.time() - 120  # 2 minutes ago, window is 60 seconds
        rate_limit_middleware.requests[client_ip] = [old_time, old_time + 10, old_time + 20]

        mock_response = Mock()
        mock_call_next.return_value = mock_response

        response = await rate_limit_middleware.dispatch(mock_request, mock_call_next)

        assert response == mock_response
        # Old requests should be cleaned, only current one should remain
        assert len(rate_limit_middleware.requests[client_ip]) == 1

    @pytest.mark.asyncio
    async def test_dispatch_multiple_clients(self, rate_limit_middleware, mock_call_next):
        """Test rate limiting works independently per client"""
        # Create two different client requests
        request1 = Mock(spec=Request)
        request1.client = Mock()
        request1.client.host = "192.168.1.100"
        request1.headers = {}

        request2 = Mock(spec=Request)
        request2.client = Mock()
        request2.client.host = "192.168.1.101"
        request2.headers = {}

        mock_response = Mock()
        mock_call_next.return_value = mock_response

        # Both should succeed initially
        response1 = await rate_limit_middleware.dispatch(request1, mock_call_next)
        response2 = await rate_limit_middleware.dispatch(request2, mock_call_next)

        assert response1 == mock_response
        assert response2 == mock_response

        # Check separate tracking
        ip1 = rate_limit_middleware._get_client_ip(request1)
        ip2 = rate_limit_middleware._get_client_ip(request2)
        assert ip1 in rate_limit_middleware.requests
        assert ip2 in rate_limit_middleware.requests
        assert len(rate_limit_middleware.requests[ip1]) == 1
        assert len(rate_limit_middleware.requests[ip2]) == 1


class TestRateLimitMiddlewareEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.mark.asyncio
    async def test_dispatch_call_next_exception(self, rate_limit_middleware, mock_request, mock_call_next):
        """Test handling when call_next raises exception"""
        mock_call_next.side_effect = Exception("Internal error")

        with pytest.raises(Exception) as exc_info:
            await rate_limit_middleware.dispatch(mock_request, mock_call_next)

        assert str(exc_info.value) == "Internal error"

    def test_get_client_ip_empty_headers(self, rate_limit_middleware, mock_request):
        """Test IP extraction with empty headers"""
        mock_request.headers = {}

        ip = rate_limit_middleware._get_client_ip(mock_request)

        assert ip == "192.168.1.100"

    def test_get_client_ip_whitespace_in_forwarded_for(self, rate_limit_middleware, mock_request):
        """Test handling whitespace in X-Forwarded-For header"""
        mock_request.headers = {"X-Forwarded-For": "  203.0.113.1  ,  198.51.100.1  "}

        ip = rate_limit_middleware._get_client_ip(mock_request)

        assert ip == "203.0.113.1"


class TestRateLimitMiddlewareConfiguration:
    """Test different configuration scenarios"""

    @pytest.mark.asyncio
    async def test_high_limit_configuration(self):
        """Test middleware with high request limit"""
        middleware = RateLimitMiddleware(None, max_requests=100, window_seconds=300)
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "192.168.1.100"
        request.headers = {}
        call_next = AsyncMock(return_value=Mock())

        # Should allow many requests
        for i in range(50):
            response = await middleware.dispatch(request, call_next)
            assert response is not None

        # Check that requests are being tracked
        client_ip = middleware._get_client_ip(request)
        assert len(middleware.requests[client_ip]) == 50

    @pytest.mark.asyncio
    async def test_short_window_configuration(self):
        """Test middleware with short time window"""
        middleware = RateLimitMiddleware(None, max_requests=3, window_seconds=10)
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "192.168.1.100"
        request.headers = {}
        call_next = AsyncMock(return_value=Mock())

        # Should allow 3 requests quickly
        for i in range(3):
            response = await middleware.dispatch(request, call_next)
            assert response is not None

        # 4th request should be blocked
        with pytest.raises(HTTPException) as exc_info:
            await middleware.dispatch(request, call_next)

        assert exc_info.value.status_code == 429


class TestRateLimitMiddlewareIntegration:
    """Integration tests for rate limiting middleware"""

    def test_middleware_inheritance(self):
        """Test that middleware properly inherits from BaseHTTPMiddleware"""
        from starlette.middleware.base import BaseHTTPMiddleware

        middleware = RateLimitMiddleware(None)

        assert isinstance(middleware, BaseHTTPMiddleware)

    def test_requests_storage_isolation(self):
        """Test that requests storage is properly isolated between instances"""
        middleware1 = RateLimitMiddleware(None, max_requests=5)
        middleware2 = RateLimitMiddleware(None, max_requests=5)

        # Different instances should have separate storage
        assert middleware1.requests is not middleware2.requests

    @pytest.mark.asyncio
    async def test_time_based_cleanup(self):
        """Test that time-based cleanup works correctly"""
        middleware = RateLimitMiddleware(None, max_requests=3, window_seconds=2)  # 2 second window
        request = Mock(spec=Request)
        request.client = Mock()
        request.client.host = "192.168.1.100"
        request.headers = {}
        call_next = AsyncMock(return_value=Mock())

        # Make requests
        for i in range(3):
            await middleware.dispatch(request, call_next)

        # Wait longer than window
        import asyncio
        await asyncio.sleep(3)

        # Next request should succeed (old requests cleaned up)
        response = await middleware.dispatch(request, call_next)
        assert response is not None