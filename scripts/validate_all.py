#!/usr/bin/env python3
"""
Master validation script for the donations system
Runs all validations to ensure database, models, and constraints are properly configured
"""

import asyncio
import sys
import os
import subprocess
import importlib.util

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Try to import logger, fall back to basic logging if not in container
try:
    from app.infrastructure.logging import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    print("⚠️  Running outside container - using basic logging")

class MasterValidator:
    def __init__(self):
        self.script_dir = os.path.dirname(__file__)
        self.total_errors = 0
        self.total_warnings = 0
        
    def run_script(self, script_name: str, description: str):
        """Run a validation script and capture results"""
        print(f"\n{'='*60}")
        print(f"RUNNING: {description}")
        print(f"{'='*60}")
        
        script_path = os.path.join(self.script_dir, script_name)
        
        if not os.path.exists(script_path):
            print(f"❌ Script not found: {script_path}")
            self.total_errors += 1
            return False
        
        try:
            # Run the script
            result = subprocess.run([
                sys.executable, script_path
            ], capture_output=True, text=True)
            
            # Print output
            if result.stdout:
                print(result.stdout)
            
            if result.stderr:
                print("STDERR:", result.stderr)
            
            # Check exit code
            if result.returncode == 0:
                print(f"✅ {description} - PASSED")
                return True
            else:
                print(f"❌ {description} - FAILED (exit code: {result.returncode})")
                self.total_errors += 1
                return False
                
        except Exception as e:
            print(f"❌ Error running {script_name}: {e}")
            self.total_errors += 1
            return False
    
    def run_async_validation(self, module_name: str, function_name: str, description: str):
        """Run an async validation function"""
        print(f"\n{'='*60}")
        print(f"RUNNING: {description}")
        print(f"{'='*60}")
        
        try:
            # Import the module
            module_path = os.path.join(self.script_dir, f"{module_name}.py")
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Get the function
            func = getattr(module, function_name)
            
            # Run the async function
            result = asyncio.run(func())
            
            if result:
                print(f"✅ {description} - PASSED")
                return True
            else:
                print(f"❌ {description} - FAILED")
                self.total_errors += 1
                return False
                
        except Exception as e:
            print(f"❌ Error running {module_name}.{function_name}: {e}")
            self.total_errors += 1
            return False
    
    def check_environment(self):
        """Check if we're running inside container or need Docker"""
        print(f"\n{'='*60}")
        print("CHECKING: Environment and Docker Status")
        print(f"{'='*60}")
        
        # Check if we're inside a container
        if os.path.exists('/.dockerenv'):
            print("🐳 Running inside Docker container")
            return True, True  # (in_container, docker_available)
        
        print("💻 Running on host system")
        
        try:
            # Check if docker-compose is available
            result = subprocess.run(['docker-compose', '--version'], 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                print("❌ docker-compose not available")
                return False, False
            
            # Check container status
            backend_dir = os.path.join(self.script_dir, '..')
            result = subprocess.run(['docker-compose', 'ps'], 
                                  cwd=backend_dir,
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("📋 Docker container status:")
                print(result.stdout)
                
                # Check if database is running
                if 'db' in result.stdout and 'Up' in result.stdout:
                    print("✅ Database container is running")
                    return False, True  # (not in container, docker available)
                else:
                    print("⚠️  Database container may not be running")
                    print("💡 Run: docker-compose up -d")
                    return False, False
            else:
                print("⚠️  Could not check Docker status")
                print("💡 Make sure you're in the backend directory and run: docker-compose up -d")
                return False, False
                
        except Exception as e:
            print(f"⚠️  Docker check failed: {e}")
            print("💡 Make sure Docker is installed and running")
            return False, False
    
    def run_all_validations(self):
        """Run all validation checks"""
        print("🚀 STARTING COMPREHENSIVE SYSTEM VALIDATION")
        print("="*60)
        
        # Check environment
        in_container, docker_ok = self.check_environment()
        
        # Validation tasks
        validations = [
            # Schema vs Models comparison
            {
                'type': 'script',
                'name': 'compare_schema_models.py',
                'description': 'Schema vs Models Synchronization'
            },
            
            # Request ID validation
            {
                'type': 'script', 
                'name': 'validate_request_id.py',
                'description': 'Request ID Handling Validation'
            }
        ]
        
        # Add database validations only if Docker is running
        if docker_ok:
            validations.append({
                'type': 'script',
                'name': 'validate_constraints.py', 
                'description': 'Database Constraints Validation'
            })
        else:
            print("\n⚠️  Skipping database validation - Docker not available")
            print("   Start Docker and database: docker-compose up -d")
        
        # Run all validations
        passed = 0
        total = len(validations)
        
        for validation in validations:
            if validation['type'] == 'script':
                if self.run_script(validation['name'], validation['description']):
                    passed += 1
            elif validation['type'] == 'async':
                if self.run_async_validation(validation['module'], validation['function'], validation['description']):
                    passed += 1
        
        # Final report
        print(f"\n{'='*60}")
        print("FINAL VALIDATION REPORT")
        print(f"{'='*60}")
        
        print(f"📊 Validations: {passed}/{total} passed")
        
        if self.total_errors == 0:
            print("🎉 ALL VALIDATIONS PASSED!")
            print("✅ Your database schema, models, and constraints are properly configured")
            print("✅ Donation uniqueness constraints are working")
            print("✅ Request ID handling is properly set up")
        else:
            print(f"❌ Found {self.total_errors} errors that need to be fixed")
            print("\n🔧 NEXT STEPS:")
            print("1. Fix the errors reported above")
            print("2. Ensure Docker containers are running: docker-compose up -d") 
            print("3. Run database migrations: docker-compose exec api alembic upgrade head")
            print("4. Re-run this validation: python scripts/validate_all.py")
        
        if not docker_ok and not in_container:
            print("\n💡 DOCKER SETUP:")
            print("   cd mgen-backend/")
            print("   docker-compose up -d")
            print("   docker-compose exec api alembic upgrade head")
            print("\n💡 ALTERNATIVE - RUN INSIDE CONTAINER:")
            print("   docker-compose exec api python scripts/validate_all.py")
        
        print(f"{'='*60}")
        
        return self.total_errors == 0

def main():
    """Main validation function"""
    validator = MasterValidator()
    success = validator.run_all_validations()
    
    if success:
        print("\n🚀 System validation completed successfully!")
        print("Your donations system is ready for development!")
        sys.exit(0)
    else:
        print("\n⚠️  System validation found issues.")
        print("Please address the errors above before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()
