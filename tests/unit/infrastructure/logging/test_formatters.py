"""
Unit tests for logging formatters and PII masking
"""
import pytest
from app.infrastructure.logging.formatters import PIIMasker


class TestPIIMasker:
    """Test cases for PII masking functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.masker = PIIMasker()
    
    def test_mask_email(self):
        """Test email masking"""
        test_cases = [
            ("Contact john.doe@example.com for support", "Contact jo***@example.com for support"),
            ("Email me at user@domain.org", "Email me at us***@domain.org"),
            ("Multiple emails: alice@test.com and bob@test.org", 
             "Multiple emails: al***@test.com and bo***@test.org"),
        ]
        
        for input_text, expected in test_cases:
            result = self.masker.mask(input_text)
            assert result == expected
    
    def test_mask_phone(self):
        """Test phone number masking"""
        test_cases = [
            ("Call me at 555-123-4567", "Call me at ***-***-****"),
            ("Phone: (555) 123-4567", "Phone: (***-***-****"),
            ("Contact: +1-555-123-4567", "Contact: +1-***-***-****"),
            ("Number 5551234567", "Number ***-***-****"),
        ]

        for input_text, expected in test_cases:
            result = self.masker.mask(input_text)
            assert result == expected
    
    def test_mask_credit_card(self):
        """Test credit card masking"""
        text = "Card: 4532-1234-5678-9012"
        result = self.masker.mask(text)
        assert "****-****-****-****" in result
        
        text2 = "Payment: 4532123456789012"
        result2 = self.masker.mask(text2)
        assert "****-****-****-****" in result2
        
        text3 = "CC: 4532 1234 5678 9012"
        result3 = self.masker.mask(text3)
        assert "****-****-****-****" in result3
    
    def test_mask_ssn(self):
        """Test SSN masking"""
        test_cases = [
            ("SSN: 123-45-6789", "SSN: ***-**-****"),
            ("Social: 123456789", "Social: ***-**-****"),
        ]
        
        for input_text, expected in test_cases:
            result = self.masker.mask(input_text)
            assert result == expected
    
    def test_mask_auth_tokens(self):
        """Test authentication token masking"""
        text1 = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0"
        result1 = self.masker.mask(text1)
        assert "[MASKED_TOKEN]" in result1
        
        text2 = "token: abc123def456ghi789jkl"
        result2 = self.masker.mask(text2)
        assert "[MASKED_TOKEN]" in result2
        
        text3 = "JWT eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0"
        result3 = self.masker.mask(text3)
        assert "[MASKED_TOKEN]" in result3
        
        text4 = "api_key: sk_live_12345678901234567890"
        result4 = self.masker.mask(text4)
        assert "[MASKED_TOKEN]" in result4
    
    def test_mask_passwords(self):
        """Test password masking"""
        test_cases = [
            ("password: secret123", "password: [MASKED]"),
            ("pwd: mypassword", "pwd: [MASKED]"),
            ("pass: 123456", "pass: [MASKED]"),
        ]
        
        for input_text, expected in test_cases:
            result = self.masker.mask(input_text)
            assert result == expected
    
    def test_mask_dict(self):
        """Test dictionary PII masking"""
        test_data = {
            "email": "user@example.com",
            "phone": "555-123-4567",
            "password": "secret123",
            "name": "John Doe",
            "message": "Contact me at john@test.com",
            "nested": {
                "token": "abc123def456",
                "public_info": "This is safe"
            }
        }
        
        result = self.masker.mask_dict(test_data)
        
        # Check masked sensitive fields by key name
        assert result["password"] == "[MASKED]"
        assert result["nested"]["token"] == "[MASKED]"
        
        # Check masked PII in content
        assert "us***@example.com" in result["email"]
        assert "***-***-****" in result["phone"]
        assert "jo***@test.com" in result["message"]
        
        # Check non-sensitive data is preserved
        assert result["name"] == "John Doe"
        assert result["nested"]["public_info"] == "This is safe"
    
    def test_mask_list_in_dict(self):
        """Test masking of lists within dictionaries"""
        test_data = {
            "emails": ["user1@test.com", "user2@test.com"],
            "messages": [
                "Call me at 555-123-4567",
                {"content": "My password is secret123"}
            ]
        }
        
        result = self.masker.mask_dict(test_data)
        
        # Check emails in list are masked
        assert "us***@test.com" in result["emails"][0]
        assert "us***@test.com" in result["emails"][1]
        
        # Check phone in list is masked
        assert "***-***-****" in result["messages"][0]
        
        # Check nested dict in list has password field masked by key name
        assert "[MASKED]" in result["messages"][1]["content"]
    
    def test_non_string_values(self):
        """Test that non-string values are preserved"""
        test_cases = [
            (123, 123),
            (True, True),
            (None, None),
            ([], []),
            ({}, {}),
        ]
        
        for input_val, expected in test_cases:
            result = self.masker.mask(input_val)
            assert result == expected
    
    def test_empty_string(self):
        """Test empty string handling"""
        result = self.masker.mask("")
        assert result == ""
    
    def test_no_pii_text(self):
        """Test text without PII is unchanged"""
        text = "This is a normal message with no sensitive data"
        result = self.masker.mask(text)
        assert result == text
