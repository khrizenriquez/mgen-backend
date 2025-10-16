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
        # Get configurable organization data from environment variables
        default_org_name = os.getenv("DEFAULT_ORGANIZATION_NAME", "Más Generosidad Guatemala")
        default_org_description = os.getenv("DEFAULT_ORGANIZATION_DESCRIPTION", "Organización principal de donaciones en Guatemala")
        default_org_email = os.getenv("DEFAULT_ORGANIZATION_EMAIL", "contacto@masgenerosidad.org")

        org = OrganizationModel(
            id="550e8400-e29b-41d4-a716-446655440000",
            name=default_org_name,
            description=default_org_description,
            contact_email=default_org_email,
            is_active=True
        )
        db.add(org)
        db.commit()
        logger.info(f"Created default organization: {default_org_name}")


def seed_default_users(db: Session) -> None:
    """Seed default test users"""
    # Ensure roles exist first
    seed_roles(db)
    seed_organization(db)

    # Get roles
    admin_role = db.query(RoleModel).filter(RoleModel.name == "ADMIN").first()
    donor_role = db.query(RoleModel).filter(RoleModel.name == "DONOR").first()
    user_role = db.query(RoleModel).filter(RoleModel.name == "USER").first()

    if not all([admin_role, donor_role, user_role]):
        logger.error("Required roles not found, skipping user seeding")
        return

    # Get default password from environment and ensure it's within bcrypt limits (72 bytes)
    default_password = os.getenv("DEFAULT_USER_PASSWORD", "seminario123")
    # Truncate password to 72 bytes if necessary (bcrypt limit)
    if len(default_password.encode('utf-8')) > 72:
        logger.warning(f"Password is longer than 72 bytes, truncating")
        default_password = default_password[:72]
    
    try:
        hashed_password = get_password_hash(default_password)
    except Exception as e:
        logger.error(f"Failed to hash password: {e}")
        return

    # Default users data (configurable via environment variables)
    default_admin_email = os.getenv("DEFAULT_ADMIN_EMAIL", "adminseminario@test.com")
    default_donor_email = os.getenv("DEFAULT_DONOR_EMAIL", "donorseminario@test.com")
    default_user_email = os.getenv("DEFAULT_USER_EMAIL", "userseminario@test.com")

    default_users = [
        {
            "email": default_admin_email,
            "password_hash": hashed_password,
            "role": admin_role,
            "email_verified": True,
            "is_active": True
        },
        {
            "email": default_donor_email,
            "password_hash": hashed_password,
            "role": donor_role,
            "email_verified": True,
            "is_active": True
        },
        {
            "email": default_user_email,
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