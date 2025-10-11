# Python & FastAPI Conventions

## Import Organization
```python
# Standard library imports
from datetime import datetime
from typing import List, Optional
from uuid import UUID

# Third-party imports
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

# Local imports
from app.domain.entities.donation import Donation, DonationStatus
from app.infrastructure.logging import get_logger
```

## FastAPI Controllers
- Use `APIRouter()` for organizing endpoints
- Include docstrings for all endpoints
- Use dependency injection with `Depends()`
- Always include structured logging
- Handle exceptions with try/catch and proper HTTP status codes

```python
router = APIRouter(prefix="/api/v1", tags=["donations"])
logger = get_logger(__name__)

@router.get("/donations", response_model=List[DonationResponse])
async def list_donations(
    limit: int = Query(100, ge=1, le=1000),
    repository: DonationRepository = Depends(get_repository)
):
    """List donations with optional filtering"""
    try:
        logger.info("Fetching donations list", limit=limit)
        donations = await repository.get_all(limit=limit)
        return [DonationResponse.from_entity(d) for d in donations]
    except Exception as e:
        logger.error("Error listing donations", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

## Error Handling
- Use structured logging for all errors
- Include `exc_info=True` for exception stack traces
- Never expose internal error details to clients in production
- Use appropriate HTTP status codes (400, 404, 500)

## Type Hints
- Always use type hints for function parameters and return values
- Use `Optional[T]` for nullable values
- Use `List[T]` for collections
- Use `UUID` for database IDs

```python
async def create_donation(
    donation_data: CreateDonationRequest,
    repository: DonationRepository
) -> Donation:
    """Create a new donation with proper type hints"""
    pass
```

## Async/Await
- All database operations must be async
- Repository methods return `async` functions
- Controllers use `async def` for endpoints
- Use `await` for all async calls

```python
# Correct async pattern
async def get_donation_by_id(
    donation_id: UUID,
    repository: DonationRepository = Depends(get_repository)
) -> DonationResponse:
    donation = await repository.get_by_id(donation_id)
    if not donation:
        raise HTTPException(status_code=404, detail="Donation not found")
    return DonationResponse.from_entity(donation)
```

## Environment Variables
- Use `os.getenv()` with defaults for configuration
- Never hardcode sensitive values
- Document required environment variables

```python
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/donations")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
```

## Validation
- Use Pydantic models for request/response validation
- Implement business validation in domain entities
- Use `__post_init__` for dataclass validation

```python
from pydantic import BaseModel, validator

class CreateDonationRequest(BaseModel):
    amount_gtq: Decimal
    donor_email: str
    
    @validator('amount_gtq')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v
```

## Database Models
- Use proper SQLAlchemy column types
- Match real database schema from `schema.sql`
- Use `server_default=func.now()` for timestamps
- Include proper foreign key relationships

```python
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID

class DonationModel(Base):
    __tablename__ = "donations"
    
    id = Column(PostgreSQL_UUID(as_uuid=True), primary_key=True)
    amount_gtq = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

## Exception Handling Pattern
```python
@router.post("/donations")
async def create_donation(request: CreateDonationRequest):
    try:
        # Business logic
        result = await service.create_donation(request)
        return DonationResponse.from_entity(result)
    except ValueError as e:
        logger.warning("Validation error", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

## Code Style
- Use descriptive variable names
- Keep functions focused and small
- Use list comprehensions where appropriate
- Follow PEP 8 naming conventions
- Use f-strings for string formatting
