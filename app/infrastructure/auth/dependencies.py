"""
Authentication dependencies for FastAPI
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID

from app.adapters.schemas.auth_schemas import UserInfo
from app.domain.entities.user import User
from app.infrastructure.database.database import get_db
from app.infrastructure.database.models import UserModel, RoleModel
from app.infrastructure.auth.jwt_utils import verify_token
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)

# Security scheme for required authentication
security = HTTPBearer()

# Security scheme for optional authentication (doesn't auto-error)
optional_security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current authenticated user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = verify_token(token, "access")

    if payload is None:
        raise credentials_exception

    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise credentials_exception

    user = db.query(UserModel).filter(UserModel.id == user_uuid).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    return user


def get_current_active_user(current_user = Depends(get_current_user)):
    """Get current active user (alias for get_current_user)"""
    return current_user


def get_user_roles(user) -> List[str]:
    """Get list of role names for a user"""
    return [user_role.role.name for user_role in user.user_roles]


def require_admin(current_user = Depends(get_current_user)):
    """Require admin role"""
    user_roles = get_user_roles(current_user)
    if "ADMIN" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    return current_user


def require_organization(current_user = Depends(get_current_user)):
    """Require organization or admin role"""
    user_roles = get_user_roles(current_user)
    if "ADMIN" not in user_roles and "ORGANIZATION" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization or Admin role required"
        )
    return current_user


def require_auditor(current_user = Depends(get_current_user)):
    """Require auditor, organization or admin role"""
    user_roles = get_user_roles(current_user)
    if not any(role in user_roles for role in ["ADMIN", "ORGANIZATION", "AUDITOR"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Auditor, Organization or Admin role required"
        )
    return current_user


def require_role(required_role: str):
    """Dependency factory to require specific role"""
    def role_checker(
        current_user,
        user_roles: List[str] = Depends(get_user_roles)
    ):
        if required_role not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        return current_user
    return role_checker


def require_any_role(*required_roles: str):
    """Dependency factory to require any of the specified roles"""
    def role_checker(
        current_user = Depends(get_current_user),
        user_roles: List[str] = Depends(get_user_roles)
    ):
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of roles {required_roles} required"
            )
        return current_user
    return role_checker


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    db: Session = Depends(get_db)
) -> Optional:
    """Get current user if token is provided, None otherwise"""
    if credentials is None:
        return None

    token = credentials.credentials
    payload = verify_token(token, "access")

    if payload is None:
        return None

    user_id: str = payload.get("sub")
    if user_id is None:
        return None

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        return None

    user = db.query(UserModel).filter(UserModel.id == user_uuid).first()
    if user is None or not user.is_active:
        return None

    return user


def user_to_user_info(user: UserModel) -> UserInfo:
    """Convert UserModel to UserInfo schema"""
    roles = [user_role.role.name for user_role in user.user_roles]
    return UserInfo(
        id=user.id,
        email=user.email,
        email_verified=user.email_verified,
        is_active=user.is_active,
        roles=roles,
        created_at=user.created_at,
        updated_at=user.updated_at
    )