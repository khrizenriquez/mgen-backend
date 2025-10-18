"""
User repository implementation using SQLAlchemy
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.database.models import UserModel


class UserRepositoryImpl(UserRepository):
    """User repository implementation"""

    def __init__(self, db: Session):
        self.db = db

    async def create(self, user: User) -> User:
        """Create a new user"""
        db_user = UserModel(
            email=user.email,
            password_hash="",  # Will be set by auth service
            email_verified=False,
            is_active=user.is_active,
            organization_id=None  # Will be set by auth service if needed
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)

        return self._to_domain(db_user)

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        return self._to_domain(db_user) if db_user else None

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        db_user = self.db.query(UserModel).filter(UserModel.email == email).first()
        return self._to_domain(db_user) if db_user else None

    async def get_all(self, skip: int = 0, limit: int = 100, organization_id: Optional[str] = None) -> List[User]:
        """Get all users with pagination and optional organization filtering"""
        query = self.db.query(UserModel)

        if organization_id:
            query = query.filter(UserModel.organization_id == organization_id)

        db_users = query.offset(skip).limit(limit).all()
        return [self._to_domain(db_user) for db_user in db_users]

    async def update(self, user_id: int, user: User) -> Optional[User]:
        """Update user"""
        db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not db_user:
            return None

        db_user.email = user.email
        db_user.is_active = user.is_active
        if hasattr(user, 'first_name') and user.first_name is not None:
            db_user.first_name = user.first_name
        if hasattr(user, 'last_name') and user.last_name is not None:
            db_user.last_name = user.last_name
        if hasattr(user, 'phone') and user.phone is not None:
            db_user.phone = user.phone
        if hasattr(user, 'address') and user.address is not None:
            db_user.address = user.address
        if hasattr(user, 'preferences') and user.preferences is not None:
            db_user.preferences = user.preferences

        self.db.commit()
        self.db.refresh(db_user)

        return self._to_domain(db_user)

    async def delete(self, user_id: int) -> bool:
        """Delete user"""
        db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not db_user:
            return False

        self.db.delete(db_user)
        self.db.commit()
        return True

    async def update_profile(self, user_id: int, profile_data: dict) -> Optional[User]:
        """Update user profile fields"""
        db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not db_user:
            return None

        # Update only profile fields
        if 'first_name' in profile_data:
            db_user.first_name = profile_data['first_name']
        if 'last_name' in profile_data:
            db_user.last_name = profile_data['last_name']
        if 'phone' in profile_data:
            db_user.phone = profile_data['phone']
        if 'address' in profile_data:
            db_user.address = profile_data['address']

        # Update timestamp
        from datetime import datetime
        db_user.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(db_user)

        return self._to_domain(db_user)

    async def update_password(self, user_id: int, hashed_password: str) -> bool:
        """Update user password"""
        db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not db_user:
            return False

        db_user.password_hash = hashed_password

        # Update timestamp
        from datetime import datetime
        db_user.updated_at = datetime.utcnow()

        self.db.commit()
        return True

    async def update_preferences(self, user_id: int, preferences: dict) -> Optional[User]:
        """Update user preferences"""
        db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not db_user:
            return None

        db_user.preferences = preferences

        # Update timestamp
        from datetime import datetime
        db_user.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(db_user)

        return self._to_domain(db_user)

    async def get_by_id_with_password(self, user_id: int) -> Optional[User]:
        """Get user by ID including password hash"""
        db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not db_user:
            return None

        user = self._to_domain(db_user)
        user.password_hash = db_user.password_hash
        return user

    def _to_domain(self, db_user: UserModel) -> User:
        """Convert database model to domain entity"""
        return User(
            id=db_user.id,
            email=db_user.email,
            first_name=db_user.first_name or "",
            last_name=db_user.last_name or "",
            phone=db_user.phone,
            address=db_user.address,
            preferences=db_user.preferences or {},
            password_hash=None,  # Don't expose password hash in domain
            email_verified=db_user.email_verified,
            is_active=db_user.is_active,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at
        )