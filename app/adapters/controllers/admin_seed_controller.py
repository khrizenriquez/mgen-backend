"""
Temporary admin controller for seeding production database
WARNING: This should be removed after initial setup or secured properly
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.infrastructure.database.database import get_db
from app.infrastructure.database.seeders import run_seeders
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/admin/seed",
    tags=["admin"],
)


@router.post("/run")
async def run_database_seeders(db: Session = Depends(get_db)):
    """
    Run database seeders to initialize roles and default data
    
    WARNING: This endpoint should be called once and then removed or secured
    """
    try:
        logger.info("Running database seeders via admin endpoint...")
        run_seeders(db)
        logger.info("Seeders completed successfully")
        
        return {
            "message": "Database seeders executed successfully",
            "success": True,
            "note": "Roles, organizations, and default users have been created"
        }
    except Exception as e:
        logger.error(f"Failed to run seeders: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run seeders: {str(e)}"
        )

