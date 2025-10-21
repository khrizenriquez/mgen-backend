"""
PayU Controller - HTTP API endpoints for PayU payment integration
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Query
from typing import Optional
from uuid import UUID

from app.infrastructure.logging import get_logger
from app.infrastructure.auth.dependencies import get_current_active_user
from app.infrastructure.database.models import UserModel
from app.infrastructure.external.payu_service import PayUService, PayUPaymentRequest
from app.infrastructure.external.payu_config import PayUConfig
from app.adapters.schemas.payu_schemas import (
    PayUPaymentCreateRequest,
    PayUPaymentResponse,
    PayUPaymentStatusRequest,
    PayUPaymentStatusResponse,
    PayUWebhookRequest,
    PayUWebhookResponse,
    PayUConfigStatus
)
from app.adapters.controllers.donation_controller import get_donation_repository
from app.infrastructure.database.repository_impl import SQLAlchemyDonationRepository
from app.infrastructure.database.database import get_db
from app.domain.entities.donation import DonationStatus

logger = get_logger(__name__)
router = APIRouter()


def get_payu_service() -> PayUService:
    """Dependency injection for PayU service"""
    return PayUService()


@router.post("/payments/create", response_model=PayUPaymentResponse)
async def create_payu_payment(
    payment_data: PayUPaymentCreateRequest,
    current_user: UserModel = Depends(get_current_active_user),
    donation_repo: SQLAlchemyDonationRepository = Depends(get_donation_repository),
    payu_service: PayUService = Depends(get_payu_service)
):
    """
    Create a PayU payment for an existing donation

    This endpoint:
    1. Validates the donation exists and belongs to current user (or admin)
    2. Checks donation status is PENDING
    3. Creates PayU payment request
    4. Returns payment URL for user to complete payment
    """
    try:
        logger.info(
            "Creating PayU payment",
            user_email=current_user.email,
            donation_id=payment_data.donation_id
        )

        # Parse donation ID
        try:
            donation_uuid = UUID(payment_data.donation_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid donation ID format")

        # Get donation
        donation = await donation_repo.get_by_id(donation_uuid)
        if not donation:
            raise HTTPException(status_code=404, detail="Donation not found")

        # Check permissions
        user_roles = [role.name for role in current_user.user_roles]
        is_admin = "ADMIN" in user_roles

        # Users can only pay for their own donations unless they're admin
        if not is_admin and donation.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You can only create payments for your own donations"
            )

        # Check donation status
        if donation.status_id != DonationStatus.PENDING.value:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot create payment for donation with status: {donation.status.name}"
            )

        # Prepare PayU payment request
        payu_request = PayUPaymentRequest(
            reference_code=donation.reference_code,
            amount=donation.amount_gtq,
            currency="GTQ",  # Guatemala Quetzal
            description=f"Donation from {donation.donor_name} - {donation.donor_email}",
            buyer_email=donation.donor_email,
            buyer_name=donation.donor_name or "Donor",
            buyer_document=donation.donor_nit,
            response_url=payment_data.response_url or "https://masgenerosidad.org/payment/complete",
            confirmation_url=payment_data.confirmation_url or "https://api.masgenerosidad.org/api/v1/webhooks/payu/confirmation"
        )

        # Create payment with PayU
        async with payu_service:
            payu_response = await payu_service.create_payment(payu_request)

        # Update donation with PayU order ID
        donation.payu_order_id = payu_response.order_id
        await donation_repo.update(donation)

        # Record payment event
        await _record_payment_event(
            donation.id,
            "payment_created",
            "webhook",  # Source is webhook since we're creating it
            DonationStatus.PENDING.value,
            {
                "payu_order_id": payu_response.order_id,
                "transaction_id": payu_response.transaction_id,
                "payment_url": payu_response.payment_url,
                "user_email": current_user.email
            }
        )

        response = PayUPaymentResponse(
            donation_id=str(donation.id),
            payu_order_id=payu_response.order_id,
            transaction_id=payu_response.transaction_id,
            payment_url=payu_response.payment_url,
            status=payu_response.status
        )

        logger.info(
            "PayU payment created successfully",
            donation_id=str(donation.id),
            payu_order_id=payu_response.order_id,
            transaction_id=payu_response.transaction_id
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error creating PayU payment",
            error=str(e),
            error_type=type(e).__name__,
            donation_id=payment_data.donation_id,
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to create PayU payment")


@router.get("/payments/status", response_model=PayUPaymentStatusResponse)
async def get_payment_status(
    donation_id: Optional[str] = Query(None, description="Donation ID"),
    payu_order_id: Optional[str] = Query(None, description="PayU order ID"),
    current_user: UserModel = Depends(get_current_active_user),
    donation_repo: SQLAlchemyDonationRepository = Depends(get_donation_repository),
    payu_service: PayUService = Depends(get_payu_service)
):
    """
    Get payment status from PayU

    Either donation_id or payu_order_id must be provided
    """
    try:
        if not donation_id and not payu_order_id:
            raise HTTPException(
                status_code=400,
                detail="Either donation_id or payu_order_id must be provided"
            )

        logger.info(
            "Getting payment status",
            user_email=current_user.email,
            donation_id=donation_id,
            payu_order_id=payu_order_id
        )

        # Get donation and validate permissions
        donation = None
        if donation_id:
            try:
                donation_uuid = UUID(donation_id)
                donation = await donation_repo.get_by_id(donation_uuid)
                if not donation:
                    raise HTTPException(status_code=404, detail="Donation not found")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid donation ID format")

        # Check permissions
        user_roles = [role.name for role in current_user.user_roles]
        is_admin = "ADMIN" in user_roles

        if donation and not is_admin and donation.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You can only check status for your own donations"
            )

        # Determine order ID to query
        order_id = payu_order_id
        if not order_id and donation:
            order_id = donation.payu_order_id

        if not order_id:
            raise HTTPException(
                status_code=400,
                detail="No PayU order ID found for this donation"
            )

        # Query PayU for status
        async with payu_service:
            status_response = await payu_service.get_payment_status(order_id)

        # Update donation status if we have the donation
        if donation:
            # Map PayU status to our internal status
            status_mapping = {
                "APPROVED": DonationStatus.APPROVED.value,
                "DECLINED": DonationStatus.DECLINED.value,
                "PENDING": DonationStatus.PENDING.value,
                "EXPIRED": DonationStatus.EXPIRED.value
            }

            new_status = status_mapping.get(status_response.status, DonationStatus.PENDING.value)

            # Only update if status changed
            if donation.status_id != new_status:
                old_status = donation.status_id
                donation.status_id = new_status

                if new_status == DonationStatus.APPROVED.value:
                    from datetime import datetime
                    donation.paid_at = datetime.utcnow()

                await donation_repo.update(donation)

                # Record status change event
                await _record_payment_event(
                    donation.id,
                    "status_updated",
                    "recon",  # Status check
                    new_status,
                    {
                        "old_status": old_status,
                        "new_status": new_status,
                        "payu_state": status_response.status,
                        "payment_method": status_response.payment_method,
                        "payment_method_name": status_response.payment_method_name
                    }
                )

                logger.info(
                    "Donation status updated from PayU status check",
                    donation_id=str(donation.id),
                    old_status=old_status,
                    new_status=new_status,
                    payu_state=status_response.status
                )

        response = PayUPaymentStatusResponse(
            donation_id=donation_id or str(donation.id) if donation else "",
            payu_order_id=status_response.order_id,
            transaction_id=status_response.transaction_id,
            status=status_response.status,
            payu_state=status_response.status,
            payment_method=status_response.payment_method,
            payment_method_name=status_response.payment_method_name,
            amount=donation.amount_gtq if donation else 0,
            currency="GTQ",
            updated_at=donation.updated_at if donation else datetime.utcnow()
        )

        logger.info(
            "Payment status retrieved successfully",
            donation_id=donation_id,
            payu_order_id=status_response.order_id,
            status=status_response.status
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting payment status",
            error=str(e),
            error_type=type(e).__name__,
            donation_id=donation_id,
            payu_order_id=payu_order_id,
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to get payment status")


@router.post("/webhooks/confirmation", response_model=PayUWebhookResponse)
async def payu_webhook_confirmation(
    request: Request,
    webhook_data: PayUWebhookRequest
):
    """
    Handle PayU webhook confirmations

    This endpoint receives automatic notifications from PayU
    when payment status changes
    """
    try:
        logger.info("Received PayU webhook", webhook_data=webhook_data.dict())

        # Get PayU service
        payu_service = PayUService()

        # Validate webhook signature if configured
        raw_body = await request.body()
        signature_valid = payu_service.validate_webhook_signature(
            raw_body.decode('utf-8'),
            webhook_data.sign
        )

        if not signature_valid:
            logger.warning("Invalid PayU webhook signature", reference_sale=webhook_data.reference_sale)
            # Still process but log the issue

        # Process webhook data
        async with payu_service:
            processed_data = await payu_service.process_webhook(webhook_data.dict())

        # Find donation by reference code
        db = await get_db()
        donation_repo = SQLAlchemyDonationRepository(db)
        donation = await donation_repo.get_by_reference_code(processed_data["reference_code"])

        if not donation:
            logger.warning(
                "Donation not found for PayU webhook",
                reference_code=processed_data["reference_code"]
            )
            raise HTTPException(status_code=404, detail="Donation not found")

        # Update donation status
        old_status = donation.status_id
        new_status = processed_data["internal_status"]

        if old_status != new_status:
            donation.status_id = new_status

            if new_status == DonationStatus.APPROVED.value:
                from datetime import datetime
                donation.paid_at = datetime.utcnow()

            await donation_repo.update(donation)

            logger.info(
                "Donation status updated from PayU webhook",
                donation_id=str(donation.id),
                reference_code=processed_data["reference_code"],
                old_status=old_status,
                new_status=new_status,
                payu_state=processed_data["payu_state"]
            )

        # Record webhook event
        await _record_payment_event(
            donation.id,
            "webhook_received",
            "webhook",
            new_status,
            {
                "webhook_data": processed_data["webhook_data"],
                "signature_valid": signature_valid,
                "payu_state": processed_data["payu_state"],
                "transaction_id": processed_data["transaction_id"]
            }
        )

        response = PayUWebhookResponse(
            success=True,
            message="Webhook processed successfully",
            reference_code=processed_data["reference_code"],
            transaction_id=processed_data["transaction_id"],
            status=DonationStatus(new_status).name,
            processed_at=datetime.fromisoformat(processed_data["processed_at"])
        )

        logger.info(
            "PayU webhook processed successfully",
            reference_code=processed_data["reference_code"],
            transaction_id=processed_data["transaction_id"],
            status=DonationStatus(new_status).name
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error processing PayU webhook",
            error=str(e),
            error_type=type(e).__name__,
            webhook_data=webhook_data.dict(),
            exc_info=True
        )
        # Return success to PayU to avoid retries
        return PayUWebhookResponse(
            success=False,
            message=f"Error processing webhook: {str(e)}",
            reference_code=webhook_data.reference_sale,
            transaction_id=webhook_data.transaction_id,
            status="ERROR",
            processed_at=datetime.utcnow()
        )


@router.get("/config/status", response_model=PayUConfigStatus)
async def get_payu_config_status():
    """
    Get PayU configuration status

    Useful for debugging and monitoring
    """
    try:
        config = PayUConfig()
        errors = config.validate_config()

        status = PayUConfigStatus(
            configured=len(errors) == 0,
            test_mode=config.TEST_MODE,
            country_code=config.COUNTRY_CODE,
            currency=config.CURRENCY,
            errors=errors
        )

        logger.info(
            "PayU config status requested",
            configured=status.configured,
            test_mode=status.test_mode,
            country_code=status.country_code,
            error_count=len(errors)
        )

        return status

    except Exception as e:
        logger.error(
            "Error getting PayU config status",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to get PayU config status")


async def _record_payment_event(donation_id: UUID, event_id: str, source: str, status_id: int, payload: dict):
    """Helper function to record payment events in database"""
    try:
        from app.infrastructure.database.database import get_db
        from app.infrastructure.database.models import PaymentEventModel
        from datetime import datetime

        db = await get_db()
        event = PaymentEventModel(
            donation_id=donation_id,
            event_id=event_id,
            source=source,
            status_id=status_id,
            payload_raw=payload,
            received_at=datetime.utcnow()
        )
        db.add(event)
        await db.commit()

    except Exception as e:
        logger.error(
            "Failed to record payment event",
            error=str(e),
            donation_id=str(donation_id),
            event_id=event_id
        )
