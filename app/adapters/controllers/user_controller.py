"""
User controller with CRUD endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.adapters.schemas.user_schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    DeleteResponse,
    UserProfileUpdate,
    UserProfileResponse,
    ChangePasswordRequest,
    UserPreferencesUpdate,
    UserPreferencesResponse
)
from app.adapters.schemas.auth_schemas import UserInfo
from app.domain.entities.user import User
from app.domain.services.user_service import UserService
from app.infrastructure.database.user_repository_impl import UserRepositoryImpl
from app.infrastructure.database.database import get_db
from app.infrastructure.auth.dependencies import (
    get_current_active_user, require_role, require_admin, require_organization, require_any_role, user_to_user_info
)

from app.infrastructure.database.models import UserModel
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Dependency to get user service"""
    user_repository = UserRepositoryImpl(db)
    return UserService(user_repository)


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    user_data: UserCreate,
    current_user = Depends(require_role("ADMIN")),
    user_service: UserService = Depends(get_user_service)
):
    """
    Create a new user
    
    - **email**: User's email address (must be unique)
    - **first_name**: User's first name
    - **last_name**: User's last name  
    - **is_active**: Whether the user is active (default: true)
    """
    user = User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        is_active=user_data.is_active
    )
    return await user_service.create_user(user)


# Profile and preferences endpoints


# CRUD endpoints
@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get current user's complete profile

    Returns the user's profile information including contact details.
    """
    user = await user_service.get_user_profile(str(current_user.id))
    return UserProfileResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        address=user.address,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Update current user's profile

    Updates profile information like name, phone, and address.
    """
    updated_user = await user_service.update_profile(str(current_user.id), profile_data.dict(exclude_unset=True))

    return UserProfileResponse(
        id=updated_user.id,
        email=updated_user.email,
        first_name=updated_user.first_name,
        last_name=updated_user.last_name,
        phone=updated_user.phone,
        address=updated_user.address,
        is_active=updated_user.is_active,
        created_at=updated_user.created_at,
        updated_at=updated_user.updated_at
    )


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    current_user = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Change current user's password

    Requires current password for verification and new password (minimum 8 characters).
    """
    result = await user_service.change_password(
        str(current_user.id),
        password_data.current_password,
        password_data.new_password
    )
    return result


@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    current_user = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get current user's preferences

    Returns user's communication preferences, favorite cause, and privacy settings.
    """
    user = await user_service.get_user_profile(str(current_user.id))

    # Get preferences from user entity (with defaults)
    preferences = user.preferences or {}
    communication_prefs = preferences.get('communication_preferences', {
        'email_notifications': True,
        'sms_notifications': False,
        'monthly_reports': True
    })
    privacy_settings = preferences.get('privacy_settings', {
        'show_donations_publicly': False,
        'allow_contact': True
    })

    return UserPreferencesResponse(
        favorite_cause=preferences.get('favorite_cause', 'Programa General'),
        communication_preferences=communication_prefs,
        privacy_settings=privacy_settings
    )


@router.put("/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    preferences_data: UserPreferencesUpdate,
    current_user = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Update current user's preferences

    Updates communication preferences, favorite cause, and privacy settings.
    """
    # Get current preferences
    current_user_obj = await user_service.get_user_profile(str(current_user.id))
    current_prefs = current_user_obj.preferences or {}

    # Update preferences
    updated_prefs = current_prefs.copy()

    if preferences_data.communication_preferences:
        updated_prefs['communication_preferences'] = preferences_data.communication_preferences

    if preferences_data.privacy_settings:
        updated_prefs['privacy_settings'] = preferences_data.privacy_settings

    # Update user preferences
    await user_service.update_preferences(str(current_user.id), updated_prefs)

    # Return updated preferences
    return UserPreferencesResponse(
        favorite_cause=updated_prefs.get('favorite_cause', 'Programa General'),
        communication_preferences=updated_prefs.get('communication_preferences', {
            'email_notifications': True,
            'sms_notifications': False,
            'monthly_reports': True
        }),
        privacy_settings=updated_prefs.get('privacy_settings', {
            'show_donations_publicly': False,
            'allow_contact': True
        })
    )

