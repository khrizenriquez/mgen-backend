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
    DeleteResponse
)
from app.adapters.schemas.auth_schemas import UserInfo
from app.domain.entities.user import User
from app.domain.services.user_service import UserService
from app.infrastructure.database.user_repository_impl import UserRepositoryImpl
from app.infrastructure.database.database import get_db
from app.infrastructure.auth.dependencies import (
    get_current_active_user, require_role, require_admin, require_organization, require_any_role, user_to_user_info
)


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


@router.get("/", response_model=UserListResponse)
async def get_users(
    current_user = Depends(require_role("ORGANIZATION")),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get users with pagination (Admin/Organization only)

    - ADMIN: See all users in the system
    - ORGANIZATION: See users in their organization (TODO: implement organization filtering)

    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 10, max: 100)
    """
    users = await user_service.get_users(skip=skip, limit=limit)
    # Convert to UserInfo format for consistency with auth endpoints
    user_infos = []
    for user in users:
        # This is a simplified conversion - in a real app you'd have proper mapping
        user_infos.append(UserInfo(
            id=user.id if hasattr(user, 'id') else "unknown",
            email=user.email,
            email_verified=getattr(user, 'email_verified', False),
            is_active=getattr(user, 'is_active', True),
            roles=[],  # Would need to be populated from relationships
            created_at=getattr(user, 'created_at', None),
            updated_at=getattr(user, 'updated_at', None)
        ))
    return UserListResponse(
        users=user_infos,
        total=len(user_infos),
        skip=skip,
        limit=limit
    )


@router.get("/{user_id}", response_model=UserInfo)
async def get_user(
    user_id: int,
    current_user = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get user by ID

    Requires authentication. Users can only view their own profile unless they are admin or organization.

    - **user_id**: The ID of the user to retrieve
    """
    # Check if user is trying to access their own profile or has admin/organization role
    user_roles = [role.name for role in current_user.user_roles]
    if str(current_user.id) != str(user_id) and not any(role in user_roles for role in ["ADMIN", "ORGANIZATION"]):
        raise HTTPException(
            status_code=403,
            detail="You can only access your own profile"
        )

    user = await user_service.get_user(user_id)
    # Convert to UserInfo format
    return UserInfo(
        id=user.id if hasattr(user, 'id') else "unknown",
        email=user.email,
        email_verified=getattr(user, 'email_verified', False),
        is_active=getattr(user, 'is_active', True),
        roles=[],  # Would need to be populated from relationships
        created_at=getattr(user, 'created_at', None),
        updated_at=getattr(user, 'updated_at', None)
    )


@router.put("/{user_id}", response_model=UserInfo)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Update user by ID

    Requires authentication. Users can only update their own profile unless they are admin or organization.

    - **user_id**: The ID of the user to update
    - **email**: New email address (must be unique)
    - **first_name**: New first name
    - **last_name**: New last name
    - **is_active**: New active status
    """
    # Check if user is trying to update their own profile or has admin/organization role
    user_roles = [role.name for role in current_user.user_roles]
    if str(current_user.id) != str(user_id) and not any(role in user_roles for role in ["ADMIN", "ORGANIZATION"]):
        raise HTTPException(
            status_code=403,
            detail="You can only update your own profile"
        )

    user = User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        is_active=user_data.is_active
    )
    updated_user = await user_service.update_user(user_id, user)

    # Convert to UserInfo format
    return UserInfo(
        id=updated_user.id if hasattr(updated_user, 'id') else "unknown",
        email=updated_user.email,
        email_verified=getattr(updated_user, 'email_verified', False),
        is_active=getattr(updated_user, 'is_active', True),
        roles=[],  # Would need to be populated from relationships
        created_at=getattr(updated_user, 'created_at', None),
        updated_at=getattr(updated_user, 'updated_at', None)
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user = Depends(require_role("ADMIN")),
    user_service: UserService = Depends(get_user_service)
):
    """
    Delete user by ID

    Requires ADMIN role.
    """
    # Prevent users from deleting themselves
    if str(current_user.id) == str(user_id):
        raise HTTPException(
            status_code=400,
            detail="You cannot delete your own account"
        )

    result = await user_service.delete_user(user_id)
    return result

