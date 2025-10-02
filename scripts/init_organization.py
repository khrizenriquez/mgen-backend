#!/usr/bin/env python3
"""
Script to initialize organization structure
"""
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from app.infrastructure.database.database import engine

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_and_create_organization_table():
    """Check if organization table exists and create it if not"""
    db = SessionLocal()

    try:
        # Check if organization table exists
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.tables
                WHERE table_name = 'organization'
            )
        """)).scalar()

        if not result:
            print("🏗️  Creating organization table...")

            # Create organization table
            db.execute(text("""
                CREATE TABLE organization (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    contact_email TEXT,
                    contact_phone TEXT,
                    address TEXT,
                    website TEXT,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            """))

            print("✅ Organization table created")
        else:
            print("✅ Organization table already exists")

        # Check if organization_id column exists in app_user
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = 'app_user' AND column_name = 'organization_id'
            )
        """)).scalar()

        if not result:
            print("🔧 Adding organization_id column to app_user...")

            # Add organization_id column
            db.execute(text("""
                ALTER TABLE app_user ADD COLUMN organization_id UUID REFERENCES organization(id)
            """))

            print("✅ organization_id column added")
        else:
            print("✅ organization_id column already exists")

        # Check if default organization exists
        result = db.execute(text("""
            SELECT COUNT(*) FROM organization
            WHERE id = '550e8400-e29b-41d4-a716-446655440000'
        """)).scalar()

        if result == 0:
            print("🏢 Creating default organization...")

            # Create default organization
            db.execute(text("""
                INSERT INTO organization (id, name, description, contact_email, is_active)
                VALUES ('550e8400-e29b-41d4-a716-446655440000',
                        'Fundación Donaciones Guatemala',
                        'Organización principal de donaciones en Guatemala',
                        'contacto@donacionesgt.org',
                        TRUE)
                ON CONFLICT (id) DO NOTHING
            """))

            print("✅ Default organization created")
        else:
            print("✅ Default organization already exists")

        db.commit()

    except Exception as e:
        db.rollback()
        print(f"❌ Error initializing organization structure: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("🏢 Initializing organization structure...")
    check_and_create_organization_table()
    print("✅ Organization structure ready!")