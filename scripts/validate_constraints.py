#!/usr/bin/env python3
"""
Script to validate database constraints and model synchronization
Run this script to ensure:
1. All UNIQUE constraints are properly enforced
2. Models match the actual database schema
3. No duplicate data can be inserted
"""

import asyncio
import os
import sys
from uuid import uuid4
from decimal import Decimal
from datetime import datetime

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import text, inspect
from sqlalchemy.exc import IntegrityError
from app.infrastructure.database.database import get_engine, get_db
from app.infrastructure.database.models import DonationModel, StatusCatalogModel
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)

class DatabaseValidator:
    def __init__(self):
        self.engine = None
        self.errors = []
        self.warnings = []
        
    async def setup(self):
        """Initialize database connection"""
        self.engine = get_engine()
        logger.info("Database validator initialized")
        
    async def validate_table_structure(self):
        """Validate that table structure matches models"""
        logger.info("Validating table structure...")
        
        async with self.engine.begin() as conn:
            # Check if donation table exists
            result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'donation' 
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            if not columns:
                self.errors.append("donation table does not exist")
                return
                
            expected_columns = {
                'id': 'uuid',
                'amount_gtq': 'numeric',
                'status_id': 'integer',
                'created_at': 'timestamp with time zone',
                'updated_at': 'timestamp with time zone',
                'paid_at': 'timestamp with time zone',
                'donor_email': 'text',
                'donor_name': 'text',
                'donor_nit': 'text',
                'user_id': 'uuid',
                'payu_order_id': 'text',
                'reference_code': 'text',
                'correlation_id': 'text'
            }
            
            actual_columns = {col.column_name: col.data_type for col in columns}
            
            for col_name, expected_type in expected_columns.items():
                if col_name not in actual_columns:
                    self.errors.append(f"Missing column: {col_name}")
                elif actual_columns[col_name] != expected_type:
                    self.warnings.append(
                        f"Column {col_name} type mismatch: "
                        f"expected {expected_type}, got {actual_columns[col_name]}"
                    )
            
            logger.info(f"Table structure validation completed. Found {len(self.errors)} errors, {len(self.warnings)} warnings")
    
    async def validate_unique_constraints(self):
        """Validate UNIQUE constraints are properly enforced"""
        logger.info("Validating UNIQUE constraints...")
        
        async with self.engine.begin() as conn:
            # Check unique constraints exist
            result = await conn.execute(text("""
                SELECT tc.constraint_name, kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = 'donation' 
                AND tc.constraint_type = 'UNIQUE'
            """))
            
            constraints = result.fetchall()
            unique_columns = {row.column_name for row in constraints}
            
            expected_unique = {'reference_code', 'correlation_id'}
            
            for col in expected_unique:
                if col not in unique_columns:
                    self.errors.append(f"Missing UNIQUE constraint on {col}")
                else:
                    logger.info(f"✓ UNIQUE constraint found on {col}")
    
    async def test_duplicate_prevention(self):
        """Test that duplicate values are actually prevented"""
        logger.info("Testing duplicate prevention...")
        
        # Generate test data
        test_reference = f"TEST_REF_{uuid4().hex[:8]}"
        test_correlation = f"TEST_CORR_{uuid4().hex[:8]}"
        
        async with self.engine.begin() as conn:
            try:
                # Insert first donation
                await conn.execute(text("""
                    INSERT INTO donation (
                        amount_gtq, status_id, donor_email, 
                        reference_code, correlation_id
                    ) VALUES (
                        100.00, 1, 'test@example.com',
                        :ref_code, :corr_id
                    )
                """), {
                    'ref_code': test_reference,
                    'corr_id': test_correlation
                })
                
                logger.info("✓ First test donation inserted successfully")
                
                # Try to insert duplicate reference_code
                try:
                    await conn.execute(text("""
                        INSERT INTO donation (
                            amount_gtq, status_id, donor_email, 
                            reference_code, correlation_id
                        ) VALUES (
                            200.00, 1, 'test2@example.com',
                            :ref_code, :corr_id
                        )
                    """), {
                        'ref_code': test_reference,  # Same reference_code
                        'corr_id': f"DIFF_{uuid4().hex[:8]}"  # Different correlation_id
                    })
                    
                    self.errors.append("Duplicate reference_code was allowed - constraint not working!")
                    
                except Exception as e:
                    if "duplicate key value" in str(e) or "unique constraint" in str(e).lower():
                        logger.info("✓ Duplicate reference_code correctly prevented")
                    else:
                        self.errors.append(f"Unexpected error on duplicate reference_code: {e}")
                
                # Try to insert duplicate correlation_id
                try:
                    await conn.execute(text("""
                        INSERT INTO donation (
                            amount_gtq, status_id, donor_email, 
                            reference_code, correlation_id
                        ) VALUES (
                            300.00, 1, 'test3@example.com',
                            :ref_code, :corr_id
                        )
                    """), {
                        'ref_code': f"DIFF_{uuid4().hex[:8]}",  # Different reference_code
                        'corr_id': test_correlation  # Same correlation_id
                    })
                    
                    self.errors.append("Duplicate correlation_id was allowed - constraint not working!")
                    
                except Exception as e:
                    if "duplicate key value" in str(e) or "unique constraint" in str(e).lower():
                        logger.info("✓ Duplicate correlation_id correctly prevented")
                    else:
                        self.errors.append(f"Unexpected error on duplicate correlation_id: {e}")
                
                # Clean up test data
                await conn.execute(text("""
                    DELETE FROM donation 
                    WHERE reference_code = :ref_code 
                    OR correlation_id = :corr_id
                """), {
                    'ref_code': test_reference,
                    'corr_id': test_correlation
                })
                
                logger.info("✓ Test data cleaned up")
                
            except Exception as e:
                self.errors.append(f"Failed to test duplicate prevention: {e}")
    
    async def validate_check_constraints(self):
        """Validate CHECK constraints are working"""
        logger.info("Validating CHECK constraints...")
        
        async with self.engine.begin() as conn:
            # Test positive amount constraint
            try:
                await conn.execute(text("""
                    INSERT INTO donation (
                        amount_gtq, status_id, donor_email, 
                        reference_code, correlation_id
                    ) VALUES (
                        -100.00, 1, 'test@example.com',
                        :ref_code, :corr_id
                    )
                """), {
                    'ref_code': f"NEG_TEST_{uuid4().hex[:8]}",
                    'corr_id': f"NEG_CORR_{uuid4().hex[:8]}"
                })
                
                self.errors.append("Negative amount was allowed - check constraint not working!")
                
            except Exception as e:
                if "check constraint" in str(e).lower() or "amount_gtq" in str(e):
                    logger.info("✓ Negative amount correctly prevented")
                else:
                    self.warnings.append(f"Unexpected error on negative amount: {e}")
    
    async def validate_foreign_keys(self):
        """Validate foreign key constraints"""
        logger.info("Validating foreign key constraints...")
        
        async with self.engine.begin() as conn:
            # Check if status_catalog has required values
            result = await conn.execute(text("""
                SELECT id, code FROM status_catalog 
                WHERE id IN (1, 2, 3, 4)
                ORDER BY id
            """))
            
            statuses = result.fetchall()
            required_statuses = {1, 2, 3, 4}
            actual_statuses = {row.id for row in statuses}
            
            missing_statuses = required_statuses - actual_statuses
            if missing_statuses:
                self.errors.append(f"Missing required status IDs: {missing_statuses}")
            else:
                logger.info("✓ All required status catalog entries found")
            
            # Test invalid foreign key
            try:
                await conn.execute(text("""
                    INSERT INTO donation (
                        amount_gtq, status_id, donor_email, 
                        reference_code, correlation_id
                    ) VALUES (
                        100.00, 999, 'test@example.com',
                        :ref_code, :corr_id
                    )
                """), {
                    'ref_code': f"FK_TEST_{uuid4().hex[:8]}",
                    'corr_id': f"FK_CORR_{uuid4().hex[:8]}"
                })
                
                self.errors.append("Invalid status_id was allowed - foreign key constraint not working!")
                
            except Exception as e:
                if "foreign key constraint" in str(e).lower() or "violates foreign key" in str(e).lower():
                    logger.info("✓ Invalid status_id correctly prevented")
                else:
                    self.warnings.append(f"Unexpected error on invalid FK: {e}")
    
    async def run_all_validations(self):
        """Run all validation checks"""
        logger.info("Starting comprehensive database validation...")
        
        await self.setup()
        
        validations = [
            self.validate_table_structure,
            self.validate_unique_constraints,
            self.validate_check_constraints,
            self.validate_foreign_keys,
            self.test_duplicate_prevention,
        ]
        
        for validation in validations:
            try:
                await validation()
            except Exception as e:
                self.errors.append(f"Validation {validation.__name__} failed: {e}")
                logger.error(f"Validation error in {validation.__name__}: {e}", exc_info=True)
        
        # Report results
        print("\n" + "="*60)
        print("DATABASE VALIDATION RESULTS")
        print("="*60)
        
        if not self.errors and not self.warnings:
            print("✅ ALL VALIDATIONS PASSED")
            print("Database constraints are properly configured and working!")
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
        
        return len(self.errors) == 0

async def main():
    """Main validation function"""
    validator = DatabaseValidator()
    success = await validator.run_all_validations()
    
    if success:
        print("\n🎉 Database validation completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Database validation failed. Please fix the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
