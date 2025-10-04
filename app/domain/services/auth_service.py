"""
Authentication service with business logic
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.adapters.schemas.auth_schemas import (
    UserRegister, UserLogin, TokenResponse, DashboardResponse, UserInfo
)
from app.infrastructure.database.models import UserModel, RoleModel
from app.infrastructure.auth.jwt_utils import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, verify_token, create_password_reset_token,
    verify_password_reset_token, create_email_verification_token,
    verify_email_verification_token
)
from app.infrastructure.external.email_service import email_service
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class AuthService:
    """Authentication service with business logic"""

    def __init__(self, db: Session):
        self.db = db

    def register_user(self, user_data: UserRegister, current_user: Optional[UserModel] = None) -> UserModel:
        """Register a new user"""
        # Check if email already exists
        existing_user = self.db.query(UserModel).filter(
            UserModel.email == user_data.email
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Validate role permissions
        requested_role = user_data.role.upper()

        # Define roles that require admin privileges
        admin_only_roles = {"ADMIN", "ORGANIZATION", "AUDITOR"}
        
        # Public roles that can be self-registered
        public_roles = {"USER", "DONOR"}

        # Only ADMIN can create ADMIN, ORGANIZATION, or AUDITOR roles
        if requested_role in admin_only_roles:
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only administrators can create users with elevated roles"
                )

            user_roles = [user_role.role.name for user_role in current_user.user_roles]
            if "ADMIN" not in user_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only administrators can create users with elevated roles"
                )
        
        # Validate that the requested role exists and is either public or user is admin
        elif requested_role not in public_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {requested_role}. Public registration only allows USER or DONOR roles."
            )

        # Get role
        role = self.db.query(RoleModel).filter(
            RoleModel.name == requested_role
        ).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {requested_role}"
            )

        # Get default organization (for now, assign all users to the default org)
        default_org = self.db.query(UserModel.__table__.c.organization_id).first()
        # For now, we'll set organization_id to None - can be updated later by admin
        # TODO: Implement proper organization assignment logic

        # Create user
        hashed_password = get_password_hash(user_data.password)
        user = UserModel(
            email=user_data.email,
            password_hash=hashed_password,
            email_verified=False,
            is_active=True,
            organization_id=None  # Will be assigned by admin later
        )

        self.db.add(user)
        self.db.flush()  # Get user ID

        # Assign role
        from app.infrastructure.database.models import UserRoleModel
        user_role = UserRoleModel(user_id=user.id, role_id=role.id)
        self.db.add(user_role)

        self.db.commit()
        self.db.refresh(user)

        # Send email verification
        verification_token = create_email_verification_token(user.id)
        email_sent = email_service.send_email_verification_email(user.email, verification_token)

        if email_sent:
            logger.info(f"Verification email sent to: {user.email}")
        else:
            logger.warning(f"Failed to send verification email to: {user.email}")

        logger.info(f"User registered: {user.email} with role {user_data.role}")
        return user

    def authenticate_user(self, user_data: UserLogin) -> Optional[UserModel]:
        """Authenticate user with email and password"""
        user = self.db.query(UserModel).filter(
            UserModel.email == user_data.email
        ).first()

        if not user or not verify_password(user_data.password, user.password_hash):
            return None

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is disabled"
            )

        return user

    def create_tokens(self, user: UserModel) -> TokenResponse:
        """Create access and refresh tokens for user"""
        roles = [user_role.role.name for user_role in user.user_roles]

        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "roles": roles
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=30 * 60  # 30 minutes
        )

    def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token"""
        payload = verify_token(refresh_token, "refresh")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        user_id = payload.get("sub")
        user = self.db.query(UserModel).filter(UserModel.id == UUID(user_id)).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        return self.create_tokens(user)

    def initiate_password_reset(self, email: str) -> str:
        """Initiate password reset process"""
        user = self.db.query(UserModel).filter(UserModel.email == email).first()
        if not user:
            # Don't reveal if email exists or not
            return "If the email exists, a reset link has been sent"

        reset_token = create_password_reset_token(email)

        # Send email with reset token
        email_sent = email_service.send_password_reset_email(email, reset_token)

        if email_sent:
            logger.info(f"Password reset email sent to: {email}")
        else:
            logger.error(f"Failed to send password reset email to: {email}")

        return "If the email exists, a reset link has been sent"

    def reset_password(self, token: str, new_password: str) -> str:
        """Reset password using reset token"""
        email = verify_password_reset_token(token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )

        user = self.db.query(UserModel).filter(UserModel.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )

        user.password_hash = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()

        self.db.commit()

        logger.info(f"Password reset completed for: {email}")
        return "Password reset successfully"

    def verify_email(self, token: str) -> str:
        """Verify user email using verification token"""
        user_id = verify_email_verification_token(token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )

        user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )

        if user.email_verified:
            return "Email already verified"

        user.email_verified = True
        user.updated_at = datetime.utcnow()

        self.db.commit()

        # Send welcome email
        email_sent = email_service.send_welcome_email(user.email, user.email)  # Using email as name for now

        if email_sent:
            logger.info(f"Welcome email sent to: {user.email}")
        else:
            logger.warning(f"Failed to send welcome email to: {user.email}")

        logger.info(f"Email verified for user: {user.email}")
        return "Email verified successfully"

    def change_password(self, user_id: UUID, current_password: str, new_password: str) -> str:
        """Change user password"""
        user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if not verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        user.password_hash = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()

        self.db.commit()

        logger.info(f"Password changed for user: {user.email}")
        return "Password changed successfully"

    def get_dashboard_data(self, user: UserModel) -> DashboardResponse:
        """Get dashboard data based on user role"""
        roles = [user_role.role.name for user_role in user.user_roles]
        user_info = UserInfo(
            id=user.id,
            email=user.email,
            email_verified=user.email_verified,
            is_active=user.is_active,
            roles=roles,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

        stats = self._get_role_based_stats(user, roles)
        recent_activity = self._get_recent_activity(user, roles)

        return DashboardResponse(
            user=user_info,
            stats=stats,
            recent_activity=recent_activity
        )

    def change_user_role_to_donor(self, user_id: UUID) -> str:
        """Allow a user to change their role to DONOR"""
        user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Check if user is already a donor
        user_roles = [user_role.role.name for user_role in user.user_roles]
        if "DONOR" in user_roles:
            return "User is already a donor"

        # Check if user is currently USER (only USER can upgrade to DONOR)
        if "USER" not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only regular users can upgrade to donor status"
            )

        # Get DONOR role
        donor_role = self.db.query(RoleModel).filter(RoleModel.name == "DONOR").first()
        if not donor_role:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="DONOR role not found"
            )

        # Remove USER role and add DONOR role
        user_role_association = None
        for ur in user.user_roles:
            if ur.role.name == "USER":
                user_role_association = ur
                break

        if user_role_association:
            self.db.delete(user_role_association)

        # Add DONOR role
        from app.infrastructure.database.models import UserRoleModel
        new_user_role = UserRoleModel(user_id=user.id, role_id=donor_role.id)
        self.db.add(new_user_role)

        self.db.commit()

        logger.info(f"User {user.email} changed role from USER to DONOR")
        return "Successfully upgraded to donor status"

    def _get_role_based_stats(self, user: UserModel, roles: List[str]) -> Dict[str, Any]:
        """Get statistics based on user roles"""
        stats = {}

        if "ADMIN" in roles:
            # Admin stats - simplified for now
            stats.update({
                "total_users": 3,  # Placeholder
                "total_donations": 0,  # Placeholder
                "system_health": "Good"
            })

        if "DONOR" in roles:
            # Donor stats
            user_donations = len(user.donations) if hasattr(user, 'donations') else 0
            total_donated = sum(d.amount_gtq for d in user.donations if hasattr(user, 'donations') and d.status_id == 2) or 0
            stats.update({
                "my_donations": user_donations,
                "total_donated_gtq": float(total_donated)
            })

        if "USER" in roles:
            # Regular user stats
            stats.update({
                "account_status": "Active" if user.is_active else "Inactive",
                "email_verified": user.email_verified
            })

        return stats
        """Get statistics based on user roles"""
        stats = {}

        if "ADMIN" in roles:
            # Admin stats
            total_users = self.db.query(UserModel).count()
            total_donations = self.db.query(self.db.query(UserModel).count()).scalar()  # Placeholder
            stats.update({
                "total_users": total_users,
                "total_donations": total_donations,
                "system_health": "Good"
            })

        if "DONOR" in roles:
            # Donor stats
            user_donations = len(user.donations)
            total_donated = sum(d.amount_gtq for d in user.donations if d.status_id == 2)  # Approved
            stats.update({
                "my_donations": user_donations,
                "total_donated_gtq": float(total_donated)
            })

        if "USER" in roles:
            # Regular user stats
            stats.update({
                "account_status": "Active" if user.is_active else "Inactive",
                "email_verified": user.email_verified
            })

        return stats

    def _get_recent_activity(self, user: UserModel, roles: List[str]) -> List[Dict[str, Any]]:
        """Get recent activity based on user roles"""
        activity = []

        if "DONOR" in roles:
            # Recent donations
            recent_donations = user.donations[:5]  # Last 5 donations
            for donation in recent_donations:
                activity.append({
                    "type": "donation",
                    "description": f"Donation of Q{donation.amount_gtq}",
                    "date": donation.created_at.isoformat(),
                    "status": "completed" if donation.status_id == 2 else "pending"
                })

        # Add login activity
        activity.append({
            "type": "login",
            "description": "User logged in",
            "date": datetime.utcnow().isoformat(),
            "status": "completed"
        })

        return activity[:10]  # Limit to 10 items