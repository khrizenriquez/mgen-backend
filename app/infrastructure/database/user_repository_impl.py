"""
User repository implementation using SQLAlchemy
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.database.models import SimpleUserModel


class UserRepositoryImpl(UserRepository):
    """User repository implementation"""

    def __init__(self, db: Session):
        self.db = db

    async def create(self, user: User) -> User:
        """Create a new user"""
        db_user = SimpleUserModel(
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        return self._to_domain(db_user)

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        db_user = self.db.query(SimpleUserModel).filter(SimpleUserModel.id == user_id).first()
        return self._to_domain(db_user) if db_user else None

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        db_user = self.db.query(SimpleUserModel).filter(SimpleUserModel.email == email).first()
        return self._to_domain(db_user) if db_user else None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination"""
        db_users = self.db.query(SimpleUserModel).offset(skip).limit(limit).all()
        return [self._to_domain(db_user) for db_user in db_users]

    async def update(self, user_id: int, user: User) -> Optional[User]:
        """Update user"""
        db_user = self.db.query(SimpleUserModel).filter(SimpleUserModel.id == user_id).first()
        if not db_user:
            return None

        db_user.email = user.email
        db_user.first_name = user.first_name
        db_user.last_name = user.last_name
        db_user.is_active = user.is_active
        
        self.db.commit()
        self.db.refresh(db_user)
        
        return self._to_domain(db_user)

    async def delete(self, user_id: int) -> bool:
        """Delete user"""
        db_user = self.db.query(SimpleUserModel).filter(SimpleUserModel.id == user_id).first()
        if not db_user:
            return False

        self.db.delete(db_user)
        self.db.commit()
        return True

    def _to_domain(self, db_user: SimpleUserModel) -> User:
        """Convert database model to domain entity"""
        return User(
            id=db_user.id,
            email=db_user.email,
            first_name=db_user.first_name,
            last_name=db_user.last_name,
            is_active=db_user.is_active,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at
        )