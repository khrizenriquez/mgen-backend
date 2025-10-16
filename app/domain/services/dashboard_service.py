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

    def get_impact_metrics(self) -> Dict[str, Any]:
        """Get real impact metrics for dashboard"""
        try:
            # Get approved donations
            approved_status = self.db.query(StatusCatalogModel).filter(
                StatusCatalogModel.code == 'APPROVED'
            ).first()

            if not approved_status:
                return {
                    "children_impacted": 0,
                    "meals_provided": 0,
                    "scholarships_awarded": 0,
                    "evangelism_hours": 0
                }

            # Calculate impact based on donation amounts
            # This is a simplified calculation - in real implementation,
            # you might have specific impact tracking tables

            total_donated_result = self.db.query(func.sum(DonationModel.amount_gtq)).filter(
                DonationModel.status_id == approved_status.id
            ).scalar()

            total_donated = float(total_donated_result) if total_donated_result else 0.0

            # Simplified impact calculations (adjust based on your business rules)
            children_impacted = int(total_donated / 50)  # Q50 per child per month
            meals_provided = int(total_donated / 10)    # Q10 per meal
            scholarships_awarded = int(total_donated / 1000)  # Q1000 per scholarship
            evangelism_hours = int(total_donated / 25)   # Q25 per hour

            return {
                "children_impacted": children_impacted,
                "meals_provided": meals_provided,
                "scholarships_awarded": scholarships_awarded,
                "evangelism_hours": evangelism_hours
            }

        except Exception as e:
            logger.error(f"Error getting impact metrics: {e}", exc_info=True)
            return {
                "children_impacted": 0,
                "meals_provided": 0,
                "scholarships_awarded": 0,
                "evangelism_hours": 0
            }

    def get_active_programs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get active programs with progress information"""
        try:
            # For now, return mock programs since we don't have a programs table
            # In real implementation, this would query a programs table

            programs = [
                {
                    "id": "prog-001",
                    "name": "Campaña de Verano 2025",
                    "description": "Apoyo estival para niños en situación de vulnerabilidad",
                    "goal_amount": 15000.00,
                    "current_amount": 9750.00,
                    "progress_percentage": 65,
                    "start_date": "2025-01-01",
                    "end_date": "2025-03-31",
                    "status": "active"
                },
                {
                    "id": "prog-002",
                    "name": "Programa de Becas 2025",
                    "description": "Educación para el futuro de nuestros niños",
                    "goal_amount": 25000.00,
                    "current_amount": 10000.00,
                    "progress_percentage": 40,
                    "start_date": "2025-01-01",
                    "end_date": "2025-12-31",
                    "status": "active"
                },
                {
                    "id": "prog-003",
                    "name": "Alimentación Escolar",
                    "description": "Nutrición para el aprendizaje continuo",
                    "goal_amount": 12000.00,
                    "current_amount": 9600.00,
                    "progress_percentage": 80,
                    "start_date": "2025-01-01",
                    "end_date": "2025-12-31",
                    "status": "active"
                }
            ]

            return programs[:limit]

        except Exception as e:
            logger.error(f"Error getting active programs: {e}", exc_info=True)
            return []

    def get_upcoming_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get upcoming events"""
        try:
            # For now, return mock events since we don't have an events table
            # In real implementation, this would query an events table

            events = [
                {
                    "id": "event-001",
                    "title": "Campaña de Navidad",
                    "date": "2025-12-01",
                    "type": "campaign",
                    "description": "Ayuda a los niños en Navidad",
                    "location": "Centro Comunitario",
                    "status": "upcoming"
                },
                {
                    "id": "event-002",
                    "title": "Día del Niño",
                    "date": "2025-04-30",
                    "type": "event",
                    "description": "Celebración especial para los niños",
                    "location": "Parque Central",
                    "status": "upcoming"
                },
                {
                    "id": "event-003",
                    "title": "Programa de Becas",
                    "date": "2025-03-15",
                    "type": "program",
                    "description": "Apoyo educativo continuo",
                    "location": "Escuela Principal",
                    "status": "upcoming"
                }
            ]

            # Filter only upcoming events (future dates)
            current_date = datetime.utcnow().strftime('%Y-%m-%d')
            upcoming_events = [event for event in events if event['date'] >= current_date]

            return upcoming_events[:limit]

        except Exception as e:
            logger.error(f"Error getting upcoming events: {e}", exc_info=True)
            return []

    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences"""
        try:
            # For now, return default preferences since we don't have a preferences table
            # In real implementation, this would query user preferences

            user = self.db.query(UserModel).filter(UserModel.id == user_id).first()

            if not user:
                return {
                    "favorite_cause": "Programa General",
                    "communication_preferences": {
                        "email_notifications": True,
                        "sms_notifications": False,
                        "monthly_reports": True
                    },
                    "privacy_settings": {
                        "show_donations_publicly": False,
                        "allow_contact": True
                    }
                }

            # Calculate favorite cause based on donation patterns
            # For now, return mock data
            favorite_cause = "Programa General"

            return {
                "favorite_cause": favorite_cause,
                "communication_preferences": {
                    "email_notifications": True,
                    "sms_notifications": False,
                    "monthly_reports": True
                },
                "privacy_settings": {
                    "show_donations_publicly": False,
                    "allow_contact": True
                }
            }

        except Exception as e:
            logger.error(f"Error getting user preferences for user {user_id}: {e}", exc_info=True)
            return {
                "favorite_cause": "Programa General",
                "communication_preferences": {
                    "email_notifications": True,
                    "sms_notifications": False,
                    "monthly_reports": True
                },
                "privacy_settings": {
                    "show_donations_publicly": False,
                    "allow_contact": True
                }
            }

    def get_user_levels(self, user_id: str) -> Dict[str, Any]:
        """Get user level and rewards information"""
        try:
            # Get user's total donations
            total_amount_result = self.db.query(func.sum(DonationModel.amount_gtq)).filter(
                DonationModel.user_id == user_id
            ).scalar()
            total_donated = float(total_amount_result) if total_amount_result else 0.0

            # Define level thresholds (in Q)
            levels = [
                {"name": "Donante Bronce", "threshold": 0, "color": "warning"},
                {"name": "Donante Plata", "threshold": 1000, "color": "secondary"},
                {"name": "Donante Oro", "threshold": 5000, "color": "warning"},
                {"name": "Donante Platino", "threshold": 15000, "color": "primary"},
                {"name": "Donante Diamante", "threshold": 50000, "color": "info"},
                {"name": "Donante Leyenda", "threshold": 100000, "color": "success"}
            ]

            # Find current level
            current_level = levels[0]
            next_level = None

            for i, level in enumerate(levels):
                if total_donated >= level["threshold"]:
                    current_level = level
                    if i + 1 < len(levels):
                        next_level = levels[i + 1]

            # Calculate progress to next level
            progress_percentage = 0
            next_level_threshold = 0

            if next_level:
                current_level_threshold = current_level["threshold"]
                next_level_threshold = next_level["threshold"]
                progress_percentage = min(100, ((total_donated - current_level_threshold) /
                                               (next_level_threshold - current_level_threshold)) * 100)
            else:
                progress_percentage = 100  # Max level reached

            return {
                "current_level": current_level["name"],
                "current_level_color": current_level["color"],
                "next_level": next_level["name"] if next_level else None,
                "total_donated": total_donated,
                "progress_percentage": progress_percentage,
                "next_level_threshold": next_level_threshold,
                "amount_needed": max(0, next_level_threshold - total_donated) if next_level else 0
            }

        except Exception as e:
            logger.error(f"Error getting user levels for user {user_id}: {e}", exc_info=True)
            return {
                "current_level": "Donante Bronce",
                "current_level_color": "warning",
                "next_level": "Donante Plata",
                "total_donated": 0.0,
                "progress_percentage": 0,
                "next_level_threshold": 1000,
                "amount_needed": 1000
            }

    def get_growth_metrics(self) -> Dict[str, Any]:
        """Get growth metrics compared to previous period"""
        try:
            # Calculate current month metrics
            current_date = datetime.utcnow()
            current_month_start = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            current_month_end = current_date

            # Previous month
            if current_date.month == 1:
                prev_month_start = current_date.replace(year=current_date.year-1, month=12, day=1, hour=0, minute=0, second=0, microsecond=0)
                prev_month_end = current_date.replace(year=current_date.year-1, month=12, day=31, hour=23, minute=59, second=59, microsecond=999999)
            else:
                prev_month_start = current_date.replace(month=current_date.month-1, day=1, hour=0, minute=0, second=0, microsecond=0)
                prev_month_end = current_date.replace(month=current_date.month-1, day=1, hour=23, minute=59, second=59, microsecond=999999) - timedelta(days=1)

            # Current month users
            current_users = self.db.query(func.count(UserModel.id)).filter(
                UserModel.created_at.between(current_month_start, current_month_end)
            ).scalar()

            # Previous month users
            prev_users = self.db.query(func.count(UserModel.id)).filter(
                UserModel.created_at.between(prev_month_start, prev_month_end)
            ).scalar()

            # Current month donations and amount
            current_donations = self.db.query(func.count(DonationModel.id)).filter(
                DonationModel.created_at.between(current_month_start, current_month_end)
            ).scalar()

            current_amount_result = self.db.query(func.sum(DonationModel.amount_gtq)).filter(
                DonationModel.created_at.between(current_month_start, current_month_end)
            ).scalar()
            current_amount = float(current_amount_result) if current_amount_result else 0.0

            # Previous month donations and amount
            prev_donations = self.db.query(func.count(DonationModel.id)).filter(
                DonationModel.created_at.between(prev_month_start, prev_month_end)
            ).scalar()

            prev_amount_result = self.db.query(func.sum(DonationModel.amount_gtq)).filter(
                DonationModel.created_at.between(prev_month_start, prev_month_end)
            ).scalar()
            prev_amount = float(prev_amount_result) if prev_amount_result else 0.0

            # Calculate growth percentages
            users_growth = ((current_users - prev_users) / prev_users * 100) if prev_users > 0 else 0
            donations_growth = ((current_donations - prev_donations) / prev_donations * 100) if prev_donations > 0 else 0
            amount_growth = ((current_amount - prev_amount) / prev_amount * 100) if prev_amount > 0 else 0

            return {
                "users_growth_percentage": round(users_growth, 1),
                "donations_growth_percentage": round(donations_growth, 1),
                "amount_growth_percentage": round(amount_growth, 1),
                "current_month": {
                    "users": current_users,
                    "donations": current_donations,
                    "amount": current_amount
                },
                "previous_month": {
                    "users": prev_users,
                    "donations": prev_donations,
                    "amount": prev_amount
                }
            }

        except Exception as e:
            logger.error(f"Error getting growth metrics: {e}", exc_info=True)
            return {
                "users_growth_percentage": 0.0,
                "donations_growth_percentage": 0.0,
                "amount_growth_percentage": 0.0,
                "current_month": {"users": 0, "donations": 0, "amount": 0.0},
                "previous_month": {"users": 0, "donations": 0, "amount": 0.0}
            }