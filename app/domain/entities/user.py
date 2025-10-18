"""
User domain entity
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """User domain entity"""
    id: Optional[int] = None
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    phone: Optional[str] = None
    address: Optional[str] = None
    preferences: Optional[dict] = None
    password_hash: Optional[str] = None
    email_verified: bool = False
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self) -> str:
        return f"User(id={self.id}, email={self.email}, name={self.full_name()})"