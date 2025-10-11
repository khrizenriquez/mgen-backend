# Hexagonal Architecture Guidelines

## Project Structure
The donation management system follows hexagonal (ports and adapters) architecture:

```
app/
├── domain/              # Core business logic (inner layer)
│   ├── entities/       # Business entities (Donation)
│   ├── repositories/   # Repository interfaces (ports)
│   └── services/       # Domain services
├── adapters/           # External interfaces (outer layer)
│   ├── controllers/    # HTTP API controllers
│   └── schemas/        # Request/response schemas
└── infrastructure/     # Technical implementations (outer layer)
    ├── database/       # Database implementations
    ├── logging/        # Logging infrastructure
    └── external/       # External service adapters
```

## Dependency Rules
- **Domain layer** has NO dependencies on outer layers
- **Adapters** depend on domain interfaces
- **Infrastructure** implements domain interfaces
- Use dependency injection for all external dependencies

## Entity Guidelines
- Domain entities in `app/domain/entities` contain business logic only
- Use dataclasses for entities with `__post_init__` validation
- Business rules and validation belong in entity methods
- Example: `app/domain/entities/donation.py`

## Repository Pattern
- Define interfaces in `app/domain/repositories`
- Implement in `app/infrastructure/database`
- Use async methods for all database operations
- Repository methods should return domain entities, not database models

## Controller Guidelines
- Controllers in `app/adapters/controllers` handle HTTP concerns only
- Use dependency injection: `repository = Depends(get_repository)`
- Always include structured logging with request context
- Return appropriate HTTP status codes and error responses
- Handle exceptions gracefully with try/catch blocks

## Database Models
- SQLAlchemy models in `app/infrastructure/database/models.py`
- Models must match the real database schema from `schema.sql`
- Use proper column types (UUID, TIMESTAMPTZ, etc.)
- Include foreign key relationships and constraints

## Service Layer
- Domain services coordinate complex business operations
- Keep services focused on single responsibilities
- Services should not know about HTTP or database details
- Use repository interfaces, not implementations

## Dependency Injection Pattern
```python
from fastapi import Depends

async def get_donation_repository() -> DonationRepository:
    return DonationRepositoryImpl()

@router.post("/donations")
async def create_donation(
    request: CreateDonationRequest,
    repository: DonationRepository = Depends(get_donation_repository)
):
    # Use repository interface, not implementation
```

## Domain Entity Example
```python
from dataclasses import dataclass
from uuid import UUID
from enum import Enum

@dataclass
class Donation:
    id: UUID
    amount_gtq: Decimal
    status: DonationStatus
    
    def __post_init__(self):
        if self.amount_gtq <= 0:
            raise ValueError("Amount must be positive")
    
    def approve(self):
        if self.status != DonationStatus.PENDING:
            raise ValueError("Only pending donations can be approved")
        self.status = DonationStatus.APPROVED
```
