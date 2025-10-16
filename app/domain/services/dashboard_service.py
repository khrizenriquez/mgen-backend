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

    def get_admin_stats(self, organization_id: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for admin dashboard"""
        try:
            # Base queries
            users_query = self.db.query(func.count(UserModel.id))
            donations_query = self.db.query(func.count(DonationModel.id))
            amount_query = self.db.query(func.sum(DonationModel.amount_gtq))
            pending_query = self.db.query(func.count(DonationModel.id))

            # Apply organization filter if provided
            if organization_id:
                users_query = users_query.filter(UserModel.organization_id == organization_id)
                # Join donations with users to filter by organization
                donations_query = donations_query.join(UserModel, DonationModel.user_id == UserModel.id).filter(
                    UserModel.organization_id == organization_id
                )
                amount_query = amount_query.join(UserModel, DonationModel.user_id == UserModel.id).filter(
                    UserModel.organization_id == organization_id
                )

            # Total users
            total_users = users_query.scalar()

            # Active users (not marked as inactive)
            active_users = self.db.query(func.count(UserModel.id)).filter(
                UserModel.is_active == True
            )
            if organization_id:
                active_users = active_users.filter(UserModel.organization_id == organization_id)
            active_users = active_users.scalar()

            # Total donations
            total_donations = donations_query.scalar()

            # Total amount
            total_amount_result = amount_query.scalar()
            total_amount_gtq = float(total_amount_result) if total_amount_result else 0.0

            # Pending donations
            pending_status = self.db.query(StatusCatalogModel).filter(
                StatusCatalogModel.code == 'PENDING'
            ).first()

            pending_donations = 0
            if pending_status:
                pending_query_base = self.db.query(func.count(DonationModel.id)).filter(
                    DonationModel.status_id == pending_status.id
                )
                if organization_id:
                    pending_query_base = pending_query_base.join(UserModel, DonationModel.user_id == UserModel.id).filter(
                        UserModel.organization_id == organization_id
                    )
                pending_donations = pending_query_base.scalar()

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

    def get_recent_users(self, limit: int = 5, organization_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent user registrations for admin dashboard"""
        try:
            query = self.db.query(UserModel)

            if organization_id:
                query = query.filter(UserModel.organization_id == organization_id)

            users = query.order_by(
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

    def get_recent_donations(self, limit: int = 5, organization_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent donations for admin dashboard"""
        try:
            query = self.db.query(DonationModel).join(
                StatusCatalogModel, DonationModel.status_id == StatusCatalogModel.id
            )

            if organization_id:
                # Join with UserModel to filter by organization
                query = query.join(UserModel, DonationModel.user_id == UserModel.id).filter(
                    UserModel.organization_id == organization_id
                )

            donations = query.order_by(
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

            # Member since
            user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
            member_since = user.created_at if user else datetime.utcnow()

            # Monthly average - calculate based on actual donation history
            if user and total_donations > 0:
                # Calculate months since user joined
                months_since_joined = max(1, (datetime.utcnow().year - member_since.year) * 12 +
                                        datetime.utcnow().month - member_since.month + 1)
                monthly_average = total_amount_gtq / months_since_joined
            else:
                monthly_average = 0.0

            # Favorite program - TODO: Implement when donation programs are added to schema
            favorite_program = "Programa General"

            # Donation streak - calculate consecutive months with donations
            donation_streak = self._calculate_donation_streak(user_id)

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

    def _calculate_donation_streak(self, user_id: str) -> int:
        """Calculate the current donation streak in consecutive months"""
        try:
            from sqlalchemy import extract, func

            # Get all approved donations for the user, ordered by creation date
            approved_status = self.db.query(StatusCatalogModel).filter(
                StatusCatalogModel.code == 'APPROVED'
            ).first()

            if not approved_status:
                return 0

            donations = self.db.query(
                extract('year', DonationModel.created_at).label('year'),
                extract('month', DonationModel.created_at).label('month')
            ).filter(
                DonationModel.user_id == user_id,
                DonationModel.status_id == approved_status.id
            ).distinct().order_by(
                desc(extract('year', DonationModel.created_at)),
                desc(extract('month', DonationModel.created_at))
            ).all()

            if not donations:
                return 0

            # Convert to set of (year, month) tuples for easy lookup
            donation_months = {(int(d.year), int(d.month)) for d in donations}

            # Start from current month and go backwards
            current_date = datetime.utcnow()
            current_year = current_date.year
            current_month = current_date.month

            streak = 0
            check_year = current_year
            check_month = current_month

            while True:
                if (check_year, check_month) in donation_months:
                    streak += 1
                    # Move to previous month
                    if check_month == 1:
                        check_month = 12
                        check_year -= 1
                    else:
                        check_month -= 1
                else:
                    # Check if current month has donations (to handle current partial month)
                    if streak == 0 and (current_year, current_month) in donation_months:
                        streak = 1
                    break

            return streak

        except Exception as e:
            logger.error(f"Error calculating donation streak for user {user_id}: {e}", exc_info=True)
            return 0