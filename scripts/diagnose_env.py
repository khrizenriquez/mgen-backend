#!/usr/bin/env python3
"""
Environment diagnostic script for Railway
Shows all environment variables to help debug configuration issues
"""
import os
import sys

def diagnose_environment():
    """Diagnose environment variables"""
    print("🔍 Environment Diagnostic Report")
    print("="*50)

    # Critical variables to check
    critical_vars = [
        'DATABASE_URL',
        'JWT_SECRET_KEY',
        'DEFAULT_USER_PASSWORD',
        'ENVIRONMENT',
        'DEBUG'
    ]

    print("\n🔐 Critical Variables:")
    for var in critical_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'password' in var.lower() or 'secret' in var.lower() or 'key' in var.lower():
                display_value = value[:10] + "..." if len(value) > 10 else value
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NOT SET")

    # Railway-specific variables
    railway_vars = [
        'RAILWAY_PROJECT_ID',
        'RAILWAY_ENVIRONMENT_ID',
        'RAILWAY_SERVICE_ID',
        'RAILWAY_STATIC_URL'
    ]

    print("\n🚂 Railway Variables:")
    for var in railway_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")

    # Database-related variables
    db_vars = [
        'PGHOST', 'PGPORT', 'PGUSER', 'PGPASSWORD', 'PGDATABASE',
        'POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_DB'
    ]

    print("\n🗄️  Database Variables:")
    for var in db_vars:
        value = os.getenv(var)
        if value:
            if 'password' in var.lower():
                display_value = value[:5] + "***"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: NOT SET")

    print("\n📋 All Environment Variables:")
    print("-"*30)
    for key, value in sorted(os.environ.items()):
        if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'key', 'token']):
            print(f"{key}=***masked***")
        else:
            print(f"{key}={value}")

if __name__ == "__main__":
    diagnose_environment()
