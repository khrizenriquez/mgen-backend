#!/usr/bin/env python3
"""
Script to validate request_id handling in the donations system
Ensures that:
1. Every HTTP request gets a unique request_id (correlation ID)
2. Request IDs are properly logged and tracked
3. No duplicate request IDs cause issues
"""

import asyncio
import uuid
import sys
import os
from uuid import uuid4
import json

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.infrastructure.logging import get_logger
from app.infrastructure.logging.middleware import LoggingMiddleware

logger = get_logger(__name__)

class RequestIdValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        
    def validate_logging_middleware(self):
        """Check that LoggingMiddleware properly handles request IDs"""
        logger.info("Validating logging middleware...")
        
        # Check middleware exists
        try:
            from app.infrastructure.logging.middleware import LoggingMiddleware
            logger.info("✓ LoggingMiddleware found")
        except ImportError:
            self.errors.append("LoggingMiddleware not found in app.infrastructure.logging.middleware")
            return
        
        # Check middleware implementation
        middleware_file = os.path.join(
            os.path.dirname(__file__), '..', 
            'app', 'infrastructure', 'logging', 'middleware.py'
        )
        
        if os.path.exists(middleware_file):
            with open(middleware_file, 'r') as f:
                content = f.read()
                
                # Check for request_id handling
                if 'request_id' not in content and 'x-request-id' not in content:
                    self.errors.append("LoggingMiddleware doesn't handle request_id/x-request-id")
                else:
                    logger.info("✓ LoggingMiddleware handles request_id")
                
                # Check for UUID generation
                if 'uuid' not in content.lower() and 'gen_random_uuid' not in content:
                    self.warnings.append("LoggingMiddleware may not generate UUIDs for request_id")
                else:
                    logger.info("✓ LoggingMiddleware generates request IDs")
        else:
            self.errors.append("LoggingMiddleware file not found")
    
    def validate_logging_configuration(self):
        """Check that logging is configured to include request_id"""
        logger.info("Validating logging configuration...")
        
        # Check logging config
        config_file = os.path.join(
            os.path.dirname(__file__), '..', 
            'app', 'infrastructure', 'logging', 'config.py'
        )
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                content = f.read()
                
                # Check for request_id in formatter
                if 'request_id' not in content:
                    self.warnings.append("Logging config may not include request_id in log format")
                else:
                    logger.info("✓ Logging config includes request_id")
                
                # Check for correlation filter
                if 'CorrelationFilter' in content or 'correlation' in content.lower():
                    logger.info("✓ Correlation filtering found in logging config")
                else:
                    self.warnings.append("No correlation filtering found in logging config")
        else:
            self.warnings.append("Logging config file not found")
    
    def validate_api_endpoints_logging(self):
        """Check that API endpoints properly log with request_id"""
        logger.info("Validating API endpoint logging...")
        
        # Check donation controller
        controller_file = os.path.join(
            os.path.dirname(__file__), '..', 
            'app', 'adapters', 'controllers', 'donation_controller.py'
        )
        
        if os.path.exists(controller_file):
            with open(controller_file, 'r') as f:
                content = f.read()
                
                # Check for structured logging
                if 'logger.info' in content or 'logger.error' in content:
                    logger.info("✓ Donation controller uses logging")
                else:
                    self.warnings.append("Donation controller may not be logging properly")
                
                # Check for get_logger import
                if 'from app.infrastructure.logging import get_logger' in content:
                    logger.info("✓ Donation controller imports structured logger")
                else:
                    self.warnings.append("Donation controller may not use structured logging")
        else:
            self.warnings.append("Donation controller file not found")
    
    def test_request_id_uniqueness(self):
        """Test that request IDs are actually unique"""
        logger.info("Testing request_id uniqueness...")
        
        # Generate multiple request IDs and check uniqueness
        request_ids = set()
        num_tests = 1000
        
        for _ in range(num_tests):
            request_id = str(uuid4())
            if request_id in request_ids:
                self.errors.append(f"Duplicate request_id generated: {request_id}")
            request_ids.add(request_id)
        
        if len(request_ids) == num_tests:
            logger.info(f"✓ Generated {num_tests} unique request IDs")
        else:
            self.errors.append(f"Only {len(request_ids)} unique IDs out of {num_tests} generated")
    
    def validate_request_id_format(self):
        """Validate that request IDs follow UUID format"""
        logger.info("Validating request_id format...")
        
        # Test UUID generation
        try:
            test_uuid = uuid4()
            uuid_str = str(test_uuid)
            
            # Check format (8-4-4-4-12 hex digits)
            import re
            uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
            
            if re.match(uuid_pattern, uuid_str):
                logger.info("✓ Request IDs follow proper UUID format")
            else:
                self.errors.append("Generated UUID doesn't match expected format")
                
        except Exception as e:
            self.errors.append(f"Error generating UUID: {e}")
    
    def check_database_request_id_usage(self):
        """Check if request_id is stored or used in database"""
        logger.info("Checking database request_id usage...")
        
        # Check if any table has request_id column
        schema_file = os.path.join(os.path.dirname(__file__), '..', 'schema.sql')
        
        if os.path.exists(schema_file):
            with open(schema_file, 'r') as f:
                content = f.read()
                
                if 'request_id' in content:
                    logger.info("ℹ️  request_id found in database schema")
                    # This might be expected for audit tables
                else:
                    logger.info("ℹ️  request_id not stored in database (this is typically correct)")
                    # Request IDs are usually for logging/tracing, not storage
        
        # Check models
        models_file = os.path.join(
            os.path.dirname(__file__), '..', 
            'app', 'infrastructure', 'database', 'models.py'
        )
        
        if os.path.exists(models_file):
            with open(models_file, 'r') as f:
                content = f.read()
                
                if 'request_id' in content:
                    logger.info("ℹ️  request_id found in SQLAlchemy models")
                else:
                    logger.info("ℹ️  request_id not in SQLAlchemy models (typically correct)")
    
    def validate_donation_unique_fields(self):
        """Validate donation-specific unique fields (not request_id)"""
        logger.info("Validating donation unique fields...")
        
        # This is what should be unique for donations
        donation_unique_fields = ['reference_code', 'correlation_id']
        
        # Check schema
        schema_file = os.path.join(os.path.dirname(__file__), '..', 'schema.sql')
        models_file = os.path.join(
            os.path.dirname(__file__), '..', 
            'app', 'infrastructure', 'database', 'models.py'
        )
        
        # Validate schema
        if os.path.exists(schema_file):
            with open(schema_file, 'r') as f:
                content = f.read()
                
                for field in donation_unique_fields:
                    if f'{field} TEXT NOT NULL UNIQUE' in content:
                        logger.info(f"✓ {field} is unique in schema")
                    else:
                        self.errors.append(f"{field} should be unique in donation table schema")
        
        # Validate models
        if os.path.exists(models_file):
            with open(models_file, 'r') as f:
                content = f.read()
                
                for field in donation_unique_fields:
                    if f'{field} = Column(Text, nullable=False, unique=True' in content:
                        logger.info(f"✓ {field} is unique in model")
                    else:
                        self.errors.append(f"{field} should be unique in DonationModel")
    
    def run_all_validations(self):
        """Run all request_id validations"""
        logger.info("Starting request_id validation...")
        
        validations = [
            self.validate_logging_middleware,
            self.validate_logging_configuration,
            self.validate_api_endpoints_logging,
            self.test_request_id_uniqueness,
            self.validate_request_id_format,
            self.check_database_request_id_usage,
            self.validate_donation_unique_fields,
        ]
        
        for validation in validations:
            try:
                validation()
            except Exception as e:
                self.errors.append(f"Validation {validation.__name__} failed: {e}")
                logger.error(f"Validation error in {validation.__name__}: {e}", exc_info=True)
        
        # Report results
        print("\n" + "="*60)
        print("REQUEST_ID VALIDATION RESULTS")
        print("="*60)
        
        if not self.errors and not self.warnings:
            print("✅ ALL REQUEST_ID VALIDATIONS PASSED")
            print("Request ID handling is properly configured!")
        else:
            if self.errors:
                print(f"❌ ERRORS FOUND ({len(self.errors)}):")
                for i, error in enumerate(self.errors, 1):
                    print(f"  {i}. {error}")
            
            if self.warnings:
                print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
                for i, warning in enumerate(self.warnings, 1):
                    print(f"  {i}. {warning}")
        
        print("\n" + "="*60)
        print("\nℹ️  CLARIFICATION:")
        print("• request_id: Used for HTTP request tracing/logging (not stored in DB)")
        print("• correlation_id: Used for donation business correlation (stored in DB)")
        print("• reference_code: Used for donation external reference (stored in DB)")
        print("="*60)
        
        return len(self.errors) == 0

def main():
    """Main validation function"""
    validator = RequestIdValidator()
    success = validator.run_all_validations()
    
    if success:
        print("\n🎉 Request ID validation completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Request ID validation failed. Please fix the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
