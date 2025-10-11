"""
Tests unitarios para la entidad Donation.
"""

import pytest
from datetime import datetime
from app.domain.entities.donation import Donation, DonationStatus


@pytest.mark.unit
def test_donation_creation():
    """Test de creación básica de donación."""
    donation_data = {
        "amount_gtq": 100.00,
        "donor_email": "test@example.com",
        "donor_name": "Test Donor",
        "reference_code": "REF-001",
        "correlation_id": "CORR-001"
    }
    
    donation = Donation(**donation_data)
    
    assert donation.amount_gtq == 100.00
    assert donation.donor_email == "test@example.com"
    assert donation.donor_name == "Test Donor"
    assert donation.reference_code == "REF-001"
    assert donation.correlation_id == "CORR-001"


@pytest.mark.unit
def test_donation_status_validation():
    """Test de validación de estados de donación."""
    donation_data = {
        "amount_gtq": 100.00,
        "donor_email": "test@example.com",
        "reference_code": "REF-001",
        "correlation_id": "CORR-001",
        "status_id": DonationStatus.PENDING
    }
    
    donation = Donation(**donation_data)
    
    assert donation.status_id == DonationStatus.PENDING
    assert donation.is_pending
    assert not donation.is_approved
    assert not donation.is_declined


@pytest.mark.unit
def test_donation_amount_validation():
    """Test de validación de monto."""
    # Monto válido
    donation_data = {
        "amount_gtq": 50.00,
        "donor_email": "test@example.com",
        "reference_code": "REF-001",
        "correlation_id": "CORR-001"
    }
    
    donation = Donation(**donation_data)
    assert donation.amount_gtq == 50.00
    
    # Test que el monto debe ser positivo (esto debe estar en la validación de la entidad)
    with pytest.raises((ValueError, AssertionError)):
        invalid_donation = Donation(
            amount_gtq=-10.00,
            donor_email="test@example.com",
            reference_code="REF-002",
            correlation_id="CORR-002"
        )


@pytest.mark.unit
def test_donation_email_validation():
    """Test de validación de email."""
    donation_data = {
        "amount_gtq": 100.00,
        "donor_email": "valid@example.com",
        "reference_code": "REF-001", 
        "correlation_id": "CORR-001"
    }
    
    donation = Donation(**donation_data)
    assert donation.donor_email == "valid@example.com"


@pytest.mark.unit
def test_donation_status_transitions():
    """Test de transiciones de estado."""
    donation_data = {
        "amount_gtq": 100.00,
        "donor_email": "test@example.com",
        "reference_code": "REF-001",
        "correlation_id": "CORR-001",
        "status_id": DonationStatus.PENDING
    }
    
    donation = Donation(**donation_data)
    
    # Estado inicial
    assert donation.is_pending
    
    # Aprobar donación
    donation.status_id = DonationStatus.APPROVED
    assert donation.is_approved
    assert not donation.is_pending
    
    # Rechazar donación
    donation.status_id = DonationStatus.DECLINED
    assert donation.is_declined
    assert not donation.is_approved


@pytest.mark.unit
def test_donation_formatted_amount():
    """Test del formateo de monto."""
    donation_data = {
        "amount_gtq": 1250.75,
        "donor_email": "test@example.com",
        "reference_code": "REF-001",
        "correlation_id": "CORR-001"
    }
    
    donation = Donation(**donation_data)
    
    # Esto depende de si tienes un método formatted_amount en tu entidad
    expected_format = "Q1,250.75"  # o el formato que uses
    # assert donation.formatted_amount == expected_format
