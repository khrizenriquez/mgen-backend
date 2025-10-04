"""
Dashboard Service - Business logic for dashboard data
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta

from app.infrastructure.database.models import UserModel, DonationModel, StatusCatalogModel
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class DashboardService:
    """Service for dashboard business logic"""

    def __init__(self, db: Session):
        self.db = db

    def get_admin_stats(self) -> Dict[str, Any]:
        """Get statistics for admin dashboard"""
        try:
            # Total users
            total_users = self.db.query(func.count(UserModel.id)).scalar()

            # Active users (not marked as inactive)
            active_users = self.db.query(func.count(UserModel.id)).filter(
                UserModel.is_active == True
            ).scalar()

            # Total donations
            total_donations = self.db.query(func.count(DonationModel.id)).scalar()

            # Total amount
            total_amount_result = self.db.query(func.sum(DonationModel.amount_gtq)).scalar()
            total_amount_gtq = float(total_amount_result) if total_amount_result else 0.0

            # Pending donations
            pending_status = self.db.query(StatusCatalogModel).filter(
                StatusCatalogModel.code == 'PENDING'
            ).first()

            pending_donations = 0
            if pending_status:
                pending_donations = self.db.query(func.count(DonationModel.id)).filter(
                    DonationModel.status_id == pending_status.id
                ).scalar()

            return {
                "total_users": total_users,
                "active_users": active_users,
                "total_donations": total_donations,
                "total_amount_gtq": total_amount_gtq,
                "pending_donations": pending_donations
            }

        except Exception as e:
            logger.error(f"Error getting admin stats: {e}", exc_info=True)
            return {
                "total_users": 0,
                "active_users": 0,
                "total_donations": 0,
                "total_amount_gtq": 0.0,
                "pending_donations": 0
            }

    def get_recent_users(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent user registrations for admin dashboard"""
        try:
            users = self.db.query(UserModel).order_by(
                desc(UserModel.created_at)
            ).limit(limit).all()

            return [{
                "id": str(user.id),
                "email": user.email,
                "roles": [role.name for role in user.user_roles],
                "joined_at": user.created_at,
                "status": "active" if user.is_active else "inactive"
            } for user in users]

        except Exception as e:
            logger.error(f"Error getting recent users: {e}", exc_info=True)
            return []

    def get_recent_donations(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent donations for admin dashboard"""
        try:
            donations = self.db.query(DonationModel).join(
                StatusCatalogModel, DonationModel.status_id == StatusCatalogModel.id
            ).order_by(
                desc(DonationModel.created_at)
            ).limit(limit).all()

            return [{
                "id": str(donation.id),
                "amount_gtq": float(donation.amount_gtq),
                "donor_email": donation.donor_email,
                "donor_name": donation.donor_name,
                "status": donation.status.code if donation.status else "UNKNOWN",
                "created_at": donation.created_at
            } for donation in donations]

        except Exception as e:
            logger.error(f"Error getting recent donations: {e}", exc_info=True)
            return []

    def get_donor_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics for donor dashboard"""
        try:
            # User's donations
            user_donations = self.db.query(DonationModel).filter(
                DonationModel.user_id == user_id
            ).all()

            total_donations = len(user_donations)

            # Total amount
            total_amount_result = self.db.query(func.sum(DonationModel.amount_gtq)).filter(
                DonationModel.user_id == user_id
            ).scalar()
            total_amount_gtq = float(total_amount_result) if total_amount_result else 0.0

            # Monthly average (simplified calculation)
            monthly_average = total_amount_gtq / max(1, (datetime.utcnow().year - 2023) * 12 + datetime.utcnow().month)

            # Favorite program (simplified - just return a placeholder)
            favorite_program = "Programa General"  # TODO: Implement based on donation programs

            # Member since
            user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
            member_since = user.created_at if user else datetime.utcnow()

            # Donation streak (simplified)
            donation_streak = min(12, total_donations)  # TODO: Implement proper streak calculation

            return {
                "total_donations": total_donations,
                "total_amount_gtq": total_amount_gtq,
                "monthly_average": monthly_average,
                "favorite_program": favorite_program,
                "member_since": member_since,
                "donation_streak": donation_streak
            }

        except Exception as e:
            logger.error(f"Error getting donor stats for user {user_id}: {e}", exc_info=True)
            return {
                "total_donations": 0,
                "total_amount_gtq": 0.0,
                "monthly_average": 0.0,
                "favorite_program": None,
                "member_since": datetime.utcnow(),
                "donation_streak": 0
            }

    def get_user_donations(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's recent donations for donor dashboard"""
        try:
            donations = self.db.query(DonationModel).join(
                StatusCatalogModel, DonationModel.status_id == StatusCatalogModel.id
            ).filter(
                DonationModel.user_id == user_id
            ).order_by(
                desc(DonationModel.created_at)
            ).limit(limit).all()

            return [{
                "id": str(donation.id),
                "amount_gtq": float(donation.amount_gtq),
                "donor_email": donation.donor_email,
                "donor_name": donation.donor_name,
                "status": donation.status.code if donation.status else "UNKNOWN",
                "created_at": donation.created_at
            } for donation in donations]

        except Exception as e:
            logger.error(f"Error getting user donations for user {user_id}: {e}", exc_info=True)
            return []

    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics for regular user dashboard"""
        try:
            # Basic system stats (same for all regular users)
            total_donations = self.db.query(func.count(DonationModel.id)).scalar()
            total_amount_result = self.db.query(func.sum(DonationModel.amount_gtq)).scalar()
            total_amount_gtq = float(total_amount_result) if total_amount_result else 0.0

            # Member since
            user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
            member_since = user.created_at if user else datetime.utcnow()

            return {
                "total_donations": total_donations,
                "total_amount_gtq": total_amount_gtq,
                "member_since": member_since
            }

        except Exception as e:
            logger.error(f"Error getting user stats for user {user_id}: {e}", exc_info=True)
            return {
                "total_donations": 0,
                "total_amount_gtq": 0.0,
                "member_since": datetime.utcnow()
            }