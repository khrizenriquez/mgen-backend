#!/usr/bin/env python3
"""
Script to initialize roles in the database
"""
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.orm import sessionmaker
from app.infrastructure.database.database import engine
from app.infrastructure.database.models import RoleModel

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_roles():
    """Initialize default roles"""
    db = SessionLocal()

    try:
        # Check existing roles
        existing_roles = db.query(RoleModel).all()
        existing_role_names = [role.name for role in existing_roles]

        print(f"📋 Found {len(existing_roles)} existing roles: {existing_role_names}")

        # Default roles to create
        default_roles = [
            ("ADMIN", "System administrator with full access to all organizations and data"),
            ("ORGANIZATION", "Organization administrator with access to their own organization data"),
            ("AUDITOR", "Read-only access for compliance and auditing purposes"),
            ("DONOR", "Registered donor with access to their own donations and profile"),
            ("USER", "Regular user with basic access")
        ]

        created_count = 0
        for role_name, description in default_roles:
            if role_name not in existing_role_names:
                role = RoleModel(name=role_name, description=description)
                db.add(role)
                print(f"✅ Created role: {role_name}")
                created_count += 1
            else:
                print(f"⚠️  Role {role_name} already exists")

        db.commit()

        if created_count > 0:
            print(f"\n🎉 Successfully created {created_count} new roles!")
        else:
            print("\nℹ️  All roles already exist")

    except Exception as e:
        db.rollback()
        print(f"❌ Error initializing roles: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 Initializing roles...")
    init_roles()