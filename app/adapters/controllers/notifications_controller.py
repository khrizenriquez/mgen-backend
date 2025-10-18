"""
Notifications controller with basic notification endpoints
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.adapters.schemas.auth_schemas import GenericResponse
from app.infrastructure.auth.dependencies import get_current_active_user
from app.infrastructure.database.database import get_db
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
    responses={404: {"description": "Not found"}},
)


# Mock notification data - in a real app this would come from database
MOCK_NOTIFICATIONS = [
    {
        "id": 1,
        "title": "Bienvenido a Yo Me Uno",
        "message": "Gracias por registrarte en nuestra plataforma de donaciones.",
        "type": "welcome",
        "read": False,
        "created_at": "2025-01-15T10:00:00Z"
    },
    {
        "id": 2,
        "title": "Tu donación fue procesada",
        "message": "Tu donación de Q500 ha sido aprobada exitosamente.",
        "type": "donation",
        "read": True,
        "created_at": "2025-01-14T15:30:00Z"
    },
    {
        "id": 3,
        "title": "Nuevo programa disponible",
        "message": "Descubre nuestro nuevo programa de apoyo educativo.",
        "type": "program",
        "read": False,
        "created_at": "2025-01-13T09:15:00Z"
    }
]


@router.get("/")
async def get_notifications(
    current_user = Depends(get_current_active_user),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of notifications to return"),
    offset: int = Query(0, ge=0, description="Number of notifications to skip"),
    unread_only: bool = Query(False, description="Return only unread notifications")
):
    """
    Get user notifications

    Returns a paginated list of user notifications.
    """
    # Filter notifications based on parameters
    notifications = MOCK_NOTIFICATIONS.copy()

    if unread_only:
        notifications = [n for n in notifications if not n["read"]]

    # Apply pagination
    total = len(notifications)
    notifications = notifications[offset:offset + limit]

    return {
        "notifications": notifications,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.put("/{notification_id}/read", response_model=GenericResponse)
async def mark_notification_read(
    notification_id: int,
    current_user = Depends(get_current_active_user)
):
    """
    Mark a notification as read

    Updates the read status of a specific notification.
    """
    # In a real implementation, this would update the database
    # For now, just return success
    return GenericResponse(message="Notification marked as read")


@router.post("/test-notification", response_model=GenericResponse)
async def send_test_notification(
    current_user = Depends(get_current_active_user)
):
    """
    Send a test notification to the current user

    This endpoint is for testing purposes only.
    """
    # In a real implementation, this would create a notification in the database
    # and potentially send it via email/push notification
    logger.info(f"Sending test notification to user {current_user.email}")

    return GenericResponse(message="Test notification sent successfully")


@router.get("/unread-count")
async def get_unread_count(
    current_user = Depends(get_current_active_user)
):
    """
    Get count of unread notifications

    Returns the number of unread notifications for the current user.
    """
    # Count unread notifications
    unread_count = len([n for n in MOCK_NOTIFICATIONS if not n["read"]])

    return {
        "unread_count": unread_count
    }
