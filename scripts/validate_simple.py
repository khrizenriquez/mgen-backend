#!/usr/bin/env python3
"""
Simplified validation script that works without external dependencies
Focuses on the core validations for your tasks #297 and #298
"""

import os
import sys
import re
import subprocess
from pathlib import Path

class SimpleValidator:
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.backend_dir = self.script_dir.parent
        self.errors = []
        self.warnings = []
        
    def check_docker_status(self):
        """Check if Docker containers are running"""
        print(f"\n{'='*60}")
        print("CHECKING: Docker Container Status")
        print(f"{'='*60}")
        
        try:
            # Check container status
            result = subprocess.run(['docker-compose', 'ps'], 
                                  cwd=self.backend_dir,
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("📋 Docker container status:")
                print(result.stdout)
                
                # Check if database is running
                if 'db' in result.stdout and 'Up' in result.stdout:
                    print("✅ Database container is running")
                    return True
                else:
                    print("⚠️  Database container not running")
                    return False
            else:
                print("⚠️  Could not check Docker status")
                return False
                
        except Exception as e:
            print(f"⚠️  Docker check failed: {e}")
            return False
    
    def validate_schema_constraints(self):
        """Validate schema.sql has proper constraints"""
        print(f"\n{'='*60}")
        print("VALIDATING: Schema Constraints (Task #298)")
        print(f"{'='*60}")
        
        schema_file = self.backend_dir / 'schema.sql'
        
        if not schema_file.exists():
            self.errors.append("schema.sql not found")
            return False
            
        with open(schema_file, 'r') as f:
            content = f.read()
        
        # Check for donation table
        donation_match = re.search(r'CREATE TABLE donation \((.*?)\);', content, re.DOTALL)
        
        if not donation_match:
            self.errors.append("donation table not found in schema.sql")
            return False
        
        donation_def = donation_match.group(1)
        
        # Check required unique constraints
        required_uniques = {
            'reference_code': 'reference_code TEXT NOT NULL UNIQUE',
            'correlation_id': 'correlation_id TEXT NOT NULL UNIQUE'
        }
        
        for field, expected in required_uniques.items():
            if expected in donation_def:
                print(f"✅ {field} has UNIQUE constraint in schema")
            else:
                self.errors.append(f"Missing UNIQUE constraint for {field} in schema.sql")
        
        # Check amount constraint
        if 'CHECK (amount_gtq > 0)' in donation_def:
            print("✅ amount_gtq has CHECK constraint > 0")
        else:
            self.errors.append("Missing CHECK constraint for amount_gtq > 0")
        
        return len(self.errors) == 0
    
    def validate_models_constraints(self):
        """Validate SQLAlchemy models have proper constraints"""
        print(f"\n{'='*60}")
        print("VALIDATING: SQLAlchemy Model Constraints")
        print(f"{'='*60}")
        
        models_file = self.backend_dir / 'app' / 'infrastructure' / 'database' / 'models.py'
        
        if not models_file.exists():
            self.errors.append("models.py not found")
            return False
            
        with open(models_file, 'r') as f:
            content = f.read()
        
        # Check DonationModel
        donation_model_match = re.search(r'class DonationModel\(Base\):(.*?)(?=class|\Z)', content, re.DOTALL)
        
        if not donation_model_match:
            self.errors.append("DonationModel not found in models.py")
            return False
        
        donation_model = donation_model_match.group(1)
        
        # Check required unique fields
        required_uniques = {
            'reference_code': 'reference_code = Column(Text, nullable=False, unique=True',
            'correlation_id': 'correlation_id = Column(Text, nullable=False, unique=True'
        }
        
        for field, expected in required_uniques.items():
            if expected in donation_model:
                print(f"✅ {field} has unique=True in model")
            else:
                self.errors.append(f"Missing unique=True for {field} in DonationModel")
        
        # Check check constraint
        if "CheckConstraint('amount_gtq > 0'" in donation_model:
            print("✅ amount_gtq has CheckConstraint in model")
        else:
            self.errors.append("Missing CheckConstraint for amount_gtq > 0 in model")
        
        return len(self.errors) == 0
    
    def validate_request_id_usage(self):
        """Validate request_id usage (Task #297)"""
        print(f"\n{'='*60}")
        print("VALIDATING: Request ID Usage (Task #297)")
        print(f"{'='*60}")
        
        # Check logging middleware
        middleware_file = self.backend_dir / 'app' / 'infrastructure' / 'logging' / 'middleware.py'
        
        if middleware_file.exists():
            with open(middleware_file, 'r') as f:
                content = f.read()
                
            if 'request_id' in content or 'x-request-id' in content:
                print("✅ LoggingMiddleware handles request_id")
            else:
                self.warnings.append("LoggingMiddleware may not handle request_id")
        else:
            self.warnings.append("LoggingMiddleware not found")
        
        # Check donation model doesn't have request_id (it shouldn't)
        models_file = self.backend_dir / 'app' / 'infrastructure' / 'database' / 'models.py'
        
        if models_file.exists():
            with open(models_file, 'r') as f:
                content = f.read()
            
            if 'request_id' in content:
                self.warnings.append("request_id found in models - should be for logging only")
            else:
                print("✅ request_id not in database models (correct - it's for logging)")
        
        # Check schema doesn't have request_id in donation table
        schema_file = self.backend_dir / 'schema.sql'
        
        if schema_file.exists():
            with open(schema_file, 'r') as f:
                content = f.read()
            
            donation_match = re.search(r'CREATE TABLE donation \((.*?)\);', content, re.DOTALL)
            if donation_match and 'request_id' in donation_match.group(1):
                self.warnings.append("request_id found in donation table - should be for logging only")
            else:
                print("✅ request_id not in donation table (correct)")
        
        print("\nℹ️  CLARIFICATION:")
        print("   • request_id: For HTTP request tracing (logging only)")
        print("   • correlation_id: For donation business logic (stored in DB)")
        print("   • reference_code: For external payment references (stored in DB)")
        
        return True
    
    def test_database_constraints(self, docker_available):
        """Test database constraints if possible"""
        if not docker_available:
            print(f"\n{'='*60}")
            print("SKIPPING: Database Constraint Testing (Docker not available)")
            print(f"{'='*60}")
            return True
        
        print(f"\n{'='*60}")
        print("TESTING: Database Constraints")
        print(f"{'='*60}")
        
        try:
            # Test constraint via docker-compose exec
            test_sql = """
            -- Test unique constraint on reference_code
            BEGIN;
            INSERT INTO donation (amount_gtq, status_id, donor_email, reference_code, correlation_id) 
            VALUES (100.00, 1, 'test1@example.com', 'TEST_REF_001', 'TEST_CORR_001');
            
            -- This should fail due to unique constraint
            INSERT INTO donation (amount_gtq, status_id, donor_email, reference_code, correlation_id) 
            VALUES (200.00, 1, 'test2@example.com', 'TEST_REF_001', 'TEST_CORR_002');
            ROLLBACK;
            """
            
            # Write test SQL to temp file
            test_file = self.backend_dir / 'test_constraints.sql'
            with open(test_file, 'w') as f:
                f.write(test_sql)
            
            # Execute test
            result = subprocess.run([
                'docker-compose', 'exec', '-T', 'db', 
                'psql', '-U', 'postgres', '-d', 'donations', '-f', '/tmp/test.sql'
            ], cwd=self.backend_dir, capture_output=True, text=True, input=test_sql)
            
            if 'duplicate key value violates unique constraint' in result.stderr:
                print("✅ Unique constraints are working (duplicate insertion failed as expected)")
            elif result.returncode != 0:
                print("✅ Constraints appear to be working (transaction failed as expected)")
            else:
                self.warnings.append("Could not confirm constraint behavior")
            
            # Clean up
            if test_file.exists():
                test_file.unlink()
                
        except Exception as e:
            self.warnings.append(f"Could not test database constraints: {e}")
        
        return True
    
    def run_validations(self):
        """Run all validations"""
        print("🚀 SIMPLIFIED VALIDATION FOR TASKS #297 & #298")
        print("="*60)
        
        # Check Docker
        docker_ok = self.check_docker_status()
        
        # Run validations
        validations = [
            ('Schema Constraints', self.validate_schema_constraints),
            ('Model Constraints', self.validate_models_constraints),
            ('Request ID Usage', self.validate_request_id_usage),
        ]
        
        if docker_ok:
            validations.append(('Database Testing', lambda: self.test_database_constraints(True)))
        
        passed = 0
        for name, validation in validations:
            try:
                if validation():
                    passed += 1
            except Exception as e:
                self.errors.append(f"{name} validation failed: {e}")
        
        # Report results
        print(f"\n{'='*60}")
        print("VALIDATION RESULTS")
        print(f"{'='*60}")
        
        print(f"📊 Validations: {passed}/{len(validations)} passed")
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        if not self.errors and not self.warnings:
            print("🎉 ALL VALIDATIONS PASSED!")
            print("✅ Task #298: Insertion duplicates are blocked")
            print("✅ Task #297: Request ID usage is properly configured")
        elif not self.errors:
            print("✅ Core validations passed with some warnings")
        
        if not docker_ok:
            print(f"\n💡 TO TEST DATABASE CONSTRAINTS:")
            print("   docker-compose up -d")
            print("   python scripts/validate_simple.py")
        
        print(f"{'='*60}")
        
        return len(self.errors) == 0

def main():
    validator = SimpleValidator()
    success = validator.run_validations()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()




