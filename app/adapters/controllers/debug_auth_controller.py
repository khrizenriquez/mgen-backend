"""
Temporary debug controller for auth issues
WARNING: Remove this in production!
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.infrastructure.database.database import get_db
from app.infrastructure.database.models import UserModel, RoleModel
from app.infrastructure.auth.jwt_utils import verify_password, get_password_hash
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/debug/auth",
    tags=["debug"],
)


@router.get("/test-user/{email}")
async def test_user_exists(email: str, db: Session = Depends(get_db)):
    """Check if user exists and show details"""
    user = db.query(UserModel).filter(UserModel.email == email).first()
    
    if not user:
        return {"exists": False, "email": email}
    
    user_roles = [ur.role.name for ur in user.user_roles]
    
    return {
        "exists": True,
        "email": user.email,
        "email_verified": user.email_verified,
        "is_active": user.is_active,
        "roles": user_roles,
        "password_hash_preview": user.password_hash[:30] if user.password_hash else None,
        "organization_id": str(user.organization_id) if user.organization_id else None
    }


@router.post("/test-password")
async def test_password_verification(
    email: str,
    password: str,
    db: Session = Depends(get_db)
):
    """Test password verification"""
    try:
        user = db.query(UserModel).filter(UserModel.email == email).first()
        
        if not user:
            return {"error": "User not found"}
        
        # Try to verify password
        try:
            result = verify_password(password, user.password_hash)
            return {
                "email": email,
                "password_length": len(password),
                "hash_preview": user.password_hash[:30],
                "verification_result": result,
                "verification_error": None
            }
        except Exception as e:
            return {
                "email": email,
                "password_length": len(password),
                "hash_preview": user.password_hash[:30],
                "verification_result": False,
                "verification_error": str(e)
            }
    except Exception as e:
        logger.error(f"Test password error: {e}", exc_info=True)
        return {"error": str(e)}


@router.post("/generate-hash")
async def generate_hash(password: str):
    """Generate password hash for testing"""
    try:
        hashed = get_password_hash(password)
        return {
            "password": password,
            "hash": hashed,
            "hash_length": len(hashed)
        }
    except Exception as e:
        logger.error(f"Hash generation error: {e}", exc_info=True)
        return {"error": str(e)}


@router.get("/list-roles")
async def list_roles(db: Session = Depends(get_db)):
    """List all roles"""
    roles = db.query(RoleModel).all()
    return {
        "count": len(roles),
        "roles": [{"id": r.id, "name": r.name, "description": r.description} for r in roles]
    }

