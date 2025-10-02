"""
Database seeders for initial data
"""
import os
import logging
from sqlalchemy.orm import Session
from app.infrastructure.database.models import UserModel, RoleModel, OrganizationModel, UserRoleModel
from app.infrastructure.auth.jwt_utils import get_password_hash

logger = logging.getLogger(__name__)


def seed_roles(db: Session) -> None:
    """Seed default roles"""
    roles_data = [
        ("ADMIN", "System administrator with full access to all organizations and data"),
        ("ORGANIZATION", "Organization administrator with access to their own organization data"),
        ("AUDITOR", "Read-only access for compliance and auditing purposes"),
        ("DONOR", "Registered donor with access to their own donations and profile"),
        ("USER", "Regular user with basic access")
    ]

    for role_name, description in roles_data:
        role = db.query(RoleModel).filter(RoleModel.name == role_name).first()
        if not role:
            role = RoleModel(name=role_name, description=description)
            db.add(role)
            logger.info(f"Created role: {role_name}")

    db.commit()


def seed_organization(db: Session) -> None:
    """Seed default organization"""
    org = db.query(OrganizationModel).filter(
        OrganizationModel.id == "550e8400-e29b-41d4-a716-446655440000"
    ).first()

    if not org:
        org = OrganizationModel(
            id="550e8400-e29b-41d4-a716-446655440000",
            name="Fundación Donaciones Guatemala",
            description="Organización principal de donaciones en Guatemala",
            contact_email="contacto@donacionesgt.org",
            is_active=True
        )
        db.add(org)
        db.commit()
        logger.info("Created default organization: Fundación Donaciones Guatemala")


def seed_default_users(db: Session) -> None:
    """Seed default test users"""
    # Ensure roles exist first
    seed_roles(db)
    seed_organization(db)

    default_password = "seminario123"
    hashed_password = get_password_hash(default_password)

    # Get roles
    admin_role = db.query(RoleModel).filter(RoleModel.name == "ADMIN").first()
    donor_role = db.query(RoleModel).filter(RoleModel.name == "DONOR").first()
    user_role = db.query(RoleModel).filter(RoleModel.name == "USER").first()

    if not all([admin_role, donor_role, user_role]):
        logger.error("Required roles not found, skipping user seeding")
        return

    # Get default password from environment
    default_password = os.getenv("DEFAULT_USER_PASSWORD", "seminario123")
    hashed_password = get_password_hash(default_password)

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
            "role": user_role,  # This will be upgraded to DONOR later
            "email_verified": True,
            "is_active": True
        }
    ]

    for user_data in default_users:
        # Check if user already exists
        existing_user = db.query(UserModel).filter(
            UserModel.email == user_data["email"]
        ).first()

        if existing_user:
            logger.info(f"User {user_data['email']} already exists, skipping...")
            continue

        # Create user
        user = UserModel(
            email=user_data["email"],
            password_hash=user_data["password_hash"],
            email_verified=user_data["email_verified"],
            is_active=user_data["is_active"],
            organization_id="550e8400-e29b-41d4-a716-446655440000"  # Default organization
        )

        db.add(user)
        db.flush()  # Get user ID

        # Assign role
        user_role_association = UserRoleModel(
            user_id=user.id,
            role_id=user_data["role"].id
        )
        db.add(user_role_association)

        db.commit()
        logger.info(f"Created default user: {user_data['email']} with role {user_data['role'].name}")


def run_seeders(db: Session) -> None:
    """Run all database seeders"""
    try:
        logger.info("Starting database seeding...")

        seed_roles(db)
        seed_organization(db)
        seed_default_users(db)

        logger.info("Database seeding completed successfully!")

    except Exception as e:
        logger.error(f"Error during database seeding: {e}")
        db.rollback()
        raise