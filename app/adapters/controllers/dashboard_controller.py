"""
Dashboard Controller - HTTP API endpoints for dashboard data
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.adapters.schemas.dashboard_schemas import (
    DashboardStats, DonorDashboardStats, UserDashboardStats, DashboardResponse
)
from app.domain.services.dashboard_service import DashboardService
from app.infrastructure.database.database import get_db
from app.infrastructure.auth.dependencies import (
    get_current_active_user, require_admin, require_any_role
)
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


def get_dashboard_service(db: Session = Depends(get_db)) -> DashboardService:
    """Dependency injection for dashboard service"""
    return DashboardService(db)


@router.get("/dashboard/stats", response_model=DashboardResponse)
async def get_dashboard_stats(
    current_user = Depends(get_current_active_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get dashboard statistics based on user role

    Returns different data based on user permissions:
    - ADMIN: Full system statistics + recent users/donations
    - DONOR: Personal donation statistics
    - USER: Basic system statistics
    """
    try:
        logger.info("Fetching dashboard stats", user_email=current_user.email)

        # Check user roles
        user_roles = [user_role.role.name for user_role in current_user.user_roles]
        is_admin = "ADMIN" in user_roles
        is_donor = "DONOR" in user_roles

        stats = {}
        recent_activity = []

        if is_admin:
            # Admin gets full system stats
            stats = dashboard_service.get_admin_stats()
            stats["recent_users"] = dashboard_service.get_recent_users(limit=5)
            stats["recent_donations"] = dashboard_service.get_recent_donations(limit=5)

            # Add recent activity
            recent_activity = [
                {"type": "user_registered", "message": f"Nuevo usuario: {user['email']}", "timestamp": user["joined_at"]}
                for user in stats["recent_users"][:3]
            ] + [
                {"type": "donation_made", "message": f"Donación: Q{donation['amount_gtq']} por {donation['donor_email']}", "timestamp": donation["created_at"]}
                for donation in stats["recent_donations"][:3]
            ]

        elif is_donor:
            # Donor gets personal stats
            donor_stats = dashboard_service.get_donor_stats(str(current_user.id))
            donor_stats["my_donations"] = dashboard_service.get_user_donations(str(current_user.id), limit=5)
            stats = donor_stats

            # Add recent activity
            recent_activity = [
                {"type": "donation_made", "message": f"Tu donación: Q{donation['amount_gtq']}", "timestamp": donation["created_at"]}
                for donation in stats["my_donations"][:3]
            ]

        else:
            # Regular user gets basic system stats
            stats = dashboard_service.get_user_stats(str(current_user.id))

            # Add recent activity (system-wide)
            recent_donations = dashboard_service.get_recent_donations(limit=3)
            recent_activity = [
                {"type": "system_donation", "message": f"Donación en el sistema: Q{donation['amount_gtq']}", "timestamp": donation["created_at"]}
                for donation in recent_donations
            ]

        logger.info(
            "Dashboard stats retrieved successfully",
            user_email=current_user.email,
            stats_keys=list(stats.keys())
        )

        return DashboardResponse(
            stats=stats,
            recent_activity=recent_activity
        )

    except Exception as e:
        logger.error(
            "Error getting dashboard stats",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Error loading dashboard data")


@router.get("/admin/users/recent")
async def get_recent_users(
    limit: int = 10,
    current_user = Depends(require_admin),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get recent user registrations (Admin only)

    Requires ADMIN role.
    """
    try:
        logger.info("Fetching recent users", user_email=current_user.email, limit=limit)

        users = dashboard_service.get_recent_users(limit=limit)

        logger.info(f"Retrieved {len(users)} recent users")
        return {"users": users, "total": len(users)}

    except Exception as e:
        logger.error(f"Error getting recent users: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error loading recent users")


@router.get("/admin/donations/recent")
async def get_recent_donations(
    limit: int = 10,
    current_user = Depends(require_admin),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get recent donations (Admin only)

    Requires ADMIN role.
    """
    try:
        logger.info("Fetching recent donations", user_email=current_user.email, limit=limit)

        donations = dashboard_service.get_recent_donations(limit=limit)

        logger.info(f"Retrieved {len(donations)} recent donations")
        return {"donations": donations, "total": len(donations)}

    except Exception as e:
        logger.error(f"Error getting recent donations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error loading recent donations")


@router.get("/donor/my-donations")
async def get_my_donations(
    limit: int = 20,
    current_user = Depends(get_current_active_user),
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """
    Get current user's donations

    Requires authentication. Users can only see their own donations.
    """
    try:
        logger.info("Fetching user donations", user_email=current_user.email, limit=limit)

        # Check if user has DONOR role or is admin
        user_roles = [role.name for role in current_user.user_roles]
        if "DONOR" not in user_roles and "ADMIN" not in user_roles:
            raise HTTPException(
                status_code=403,
                detail="Only donors can access their donation history"
            )

        donations = dashboard_service.get_user_donations(str(current_user.id), limit=limit)

        logger.info(f"Retrieved {len(donations)} user donations")
        return {"donations": donations, "total": len(donations)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user donations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error loading donation history")