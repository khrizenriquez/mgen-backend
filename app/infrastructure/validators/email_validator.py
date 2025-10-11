"""
Email validation utilities
"""
import re
import dns.resolver
from typing import Tuple
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class EmailValidator:
    """Email validator with domain and DNS verification"""
    
    # Lista de dominios de emails desechables/temporales comunes
    DISPOSABLE_EMAIL_DOMAINS = {
        '10minutemail.com', 'guerrillamail.com', 'mailinator.com',
        'tempmail.com', 'throwaway.email', 'yopmail.com',
        'trashmail.com', 'maildrop.cc', 'getnada.com',
        'temp-mail.org', 'fakeinbox.com', 'sharklasers.com'
    }
    
    @staticmethod
    def is_valid_email_format(email: str) -> bool:
        """
        Validate email format using regex
        
        Args:
            email: Email address to validate
            
        Returns:
            bool: True if format is valid
        """
        # RFC 5322 simplified regex
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def is_disposable_email(email: str) -> bool:
        """
        Check if email is from a disposable/temporary email service
        
        Args:
            email: Email address to check
            
        Returns:
            bool: True if email is from a disposable service
        """
        domain = email.split('@')[-1].lower()
        return domain in EmailValidator.DISPOSABLE_EMAIL_DOMAINS
    
    @staticmethod
    def check_mx_records(domain: str) -> bool:
        """
        Check if domain has valid MX (Mail Exchange) records
        
        Args:
            domain: Domain to check
            
        Returns:
            bool: True if domain has valid MX records
        """
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            return len(mx_records) > 0
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
            logger.warning(f"No MX records found for domain: {domain}")
            return False
        except Exception as e:
            logger.error(f"Error checking MX records for {domain}: {e}")
            return False
    
    @staticmethod
    def validate_email(email: str, check_mx: bool = True, allow_disposable: bool = False) -> Tuple[bool, str]:
        """
        Comprehensive email validation
        
        Args:
            email: Email address to validate
            check_mx: Whether to check MX records
            allow_disposable: Whether to allow disposable email addresses
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        # Check format
        if not EmailValidator.is_valid_email_format(email):
            return False, "Invalid email format"
        
        # Check if disposable
        if not allow_disposable and EmailValidator.is_disposable_email(email):
            return False, "Disposable email addresses are not allowed"
        
        # Check MX records
        if check_mx:
            domain = email.split('@')[-1]
            if not EmailValidator.check_mx_records(domain):
                return False, f"Domain {domain} does not accept emails (no MX records found)"
        
        return True, ""


def validate_email_for_registration(email: str) -> Tuple[bool, str]:
    """
    Validate email for user registration
    Uses strict validation: checks format, rejects disposable emails, and verifies MX records
    
    Args:
        email: Email address to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    validator = EmailValidator()
    return validator.validate_email(
        email=email,
        check_mx=True,
        allow_disposable=False
    )
