"""
Authentication controller with JWT endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.adapters.schemas.auth_schemas import (
    UserRegister, UserLogin, TokenResponse, RefreshTokenRequest,
    ForgotPasswordRequest, ResetPasswordRequest, PasswordChangeRequest,
    EmailVerificationRequest, DashboardResponse, GenericResponse, UserListResponse
)
from app.domain.services.auth_service import AuthService
from app.infrastructure.database.database import get_db
from app.infrastructure.auth.dependencies import (
    get_current_active_user, get_optional_current_user, require_role, require_any_role, user_to_user_info,
    require_admin, require_organization, require_auditor
)
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={401: {"description": "Unauthorized"}}
)


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Dependency to get auth service"""
    return AuthService(db)


@router.post("/register", response_model=GenericResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegister,
    current_user = Depends(get_optional_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user account

    - **email**: User's email address (must be unique)
    - **password**: User's password (min 8 characters)
    - **role**: User's role (default: USER, requires admin for elevated roles)
    """
    try:
        user = auth_service.register_user(user_data, current_user)
        logger.info(f"User registered successfully: {user.email}")

        return GenericResponse(message="User registered successfully. Please check your email for verification.")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    user_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate user and return JWT tokens

    - **email**: User's email address
    - **password**: User's password
    """
    try:
        user = auth_service.authenticate_user(user_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )

        tokens = auth_service.create_tokens(user)
        logger.info(f"User logged in: {user.email}")

        return tokens

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token

    - **refresh_token**: Valid refresh token
    """
    try:
        return auth_service.refresh_access_token(token_data.refresh_token)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/forgot-password", response_model=GenericResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Initiate password reset process

    - **email**: User's email address
    """
    try:
        result = auth_service.initiate_password_reset(request.email)
        return GenericResponse(message=result)
    except Exception as e:
        logger.error(f"Forgot password failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed"
        )


@router.post("/reset-password", response_model=GenericResponse)
async def reset_password(
    request: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Reset password using reset token

    - **token**: Password reset token
    - **new_password**: New password (min 8 characters)
    """
    try:
        result = auth_service.reset_password(request.token, request.new_password)
        return GenericResponse(message=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


@router.post("/verify-email", response_model=GenericResponse)
async def verify_email(
    request: EmailVerificationRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Verify user email using verification token

    - **token**: Email verification token
    """
    try:
        result = auth_service.verify_email(request.token)
        return GenericResponse(message=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )


@router.post("/change-password", response_model=GenericResponse)
async def change_password(
    request: PasswordChangeRequest,
    current_user = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Change current user's password

    - **current_password**: Current password
    - **new_password**: New password (min 8 characters)
    """
    try:
        result = auth_service.change_password(
            current_user.id,
            request.current_password,
            request.new_password
        )
        return GenericResponse(message=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.post("/logout", response_model=GenericResponse)
async def logout_user(
    current_user = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Log out current user

    Removes user session on server side. Client should also remove stored tokens.
    """
    try:
        result = auth_service.logout_user(current_user)
        return GenericResponse(message=result)
    except Exception as e:
        logger.error(f"Logout failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    current_user = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Get user dashboard with role-based data

    Requires authentication.
    """
    try:
        return auth_service.get_dashboard_data(current_user)
    except Exception as e:
        logger.error(f"Dashboard fetch failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load dashboard"
        )


@router.get("/me")
async def get_current_user_info(
    current_user = Depends(get_current_active_user)
):
    """
    Get current user information

    Requires authentication.
    """
    try:
        roles = [user_role.role.name for user_role in current_user.user_roles]
        return {
            "id": str(current_user.id),
            "email": current_user.email,
            "email_verified": current_user.email_verified,
            "is_active": current_user.is_active,
            "roles": roles,
            "created_at": current_user.created_at.isoformat(),
            "updated_at": current_user.updated_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Get user info failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )


@router.post("/upgrade-to-donor", response_model=GenericResponse)
async def upgrade_to_donor(
    current_user = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Upgrade current user role from USER to DONOR

    Requires authentication. Only regular users can upgrade to donor status.
    """
    try:
        result = auth_service.change_user_role_to_donor(current_user.id)
        return GenericResponse(message=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Role upgrade failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upgrade role"
        )


# Admin-only endpoints
# TODO: Fix FastAPI compatibility issue with UserModel
# @router.get("/admin/users", response_model=UserListResponse)
# async def get_all_users(
#     current_user = Depends(require_role("ADMIN")),
#     auth_service: AuthService = Depends(get_auth_service),
#     skip: int = 0,
#     limit: int = 100
# ) -> UserListResponse:
#     """
#     Get all users (Admin only)
#
#     Requires ADMIN role.
#     """
#     try:
#         users = auth_service.get_all_users(skip=skip, limit=limit)
#         return UserListResponse(
#             users=users,
#             total=len(users),
#             skip=skip,
#             limit=limit
#         )
#     except Exception as e:
#         logger.error(f"Get all users failed: {e}", exc_info=True)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Failed to get users"
#         )