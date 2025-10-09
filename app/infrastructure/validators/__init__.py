"""
Validators module
"""
from app.infrastructure.validators.email_validator import (
    EmailValidator,
    validate_email_for_registration
)

__all__ = [
    'EmailValidator',
    'validate_email_for_registration'
]
