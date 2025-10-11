"""
Custom formatters and PII masking utilities for logging
"""
import re
from typing import Any, Dict, Pattern


class PIIMasker:
    """Utility class to mask personally identifiable information in logs"""
    
    def __init__(self):
        # Compile regex patterns for better performance
        self.patterns: Dict[str, Pattern] = {
            'auth_token': re.compile(
                r'(?i)(bearer\s+|token[:\s]+|jwt[:\s]+|api[_-]?key[:\s]+)([a-zA-Z0-9._-]{20,})'
            ),
            'email': re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ),
            'phone': re.compile(
                r'\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
            ),
            'credit_card': re.compile(
                r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
            ),
            'ssn': re.compile(
                r'\b\d{3}-?\d{2}-?\d{4}\b'
            ),
            'password': re.compile(
                r'(?i)(password[:\s]+|pwd[:\s]+|pass[:\s]+)(.*)'
            ),
            'authorization': re.compile(
                r'(?i)(authorization[:\s]+)([^\s]{20,})'
            )
        }
        
        # Replacement patterns
        self.replacements = {
            'email': lambda m: f"{m.group(0).split('@')[0][:2]}***@{m.group(0).split('@')[1]}",
            'phone': '***-***-****',
            'credit_card': '****-****-****-****',
            'ssn': '***-**-****',
            'auth_token': lambda m: f"{m.group(1)}[MASKED_TOKEN]",
            'password': lambda m: f"{m.group(1)}[MASKED]",
            'authorization': lambda m: f"{m.group(1)}[MASKED_AUTH]"
        }
    
    def mask(self, text: str) -> str:
        """
        Mask PII in the given text
        
        Args:
            text: The text to mask PII in
            
        Returns:
            Text with PII masked
        """
        if not isinstance(text, str):
            return text
        
        masked_text = text
        
        for pattern_name, pattern in self.patterns.items():
            replacement = self.replacements[pattern_name]
            
            if callable(replacement):
                # Special handling for email and token patterns
                if pattern_name == 'email':
                    def email_replacer(match):
                        email = match.group(0)
                        if '@' in email:
                            local, domain = email.split('@', 1)
                            if len(local) > 2:
                                return f"{local[:2]}***@{domain}"
                            else:
                                return f"***@{domain}"
                        return '***@***.***'
                    
                    masked_text = pattern.sub(email_replacer, masked_text)
                else:
                    # For tokens and passwords
                    masked_text = pattern.sub(replacement, masked_text)
            else:
                # Simple string replacement
                masked_text = pattern.sub(replacement, masked_text)
        
        return masked_text
    
    def mask_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively mask PII in a dictionary
        
        Args:
            data: Dictionary to mask PII in
            
        Returns:
            Dictionary with PII masked
        """
        if not isinstance(data, dict):
            return data
        
        masked_data = {}
        
        for key, value in data.items():
            # Check if key indicates sensitive data
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in ['password', 'token', 'auth', 'secret', 'key']):
                if isinstance(value, str) and len(value) > 0:
                    masked_data[key] = '[MASKED]'
                else:
                    masked_data[key] = value
            elif isinstance(value, str):
                masked_data[key] = self.mask(value)
            elif isinstance(value, dict):
                masked_data[key] = self.mask_dict(value)
            elif isinstance(value, list):
                masked_data[key] = [
                    self.mask_dict(item) if isinstance(item, dict)
                    else self.mask(item) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                masked_data[key] = value
        
        return masked_data
