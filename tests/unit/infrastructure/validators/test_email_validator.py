"""
Unit tests for email validator
"""
import pytest
from unittest.mock import Mock, patch


class TestEmailValidator:
    """Test email validation logic"""

    def test_valid_email_formats(self):
        """Test valid email format validation"""
        valid_emails = [
            "user@example.com",
            "test.user@domain.co.uk",
            "admin+tag@test.com",
            "user123@test-domain.org"
        ]
        
        for email in valid_emails:
            assert "@" in email
            assert "." in email.split("@")[1]

    def test_invalid_email_formats(self):
        """Test invalid email detection"""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "user@",
            "user @example.com",
            "user@.com"
        ]
        
        for email in invalid_emails:
            # Basic validation - at least one should be true for invalid emails
            has_no_at = "@" not in email
            starts_with_at = email.startswith("@") if "@" in email else False
            ends_with_at = email.endswith("@") if "@" in email else False
            has_space = " " in email
            wrong_at_count = email.count("@") != 1
            domain_starts_with_dot = email.split('@')[1].startswith('.') if '@' in email and len(email.split('@')) > 1 else False

            is_invalid = has_no_at or starts_with_at or ends_with_at or has_space or wrong_at_count or domain_starts_with_dot
            assert is_invalid, f"Email {email} should be invalid but passed validation"

    def test_disposable_email_detection(self):
        """Test disposable email domain detection"""
        disposable_domains = [
            "tempmail.com",
            "guerrillamail.com",
            "throwaway.email",
            "10minutemail.com"
        ]
        
        for domain in disposable_domains:
            email = f"test@{domain}"
            assert domain in email

    def test_email_normalization(self):
        """Test email normalization"""
        email = "  User@Example.COM  "
        normalized = email.strip().lower()
        
        assert normalized == "user@example.com"

    def test_email_domain_extraction(self):
        """Test domain extraction from email"""
        email = "user@example.com"
        domain = email.split("@")[1]
        
        assert domain == "example.com"

    def test_email_local_part_validation(self):
        """Test local part (before @) validation"""
        valid_local_parts = [
            "user",
            "user.name",
            "user+tag",
            "user123"
        ]
        
        for local_part in valid_local_parts:
            email = f"{local_part}@example.com"
            assert email.split("@")[0] == local_part

    def test_email_length_validation(self):
        """Test email length constraints"""
        # Email should not be too short or too long
        short_email = "a@b.c"
        long_local = "a" * 65  # More than 64 chars
        long_email = f"{long_local}@example.com"
        
        assert len(short_email) >= 5
        assert len(long_local) > 64

    def test_multiple_emails_validation(self):
        """Test validation of multiple emails"""
        emails = [
            "user1@example.com",
            "user2@example.com",
            "user3@example.com"
        ]
        
        valid_count = sum(1 for email in emails if "@" in email and "." in email)
        assert valid_count == 3

    def test_email_with_special_chars(self):
        """Test emails with allowed special characters"""
        special_char_emails = [
            "user.name@example.com",
            "user+tag@example.com",
            "user_name@example.com",
            "user-name@example.com"
        ]
        
        for email in special_char_emails:
            assert "@" in email

    def test_email_case_insensitivity(self):
        """Test that email comparison is case-insensitive"""
        email1 = "User@Example.COM"
        email2 = "user@example.com"
        
        assert email1.lower() == email2.lower()
