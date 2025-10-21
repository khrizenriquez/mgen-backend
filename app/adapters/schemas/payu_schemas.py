"""
PayU API Schemas - Request/Response models for PayU payment integration
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class PayUPaymentCreateRequest(BaseModel):
    """Request schema for creating a PayU payment"""
    donation_id: str = Field(..., description="ID of the donation to pay for")
    response_url: Optional[str] = Field(None, description="URL to redirect user after payment")
    confirmation_url: Optional[str] = Field(None, description="URL for PayU to send webhook confirmations")

    class Config:
        json_schema_extra = {
            "example": {
                "donation_id": "550e8400-e29b-41d4-a716-446655440000",
                "response_url": "https://masgenerosidad.org/payment/complete",
                "confirmation_url": "https://api.masgenerosidad.org/api/v1/webhooks/payu/confirmation"
            }
        }


class PayUPaymentResponse(BaseModel):
    """Response schema for PayU payment creation"""
    donation_id: str
    payu_order_id: str
    transaction_id: str
    payment_url: str
    status: str
    expires_at: Optional[datetime] = None

    class Config:
        json_schema_extra = {
            "example": {
                "donation_id": "550e8400-e29b-41d4-a716-446655440000",
                "payu_order_id": "ORDER_1703123456789_A1B2C3D4",
                "transaction_id": "abcd1234-5678-90ef-ghij-klmnopqrstuv",
                "payment_url": "https://sandbox.checkout.payulatam.com/...",
                "status": "PENDING",
                "expires_at": "2024-01-15T10:30:00Z"
            }
        }


class PayUPaymentStatusRequest(BaseModel):
    """Request schema for checking payment status"""
    donation_id: Optional[str] = Field(None, description="Donation ID to check")
    payu_order_id: Optional[str] = Field(None, description="PayU order ID to check")

    class Config:
        json_schema_extra = {
            "example": {
                "donation_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class PayUPaymentStatusResponse(BaseModel):
    """Response schema for payment status query"""
    donation_id: str
    payu_order_id: str
    transaction_id: str
    status: str
    payu_state: str
    payment_method: Optional[str] = None
    payment_method_name: Optional[str] = None
    amount: Decimal
    currency: str
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "donation_id": "550e8400-e29b-41d4-a716-446655440000",
                "payu_order_id": "ORDER_1703123456789_A1B2C3D4",
                "transaction_id": "abcd1234-5678-90ef-ghij-klmnopqrstuv",
                "status": "APPROVED",
                "payu_state": "APPROVED",
                "payment_method": "VISA",
                "payment_method_name": "Visa",
                "amount": 100.00,
                "currency": "GTQ",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }


class PayUWebhookRequest(BaseModel):
    """Request schema for PayU webhook notifications"""
    reference_sale: str = Field(..., description="Reference code from PayU")
    state_pol: str = Field(..., description="Transaction state")
    response_code_pol: str = Field(..., description="Response code")
    response_message_pol: str = Field(..., description="Response message")
    transaction_id: str = Field(..., description="Transaction ID")
    reference_pol: str = Field(..., description="Reference pol")
    payment_method_type: str = Field(..., description="Payment method type")
    payment_method_name: str = Field(..., description="Payment method name")
    payment_method_id: str = Field(..., description="Payment method ID")
    value: str = Field(..., description="Transaction value")
    currency: str = Field(..., description="Transaction currency")
    sign: str = Field(..., description="Digital signature")
    extra1: Optional[str] = Field(None, description="Extra field 1")
    extra2: Optional[str] = Field(None, description="Extra field 2")
    extra3: Optional[str] = Field(None, description="Extra field 3")

    class Config:
        json_schema_extra = {
            "example": {
                "reference_sale": "REF_123456789",
                "state_pol": "4",  # 4 = APPROVED
                "response_code_pol": "1",
                "response_message_pol": "APPROVED",
                "transaction_id": "abcd1234-5678-90ef-ghij-klmnopqrstuv",
                "reference_pol": "123456789",
                "payment_method_type": "2",
                "payment_method_name": "VISA",
                "payment_method_id": "1",
                "value": "100.00",
                "currency": "GTQ",
                "sign": "signature_hash_here",
                "extra1": "donation_id_here",
                "extra2": "",
                "extra3": ""
            }
        }


class PayUWebhookResponse(BaseModel):
    """Response schema for PayU webhook processing"""
    success: bool
    message: str
    reference_code: str
    transaction_id: str
    status: str
    processed_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Webhook processed successfully",
                "reference_code": "REF_123456789",
                "transaction_id": "abcd1234-5678-90ef-ghij-klmnopqrstuv",
                "status": "APPROVED",
                "processed_at": "2024-01-15T10:30:00Z"
            }
        }


class PayUConfigStatus(BaseModel):
    """Response schema for PayU configuration status"""
    configured: bool
    test_mode: bool
    country_code: str
    currency: str
    errors: list[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "configured": True,
                "test_mode": True,
                "country_code": "GT",
                "currency": "GTQ",
                "errors": []
            }
        }
