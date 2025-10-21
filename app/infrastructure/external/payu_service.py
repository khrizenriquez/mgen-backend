"""
PayU Service - Payment gateway integration
Handles payment creation, status checking, and webhook processing
"""
import asyncio
import hashlib
import hmac
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional, Any, Tuple
from decimal import Decimal

import httpx
from pydantic import BaseModel

from app.infrastructure.logging import get_logger
from app.infrastructure.external.payu_config import PayUConfig
from app.domain.entities.donation import DonationStatus

logger = get_logger(__name__)


class PayUPaymentRequest(BaseModel):
    """Request model for creating a PayU payment"""
    reference_code: str
    amount: Decimal
    currency: str
    description: str
    buyer_email: str
    buyer_name: str
    buyer_document: Optional[str] = None
    response_url: str
    confirmation_url: str


class PayUPaymentResponse(BaseModel):
    """Response model from PayU payment creation"""
    transaction_id: str
    order_id: str
    payment_url: str
    status: str


class PayUStatusResponse(BaseModel):
    """Response model for payment status"""
    transaction_id: str
    order_id: str
    status: str
    payment_method: Optional[str] = None
    payment_method_name: Optional[str] = None


class PayUService:
    """
    PayU Payment Service
    Handles all interactions with PayU payment gateway
    """

    def __init__(self):
        self.config = PayUConfig()
        self.client = httpx.AsyncClient(
            timeout=self.config.REQUEST_TIMEOUT,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def _generate_signature(self, reference_code: str, amount: str, currency: str) -> str:
        """
        Generate PayU signature for payment validation
        Formula: ApiKey~merchantId~referenceCode~amount~currency
        """
        data = f"{self.config.API_KEY}~{self.config.MERCHANT_ID}~{reference_code}~{amount}~{currency}"
        signature = hashlib.md5(data.encode('utf-8')).hexdigest()
        return signature

    def _generate_order_id(self) -> str:
        """Generate unique order ID for PayU"""
        timestamp = int(time.time() * 1000)
        return f"ORDER_{timestamp}_{uuid.uuid4().hex[:8].upper()}"

    async def _make_request(self, endpoint: str, payload: Dict[str, Any], max_retries: int = None) -> Dict[str, Any]:
        """Make authenticated request to PayU API with retry logic"""
        if max_retries is None:
            max_retries = self.config.MAX_RETRIES

        url = self.config.get_api_url(endpoint)
        last_error = None

        for attempt in range(max_retries):
            try:
                logger.info(
                    "Making PayU API request",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    endpoint=endpoint,
                    url=url
                )

                response = await self.client.post(url, json=payload)

                # Log response for debugging
                logger.info(
                    "PayU API response received",
                    status_code=response.status_code,
                    attempt=attempt + 1
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("code") == "SUCCESS":
                        return data
                    else:
                        error_message = data.get("error", "Unknown PayU error")
                        logger.error("PayU API error response", error=error_message, data=data)
                        raise Exception(f"PayU API error: {error_message}")

                elif response.status_code >= 500:
                    # Server error, retry
                    last_error = f"HTTP {response.status_code}: {response.text}"
                    if attempt < max_retries - 1:
                        await asyncio.sleep(self.config.RETRY_DELAY * (attempt + 1))
                        continue
                else:
                    # Client error, don't retry
                    last_error = f"HTTP {response.status_code}: {response.text}"
                    break

            except httpx.TimeoutException as e:
                last_error = f"Timeout: {str(e)}"
                if attempt < max_retries - 1:
                    await asyncio.sleep(self.config.RETRY_DELAY * (attempt + 1))
                    continue
                break
            except Exception as e:
                last_error = str(e)
                break

        logger.error("PayU API request failed after all retries", error=last_error)
        raise Exception(f"PayU API request failed: {last_error}")

    async def create_payment(self, payment_request: PayUPaymentRequest) -> PayUPaymentResponse:
        """
        Create a payment request in PayU
        Returns payment URL for user to complete payment
        """
        try:
            logger.info(
                "Creating PayU payment",
                reference_code=payment_request.reference_code,
                amount=str(payment_request.amount),
                currency=payment_request.currency,
                buyer_email=payment_request.buyer_email
            )

            # Generate signature
            signature = self._generate_signature(
                payment_request.reference_code,
                f"{payment_request.amount:.2f}",
                payment_request.currency
            )

            # Generate order ID
            order_id = self._generate_order_id()

            # Build payment payload
            payload = {
                "language": "es",
                "command": "SUBMIT_TRANSACTION",
                "merchant": {
                    "apiKey": self.config.API_KEY,
                    "apiLogin": self.config.API_LOGIN
                },
                "transaction": {
                    "order": {
                        "accountId": self.config.get_account_id(),
                        "referenceCode": payment_request.reference_code,
                        "description": payment_request.description,
                        "language": "es",
                        "signature": signature,
                        "notifyUrl": payment_request.confirmation_url,
                        "additionalValues": {
                            "TX_VALUE": {
                                "value": float(payment_request.amount),
                                "currency": payment_request.currency
                            }
                        },
                        "buyer": {
                            "merchantBuyerId": payment_request.buyer_email,
                            "fullName": payment_request.buyer_name,
                            "emailAddress": payment_request.buyer_email,
                            "dniNumber": payment_request.buyer_document or "",
                            "shippingAddress": {
                                "street1": "N/A",
                                "city": "N/A",
                                "state": "N/A",
                                "country": self.config.COUNTRY_CODE,
                                "postalCode": "00000",
                                "phone": ""
                            }
                        }
                    },
                    "type": "AUTHORIZATION_AND_CAPTURE",
                    "paymentMethod": "N/A",  # Let user choose on PayU page
                    "paymentCountry": self.config.COUNTRY_CODE,
                    "deviceSessionId": str(uuid.uuid4()),
                    "ipAddress": "127.0.0.1",  # Will be overridden by actual IP
                    "cookie": str(uuid.uuid4()),
                    "userAgent": "Donations System API"
                },
                "test": self.config.TEST_MODE
            }

            # Make API request
            response_data = await self._make_request("", payload)

            # Extract transaction info
            transaction = response_data.get("transactionResponse", {})
            transaction_id = transaction.get("transactionId", "")
            state = transaction.get("state", "")

            # Check if payment was successfully created
            if state != "PENDING":
                logger.warning(
                    "PayU payment creation returned unexpected state",
                    state=state,
                    transaction_id=transaction_id
                )

            # Generate payment URL
            payment_url = f"{self.config.PAYMENTS_URL}?merchantId={self.config.MERCHANT_ID}&referenceCode={payment_request.reference_code}&signature={signature}&accountId={self.config.get_account_id()}"

            payment_response = PayUPaymentResponse(
                transaction_id=transaction_id,
                order_id=order_id,
                payment_url=payment_url,
                status=state
            )

            logger.info(
                "PayU payment created successfully",
                transaction_id=transaction_id,
                order_id=order_id,
                payment_url=payment_url,
                status=state
            )

            return payment_response

        except Exception as e:
            logger.error(
                "Failed to create PayU payment",
                error=str(e),
                reference_code=payment_request.reference_code,
                amount=str(payment_request.amount)
            )
            raise

    async def get_payment_status(self, order_id: str) -> PayUStatusResponse:
        """
        Query payment status from PayU
        """
        try:
            logger.info("Querying PayU payment status", order_id=order_id)

            payload = {
                "language": "es",
                "command": "ORDER_DETAIL",
                "merchant": {
                    "apiKey": self.config.API_KEY,
                    "apiLogin": self.config.API_LOGIN
                },
                "details": {
                    "orderId": order_id
                },
                "test": self.config.TEST_MODE
            }

            response_data = await self._make_request("", payload)

            # Extract transaction details
            transactions = response_data.get("result", {}).get("payload", {}).get("transactions", [])
            if not transactions:
                raise Exception(f"No transaction found for order ID: {order_id}")

            transaction = transactions[0]
            transaction_id = transaction.get("id", "")
            state = transaction.get("state", "")

            # Map PayU status to our internal status
            status_mapping = {
                "APPROVED": "APPROVED",
                "DECLINED": "DECLINED",
                "PENDING": "PENDING",
                "EXPIRED": "EXPIRED",
                "ERROR": "DECLINED"
            }

            mapped_status = status_mapping.get(state, "UNKNOWN")

            status_response = PayUStatusResponse(
                transaction_id=transaction_id,
                order_id=order_id,
                status=mapped_status,
                payment_method=transaction.get("paymentMethod"),
                payment_method_name=transaction.get("paymentMethodName")
            )

            logger.info(
                "PayU payment status retrieved",
                order_id=order_id,
                transaction_id=transaction_id,
                status=mapped_status,
                payu_state=state
            )

            return status_response

        except Exception as e:
            logger.error(
                "Failed to get PayU payment status",
                error=str(e),
                order_id=order_id
            )
            raise

    def validate_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Validate webhook signature for security
        """
        if not self.config.WEBHOOK_SECRET:
            logger.warning("PayU webhook secret not configured, skipping signature validation")
            return True

        expected_signature = hmac.new(
            self.config.WEBHOOK_SECRET.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    async def process_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process PayU webhook notification
        Returns processed webhook data with validation results
        """
        try:
            logger.info("Processing PayU webhook", webhook_data=webhook_data)

            # Extract relevant data
            transaction = webhook_data.get("transaction", {})
            order_id = webhook_data.get("reference_sale", "")
            transaction_id = transaction.get("id", "")
            state = transaction.get("state", "")
            reference_code = webhook_data.get("reference_sale", "")

            # Validate signature if secret is configured
            signature_valid = True
            if self.config.WEBHOOK_SECRET:
                # Note: PayU webhook signature validation depends on implementation
                # This is a placeholder - adjust based on PayU webhook documentation
                signature_valid = True  # Implement actual validation

            # Map PayU state to our status
            status_mapping = {
                "APPROVED": DonationStatus.APPROVED.value,
                "DECLINED": DonationStatus.DECLINED.value,
                "PENDING": DonationStatus.PENDING.value,
                "EXPIRED": DonationStatus.EXPIRED.value,
                "ERROR": DonationStatus.DECLINED.value
            }

            internal_status = status_mapping.get(state, DonationStatus.PENDING.value)

            processed_data = {
                "reference_code": reference_code,
                "order_id": order_id,
                "transaction_id": transaction_id,
                "payu_state": state,
                "internal_status": internal_status,
                "signature_valid": signature_valid,
                "webhook_data": webhook_data,
                "processed_at": datetime.now(timezone.utc).isoformat()
            }

            logger.info(
                "PayU webhook processed successfully",
                reference_code=reference_code,
                order_id=order_id,
                payu_state=state,
                internal_status=internal_status,
                signature_valid=signature_valid
            )

            return processed_data

        except Exception as e:
            logger.error(
                "Failed to process PayU webhook",
                error=str(e),
                webhook_data=webhook_data
            )
            raise
