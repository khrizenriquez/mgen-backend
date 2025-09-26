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
from app.domain.entities.user import User
from app.domain.services.user_service import UserService
from app.infrastructure.database.user_repository_impl import UserRepositoryImpl
from app.infrastructure.database.database import get_db


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


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get all users with pagination
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 10, max: 100)
    """
    users = await user_service.get_users(skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """
    Get user by ID
    
    - **user_id**: The ID of the user to retrieve
    """
    return await user_service.get_user(user_id)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    user_service: UserService = Depends(get_user_service)
):
    """
    Update user by ID
    
    - **user_id**: The ID of the user to update
    - **email**: New email address (must be unique)
    - **first_name**: New first name
    - **last_name**: New last name
    - **is_active**: New active status
    """
    user = User(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        is_active=user_data.is_active
    )
    return await user_service.update_user(user_id, user)


@router.delete("/{user_id}", response_model=DeleteResponse)
async def delete_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """
    Delete user by ID
    
    - **user_id**: The ID of the user to delete
    """
    return await user_service.delete_user(user_id)