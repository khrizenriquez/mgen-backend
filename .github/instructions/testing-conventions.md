# Testing Conventions

## Test Organization
Follow the test structure in `tests/`:
```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── domain/             # Domain entity tests
│   ├── adapters/           # Controller tests
│   └── infrastructure/     # Infrastructure tests
├── integration/            # Integration tests (with database)
│   ├── adapters/           # API endpoint tests
│   └── infrastructure/     # Database integration tests
└── conftest.py             # Shared test configuration
```

## Test Configuration
- Use pytest configuration from `pytest.ini`
- Shared fixtures in `conftest.py`
- Run tests in Docker: `docker-compose exec api pytest`

## Unit Testing Guidelines
- Test domain entities for business logic validation
- Mock external dependencies (database, APIs)
- Test logging formatters and PII masking
- Use descriptive test names

```python
class TestDonationEntity:
    """Test cases for Donation entity business logic"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.donation_data = {
            "id": uuid4(),
            "amount_gtq": Decimal("100.00"),
            "status": DonationStatus.PENDING
        }
    
    def test_donation_creation_success(self):
        """Test successful donation creation with valid data"""
        # Arrange
        donation = Donation(**self.donation_data)
        
        # Act & Assert
        assert donation.amount_gtq == Decimal("100.00")
        assert donation.status == DonationStatus.PENDING
    
    def test_donation_validation_negative_amount(self):
        """Test validation failure with negative amount"""
        # Arrange
        self.donation_data["amount_gtq"] = Decimal("-10.00")
        
        # Act & Assert
        with pytest.raises(ValueError, match="Amount must be positive"):
            Donation(**self.donation_data)
```

## Integration Testing
- Test API endpoints with real database
- Use TestClient for FastAPI testing
- Verify logging middleware and correlation IDs

```python
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def app_with_logging():
    """Create FastAPI app with logging middleware for testing"""
    setup_logging()
    app = FastAPI()
    app.add_middleware(LoggingMiddleware)
    return app

@pytest.fixture  
def client(app_with_logging):
    """Create test client"""
    return TestClient(app_with_logging)

def test_create_donation_success(client):
    """Test donation creation endpoint"""
    # Arrange
    donation_data = {
        "amount_gtq": 100.00,
        "donor_email": "test@example.com"
    }
    
    # Act
    response = client.post("/api/v1/donations", json=donation_data)
    
    # Assert
    assert response.status_code == 201
    assert "id" in response.json()
    assert response.headers["x-request-id"]  # Verify correlation ID
```

## Mocking Guidelines
- Mock external dependencies at the boundary
- Use `unittest.mock.Mock` and `patch` decorators
- Mock logging calls to verify structured logging
- Mock database calls in unit tests

```python
from unittest.mock import Mock, patch

@patch('app.infrastructure.logging.get_logger')
def test_controller_logging(mock_get_logger):
    """Test that controller logs properly"""
    # Arrange
    mock_logger = Mock()
    mock_get_logger.return_value = mock_logger
    
    # Act
    controller.create_donation(donation_request)
    
    # Assert
    mock_logger.info.assert_called_with(
        "Creating donation",
        amount=100.00,
        donor_email="us***@example.com"
    )
```

## Assertion Patterns
- Use descriptive assertion messages
- Verify exception types and messages
- Check log output format and fields
- Validate HTTP status codes and response structure

```python
def test_donation_approval_invalid_status(self):
    """Test that approval fails for non-pending donations"""
    # Arrange
    donation = Donation(
        id=uuid4(),
        amount_gtq=Decimal("100.00"),
        status=DonationStatus.APPROVED
    )
    
    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        donation.approve()
    
    assert "Only pending donations can be approved" in str(exc_info.value)
```

## Test Data
- Use realistic but non-sensitive test data
- Create reusable fixtures for common entities
- Use UUID4 for test IDs
- Follow real schema constraints

```python
@pytest.fixture
def sample_donation():
    """Provide a sample donation for testing"""
    return Donation(
        id=uuid4(),
        amount_gtq=Decimal("150.00"),
        status=DonationStatus.PENDING,
        donor_email="donor@example.com",
        created_at=datetime.now()
    )
```

## Testing Async Code
```python
import pytest

@pytest.mark.asyncio
async def test_repository_create_donation():
    """Test async repository method"""
    # Arrange
    repository = DonationRepositoryImpl()
    donation_data = CreateDonationRequest(
        amount_gtq=Decimal("100.00"),
        donor_email="test@example.com"
    )
    
    # Act
    result = await repository.create(donation_data)
    
    # Assert
    assert result.id is not None
    assert result.amount_gtq == Decimal("100.00")
```

## Running Tests
- Unit tests: `pytest tests/unit/ -v`
- Integration tests: `pytest tests/integration/ -v`
- All tests: `pytest -v`
- With coverage: `pytest --cov=app --cov-report=html`
- Specific test: `pytest tests/unit/domain/test_donation.py::TestDonationEntity::test_validation_success -v`

## Test Coverage
- Aim for high coverage of business logic
- Focus on critical paths and error conditions
- Include edge cases and validation scenarios
- Test logging output and correlation IDs

## Parameterized Testing
```python
@pytest.mark.parametrize("amount,expected_valid", [
    (Decimal("100.00"), True),
    (Decimal("0.01"), True),
    (Decimal("0.00"), False),
    (Decimal("-10.00"), False),
])
def test_donation_amount_validation(amount, expected_valid):
    """Test donation amount validation with various inputs"""
    if expected_valid:
        donation = Donation(id=uuid4(), amount_gtq=amount, status=DonationStatus.PENDING)
        assert donation.amount_gtq == amount
    else:
        with pytest.raises(ValueError):
            Donation(id=uuid4(), amount_gtq=amount, status=DonationStatus.PENDING)
```
