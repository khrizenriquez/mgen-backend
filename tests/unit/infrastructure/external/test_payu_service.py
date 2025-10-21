"""
Tests for PayU service
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal

from app.infrastructure.external.payu_service import PayUService, PayUPaymentRequest
from app.infrastructure.external.payu_config import PayUConfig


class TestPayUService:
    """Test PayU service functionality"""

    @pytest.fixture
    def payu_service(self):
        """Create PayU service instance"""
        return PayUService()

    @pytest.fixture
    def payment_request(self):
        """Create sample payment request"""
        return PayUPaymentRequest(
            reference_code="REF_TEST_123",
            amount=Decimal("100.00"),
            currency="GTQ",
            description="Test donation",
            buyer_email="test@example.com",
            buyer_name="Test User",
            buyer_document="123456789",
            response_url="https://example.com/complete",
            confirmation_url="https://api.example.com/webhook"
        )

    def test_generate_signature(self, payu_service):
        """Test signature generation"""
        signature = payu_service._generate_signature("REF123", "100.00", "GTQ")

        # MD5 hash should be generated
        assert isinstance(signature, str)
        assert len(signature) == 32  # MD5 hash length

    def test_generate_order_id(self, payu_service):
        """Test order ID generation"""
        order_id = payu_service._generate_order_id()

        assert order_id.startswith("ORDER_")
        assert len(order_id) > 10

    @patch('httpx.AsyncClient.post')
    async def test_create_payment_success(self, mock_post, payu_service, payment_request):
        """Test successful payment creation"""
        # Mock successful PayU response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "SUCCESS",
            "transactionResponse": {
                "transactionId": "test-transaction-123",
                "state": "PENDING"
            }
        }
        mock_post.return_value = mock_response

        async with payu_service:
            result = await payu_service.create_payment(payment_request)

        assert result.transaction_id == "test-transaction-123"
        assert result.status == "PENDING"
        assert "checkout.payulatam.com" in result.payment_url

    @patch('httpx.AsyncClient.post')
    async def test_create_payment_payu_error(self, mock_post, payu_service, payment_request):
        """Test payment creation with PayU API error"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "ERROR",
            "error": "Invalid payment data"
        }
        mock_post.return_value = mock_response

        async with payu_service:
            with pytest.raises(Exception, match="PayU API error"):
                await payu_service.create_payment(payment_request)

    @patch('httpx.AsyncClient.post')
    async def test_create_payment_http_error(self, mock_post, payu_service, payment_request):
        """Test payment creation with HTTP error"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        async with payu_service:
            with pytest.raises(Exception, match="PayU API request failed"):
                await payu_service.create_payment(payment_request)

    @patch('httpx.AsyncClient.post')
    async def test_get_payment_status_success(self, mock_post, payu_service):
        """Test successful payment status retrieval"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "SUCCESS",
            "result": {
                "payload": {
                    "transactions": [{
                        "id": "test-transaction-123",
                        "state": "APPROVED",
                        "paymentMethod": "VISA",
                        "paymentMethodName": "Visa"
                    }]
                }
            }
        }
        mock_post.return_value = mock_response

        async with payu_service:
            result = await payu_service.get_payment_status("ORDER123")

        assert result.transaction_id == "test-transaction-123"
        assert result.status == "APPROVED"
        assert result.payment_method == "VISA"

    @patch('httpx.AsyncClient.post')
    async def test_get_payment_status_not_found(self, mock_post, payu_service):
        """Test payment status for non-existent order"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": "SUCCESS",
            "result": {
                "payload": {
                    "transactions": []  # Empty transactions
                }
            }
        }
        mock_post.return_value = mock_response

        async with payu_service:
            with pytest.raises(Exception, match="No transaction found"):
                await payu_service.get_payment_status("ORDER123")

    def test_validate_webhook_signature_no_secret(self, payu_service):
        """Test webhook signature validation when no secret is configured"""
        # Should return True (skip validation) when no secret
        payu_service.config.WEBHOOK_SECRET = None
        result = payu_service.validate_webhook_signature("test_payload", "test_signature")
        assert result is True

    def test_validate_webhook_signature_with_secret(self, payu_service):
        """Test webhook signature validation with secret configured"""
        payu_service.config.WEBHOOK_SECRET = "test_secret"
        payload = "test_payload"
        # Generate a valid signature
        import hmac
        import hashlib
        expected_signature = hmac.new(
            "test_secret".encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        result = payu_service.validate_webhook_signature(payload, expected_signature)
        assert result is True

        # Test invalid signature
        result = payu_service.validate_webhook_signature(payload, "invalid_signature")
        assert result is False

    async def test_process_webhook_success(self, payu_service):
        """Test successful webhook processing"""
        webhook_data = {
            "reference_sale": "REF_TEST_123",
            "state_pol": "4",  # APPROVED
            "transaction_id": "test-transaction-123",
            "value": "100.00",
            "currency": "GTQ"
        }

        result = await payu_service.process_webhook(webhook_data)

        assert result["reference_code"] == "REF_TEST_123"
        assert result["transaction_id"] == "test-transaction-123"
        assert result["internal_status"] == 2  # APPROVED
        assert result["payu_state"] == "4"
        assert "processed_at" in result

    async def test_process_webhook_declined(self, payu_service):
        """Test webhook processing for declined payment"""
        webhook_data = {
            "reference_sale": "REF_TEST_123",
            "state_pol": "6",  # DECLINED
            "transaction_id": "test-transaction-123"
        }

        result = await payu_service.process_webhook(webhook_data)

        assert result["internal_status"] == 3  # DECLINED

    async def test_process_webhook_unknown_state(self, payu_service):
        """Test webhook processing for unknown state"""
        webhook_data = {
            "reference_sale": "REF_TEST_123",
            "state_pol": "99",  # Unknown state
            "transaction_id": "test-transaction-123"
        }

        result = await payu_service.process_webhook(webhook_data)

        assert result["internal_status"] == 1  # PENDING (default)

    @patch('httpx.AsyncClient.post')
    async def test_make_request_retry_on_failure(self, mock_post, payu_service):
        """Test that failed requests are retried"""
        # First call fails with 500, second succeeds
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 500
        mock_response_fail.text = "Server Error"

        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"code": "SUCCESS"}

        mock_post.side_effect = [mock_response_fail, mock_response_success]

        async with payu_service:
            result = await payu_service._make_request("test", {})

        assert result["code"] == "SUCCESS"
        assert mock_post.call_count == 2  # Should have retried once

    @patch('httpx.AsyncClient.post')
    async def test_make_request_max_retries_exceeded(self, mock_post, payu_service):
        """Test that requests fail after max retries"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        mock_post.return_value = mock_response

        async with payu_service:
            with pytest.raises(Exception, match="PayU API request failed"):
                await payu_service._make_request("test", {})

        assert mock_post.call_count == 3  # Max retries (default is 3)
