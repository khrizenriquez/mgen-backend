#!/usr/bin/env python3
"""
Script to create default users for testing
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
from app.infrastructure.database.models import UserModel, RoleModel, UserRoleModel
from app.infrastructure.auth.jwt_utils import get_password_hash

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_default_users():
    """Create default test users"""
    db = SessionLocal()

    try:
        # Default password for all users
        default_password = "seminario123"
        hashed_password = get_password_hash(default_password)

        # Get roles
        admin_role = db.query(RoleModel).filter(RoleModel.name == "ADMIN").first()
        donor_role = db.query(RoleModel).filter(RoleModel.name == "DONOR").first()
        user_role = db.query(RoleModel).filter(RoleModel.name == "USER").first()

        if not admin_role or not donor_role or not user_role:
            print("❌ Error: Required roles not found in database")
            print("Please run database migrations first")
            return

        # Default users data
        default_users = [
            {
                "email": "adminseminario@test.com",
                "password_hash": hashed_password,
                "role": admin_role,
                "email_verified": True,
                "is_active": True
            },
            {
                "email": "donorseminario@test.com",
                "password_hash": hashed_password,
                "role": donor_role,
                "email_verified": True,
                "is_active": True
            },
            {
                "email": "userseminario@test.com",
                "password_hash": hashed_password,
                "role": user_role,
                "email_verified": True,
                "is_active": True
            }
        ]

        created_users = []
        for user_data in default_users:
            # Check if user already exists
            existing_user = db.query(UserModel).filter(
                UserModel.email == user_data["email"]
            ).first()

            if existing_user:
                print(f"⚠️  User {user_data['email']} already exists, skipping...")
                continue

            # Create user
            user = UserModel(
                email=user_data["email"],
                password_hash=user_data["password_hash"],
                email_verified=user_data["email_verified"],
                is_active=user_data["is_active"],
                organization_id=None  # No organization assigned yet
            )

            db.add(user)
            db.flush()  # Get user ID

            # Assign role
            user_role_association = UserRoleModel(
                user_id=user.id,
                role_id=user_data["role"].id
            )
            db.add(user_role_association)

            created_users.append(user_data["email"])
            print(f"✅ Created user: {user_data['email']} with role {user_data['role'].name}")

        db.commit()

        if created_users:
            print(f"\n🎉 Successfully created {len(created_users)} default users!")
            print(f"📧 All users have password: {default_password}")
            print("\n📋 User Credentials:")
            for email in created_users:
                role_name = email.split('@')[0].replace('seminario', '').upper()
                print(f"   {email} | {default_password} | {role_name}")
        else:
            print("\nℹ️  All default users already exist")

    except Exception as e:
        db.rollback()
        print(f"❌ Error creating default users: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def list_existing_users():
    """List all existing users in the database"""
    db = SessionLocal()

    try:
        users = db.query(UserModel).all()

        if not users:
            print("📭 No users found in database")
            return

        print(f"👥 Found {len(users)} users in database:")
        print("-" * 80)
        print("<10")
        print("-" * 80)

        for user in users:
            roles = [ur.role.name for ur in user.user_roles]
            org_name = user.organization.name if user.organization else "No Organization"
            print("<10")

    except Exception as e:
        print(f"❌ Error listing users: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🔍 Checking existing users...")
    list_existing_users()

    print("\n🛠️  Creating default users...")
    create_default_users()

    print("\n🔍 Final user list:")
    list_existing_users()