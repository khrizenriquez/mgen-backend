#!/usr/bin/env python3
"""
Configuration validation script
Checks that all required environment variables are set before starting the application
"""
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

def validate_configuration():
    """Validate all required configuration"""
    errors = []
    warnings = []

    print("🔍 Validating application configuration...\n")

    # Critical security variables (required)
    critical_vars = {
        'JWT_SECRET_KEY': 'Required for JWT token signing',
        'DATABASE_URL': 'Required for database connection'
    }

    print("🔐 Checking CRITICAL security variables:")
    for var_name, description in critical_vars.items():
        value = os.getenv(var_name)
        if not value:
            errors.append(f"❌ {var_name}: {description} - NOT SET")
        else:
            print(f"✅ {var_name}: Configured")
            # Debug: Show first few chars of DATABASE_URL for verification
            if var_name == 'DATABASE_URL' and value:
                print(f"   📍 DATABASE_URL starts with: {value[:20]}...")

    # Recommended security variables
    recommended_vars = {
        'ENVIRONMENT': ('development', 'Should be "development" or "production"'),
        'RATE_LIMIT_REQUESTS': ('10', 'Rate limiting for auth endpoints'),
        'RATE_LIMIT_WINDOW': ('60', 'Rate limiting window in seconds')
    }

    print("\n⚠️  Checking RECOMMENDED security variables:")
    for var_name, (default, description) in recommended_vars.items():
        value = os.getenv(var_name, default)
        if not os.getenv(var_name):
            warnings.append(f"⚠️  {var_name}: Using default value '{default}' - {description}")
        else:
            print(f"✅ {var_name}: {value}")

    # Email configuration (Mailjet - required for production)
    email_vars = ['MAILJET_API_KEY', 'MAILJET_API_SECRET', 'FROM_EMAIL']
    email_configured = all(os.getenv(var) for var in email_vars)

    print("\n📧 Checking EMAIL configuration (Mailjet):")
    if email_configured:
        print("✅ Email service: Fully configured")
    else:
        missing = [var for var in email_vars if not os.getenv(var)]
        warnings.append(f"⚠️  Email service: Missing {', '.join(missing)} - Password reset will not work")

    # Environment-specific checks
    environment = os.getenv('ENVIRONMENT', 'development')
    if environment == 'production':
        print("\n🏭 PRODUCTION environment detected:")

        # Production-specific checks
        default_password = os.getenv('DEFAULT_USER_PASSWORD')
        if default_password:
            errors.append("❌ DEFAULT_USER_PASSWORD: Should not be set in production")
            print(f"   ⚠️  DEFAULT_USER_PASSWORD is currently set to: '{default_password[:10]}...'")

        if not email_configured:
            errors.append("❌ Email configuration: Required in production for password reset")

        # Check for debug mode
        if os.getenv('DEBUG', '').lower() == 'true':
            warnings.append("⚠️  DEBUG: Should be disabled in production")

    elif environment == 'development':
        print("\n🛠️  DEVELOPMENT environment detected:")

        if not os.getenv('DEFAULT_USER_PASSWORD'):
            warnings.append("⚠️  DEFAULT_USER_PASSWORD: Not set - using default 'seminario123'")

    # Summary
    print("\n" + "="*60)
    print("📊 CONFIGURATION VALIDATION SUMMARY")
    print("="*60)

    if errors:
        print(f"\n❌ CRITICAL ERRORS ({len(errors)}):")
        for error in errors:
            print(f"   {error}")
        print("\n🚫 Application CANNOT start with these errors!")
        return False

    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for warning in warnings:
            print(f"   {warning}")
        print("\n✅ Application can start but review warnings for production use")

    if not errors and not warnings:
        print("\n✅ All configuration validated successfully!")
        print("🚀 Application is ready to start")

    return len(errors) == 0

if __name__ == "__main__":
    success = validate_configuration()
    sys.exit(0 if success else 1)