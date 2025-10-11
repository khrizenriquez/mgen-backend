# Structured Logging Standards

## Required Logging Setup
- Always use structured logging with JSON format in production
- Use the centralized logging configuration from `app/infrastructure/logging`
- Import logger using: `from app.infrastructure.logging import get_logger`
- Initialize logger: `logger = get_logger(__name__)`

## Logging Format Requirements
- All logs must include these standard fields:
  - `timestamp`: ISO format timestamp
  - `level`: Log level (INFO, ERROR, WARNING, DEBUG)
  - `service`: Always "donations-api"
  - `env`: Environment (development, staging, production)
  - `version`: Application version
  - `request_id`: Correlation ID for request tracing
  - `method`, `path`, `status_code`, `latency_ms`: For HTTP requests

## Request Correlation
- Every HTTP request must have a unique `request_id` (UUID)
- Use the LoggingMiddleware from `app/infrastructure/logging/middleware.py`
- Add correlation IDs to response headers: `x-request-id`

## PII Masking
- Automatically mask sensitive data using PIIMasker from `app/infrastructure/logging/formatters.py`
- Never log passwords, tokens, or full credit card numbers
- Email masking: `user@example.com` → `us***@example.com`
- Phone masking: `555-123-4567` → `***-***-****`

## Error Logging
- Always log errors with context using structured format:
```python
logger.error(
    "Operation failed",
    error=str(e),
    error_type=type(e).__name__,
    user_id=user_id,
    operation="create_donation",
    exc_info=True
)
```

## Controller Logging Pattern
```python
@router.post("/donations")
async def create_donation(request: CreateDonationRequest):
    request_id = str(uuid4())
    logger.info(
        "Creating donation", 
        request_id=request_id,
        amount=request.amount_gtq,
        donor_email=request.donor_email  # Will be masked automatically
    )
    
    try:
        # Business logic
        result = await service.create_donation(request)
        logger.info("Donation created successfully", request_id=request_id, donation_id=str(result.id))
        return result
    except Exception as e:
        logger.error(
            "Failed to create donation",
            request_id=request_id,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal server error")
```

## Environment Variables
- Control logging via environment variables:
  - `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR
  - `SERVICE_NAME`: Service identifier
  - `ENVIRONMENT`: Environment name
  - `VERSION`: Application version

## Logging Middleware Setup
```python
from app.infrastructure.logging.middleware import LoggingMiddleware

app = FastAPI()
app.add_middleware(LoggingMiddleware)
```

## Log Output Format (JSON)
```json
{
  "timestamp": "2025-09-01T12:00:00Z",
  "level": "INFO",
  "service": "donations-api",
  "env": "development",
  "version": "1.0.0",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Creating donation",
  "amount": 100.00,
  "donor_email": "us***@example.com"
}
```
