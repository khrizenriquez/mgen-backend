"""
Unit tests for donation service
"""
import pytest
from unittest.mock import Mock, AsyncMock
from decimal import Decimal
from datetime import datetime

from app.domain.services.donation_service import DonationService
from app.domain.entities.donation import DonationStatus, DonationType


@pytest.fixture
def mock_repository():
    """Mock donation repository"""
    repo = Mock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.update = AsyncMock()
    repo.get_total_amount_by_status = AsyncMock()
    repo.count_by_status = AsyncMock()
    repo.get_by_email = AsyncMock()
    return repo


@pytest.fixture
def sample_donation():
    """Sample donation entity"""
    donation = Mock()
    donation.id = 1
    donation.donor_name = "John Doe"
    donation.donor_email = "john@example.com"
    donation.amount_gtq = Decimal("100.00")
    donation.status_id = 1  # PENDING
    donation.description = "Test donation"
    donation.created_at = datetime.utcnow()
    donation.updated_at = datetime.utcnow()
    donation.paid_at = None
    donation.is_pending = True
    donation.approve = Mock()
    donation.decline = Mock()
    donation.cancel = Mock()
    return donation


@pytest.fixture
def donation_service(mock_repository):
    """Donation service instance"""
    return DonationService(mock_repository)


class TestDonationService:
    """Test donation service business logic"""

    @pytest.mark.asyncio
    async def test_create_donation_success(self, donation_service, mock_repository, sample_donation):
        """Test successful donation creation"""
        mock_repository.create.return_value = sample_donation

        result = await donation_service.create_donation(
            donor_name="John Doe",
            donor_email="john@example.com",
            amount=Decimal("100.00"),
            currency="USD",
            donation_type=DonationType.ONE_TIME
        )

        assert result == sample_donation
        mock_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_donation_minimum_amount(self, donation_service, mock_repository):
        """Test minimum donation amount validation"""
        with pytest.raises(ValueError, match="Minimum donation amount"):
            await donation_service.create_donation(
                donor_name="John Doe",
                donor_email="john@example.com",
                amount=Decimal("0.50"),
                currency="USD",
                donation_type=DonationType.ONE_TIME
            )

    @pytest.mark.asyncio
    async def test_create_donation_maximum_amount(self, donation_service, mock_repository):
        """Test maximum donation amount validation"""
        with pytest.raises(ValueError, match="Maximum donation amount"):
            await donation_service.create_donation(
                donor_name="John Doe",
                donor_email="john@example.com",
                amount=Decimal("15000.00"),
                currency="USD",
                donation_type=DonationType.ONE_TIME
            )

    @pytest.mark.asyncio
    async def test_process_donation_success(self, donation_service, mock_repository, sample_donation):
        """Test successful donation processing"""
        mock_repository.get_by_id.return_value = sample_donation
        mock_repository.update.return_value = sample_donation

        result = await donation_service.process_donation(1)

        assert result == sample_donation
        sample_donation.approve.assert_called_once()
        mock_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_donation_not_found(self, donation_service, mock_repository):
        """Test processing non-existent donation"""
        mock_repository.get_by_id.return_value = None

        with pytest.raises(ValueError, match="not found"):
            await donation_service.process_donation(1)

    @pytest.mark.asyncio
    async def test_process_donation_not_pending(self, donation_service, mock_repository, sample_donation):
        """Test processing donation that is not pending"""
        sample_donation.is_pending = False
        mock_repository.get_by_id.return_value = sample_donation

        with pytest.raises(ValueError, match="not in pending status"):
            await donation_service.process_donation(1)

    @pytest.mark.asyncio
    async def test_cancel_donation_success(self, donation_service, mock_repository, sample_donation):
        """Test successful donation cancellation"""
        mock_repository.get_by_id.return_value = sample_donation
        mock_repository.update.return_value = sample_donation

        result = await donation_service.cancel_donation(1)

        assert result == sample_donation
        sample_donation.cancel.assert_called_once()
        mock_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_donation_statistics(self, donation_service, mock_repository):
        """Test getting donation statistics"""
        mock_repository.get_total_amount_by_status.side_effect = [Decimal("1000.00"), Decimal("500.00")]
        mock_repository.count_by_status.side_effect = [10, 5, 2]

        result = await donation_service.get_donation_statistics()

        assert result["total_amount_approved"] == 1000.0
        assert result["total_amount_pending"] == 500.0
        assert result["count_approved"] == 10
        assert result["count_pending"] == 5
        assert result["count_failed"] == 2
        assert "success_rate" in result

    @pytest.mark.asyncio
    async def test_get_donor_donations(self, donation_service, mock_repository, sample_donation):
        """Test getting donor donations"""
        mock_repository.get_by_email.return_value = [sample_donation]

        result = await donation_service.get_donor_donations("john@example.com")

        assert result == [sample_donation]
        mock_repository.get_by_email.assert_called_once_with("john@example.com")
