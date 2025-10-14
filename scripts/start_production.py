#!/usr/bin/env python3
"""
Production startup script for Railway
Includes diagnostics and validation before starting the application
"""
import os
import sys
import subprocess
from pathlib import Path

def run_diagnostic():
    """Run environment diagnostic"""
    print("🔍 Running Railway Environment Diagnostic...")
    print("="*60)

    # Run the diagnostic script
    try:
        result = subprocess.run([
            sys.executable,
            str(Path(__file__).parent / "diagnose_env.py")
        ], capture_output=True, text=True)

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run diagnostic: {e}")
        return False

def run_validation():
    """Run configuration validation"""
    print("\n🔧 Running Configuration Validation...")
    print("="*60)

    try:
        result = subprocess.run([
            sys.executable,
            str(Path(__file__).parent / "validate_config.py")
        ], capture_output=True, text=True)

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run validation: {e}")
        return False

def start_application():
    """Start the FastAPI application"""
    print("\n🚀 Starting FastAPI Application...")
    print("="*60)

    # Use uvicorn to start the application
    # Railway injects PORT environment variable
    port = os.getenv("PORT", "8000")
    print(f"🚀 Starting on port: {port}")

    os.execvp("uvicorn", [
        "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", port,
        "--reload"
    ])

def main():
    """Main startup sequence"""
    print("🏭 Starting Donations API - Production Mode")
    print("="*80)

    # Check if we're running on Railway
    is_railway = bool(os.getenv('RAILWAY_PROJECT_ID'))

    if is_railway:
        print("🚂 Detected Railway environment")

        # Run diagnostics first
        if not run_diagnostic():
            print("❌ Diagnostic failed!")
            sys.exit(1)

        # Run validation
        if not run_validation():
            print("❌ Configuration validation failed!")
            print("💡 Check Railway environment variables and secrets")
            sys.exit(1)

        print("\n✅ All checks passed! Starting application...")
    else:
        print("💻 Running in local/development environment")
        print("ℹ️  Skipping Railway-specific diagnostics")

    # Start the application
    start_application()

if __name__ == "__main__":
    main()
