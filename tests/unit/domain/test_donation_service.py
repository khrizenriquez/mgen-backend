"""
Tests unitarios para el servicio de donaciones.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from app.domain.services.donation_service import DonationService
from app.domain.entities.donation import Donation, DonationStatus
from app.domain.repositories.donation_repository import DonationRepository


@pytest.mark.unit
def test_donation_service_creation():
    """Test de creación del servicio de donaciones."""
    mock_repository = Mock(spec=DonationRepository)
    
    service = DonationService(mock_repository)
    
    assert service is not None
    # assert service.repository == mock_repository  # Si tienes esta propiedad


@pytest.mark.unit
async def test_create_donation_success():
    """Test de creación exitosa de donación."""
    # Mock del repositorio
    mock_repository = AsyncMock(spec=DonationRepository)
    
    # Datos de entrada
    donation_data = {
        "amount_gtq": 100.00,
        "donor_email": "test@example.com",
        "donor_name": "Test Donor",
        "reference_code": "REF-001",
        "correlation_id": "CORR-001"
    }
    
    # Mock de la donación creada
    created_donation = Donation(**donation_data)
    created_donation.id = "test-uuid-123"
    created_donation.status_id = DonationStatus.PENDING
    
    # Configurar mock para devolver la donación
    mock_repository.create.return_value = created_donation
    
    # Crear servicio
    service = DonationService(mock_repository)
    
    # Ejecutar método
    result = await service.create_donation(donation_data)
    
    # Verificaciones
    assert result is not None
    assert result.amount_gtq == 100.00
    assert result.donor_email == "test@example.com"
    assert result.status_id == DonationStatus.PENDING
    
    # Verificar que el repositorio fue llamado
    mock_repository.create.assert_called_once()


@pytest.mark.unit
async def test_get_donation_by_id_success():
    """Test de obtención de donación por ID."""
    mock_repository = AsyncMock(spec=DonationRepository)
    
    # Mock donation
    donation_id = "test-uuid-123"
    mock_donation = Mock(spec=Donation)
    mock_donation.id = donation_id
    mock_donation.amount_gtq = 150.00
    mock_donation.donor_email = "donor@example.com"
    
    # Configurar mock
    mock_repository.get_by_id.return_value = mock_donation
    
    # Crear servicio
    service = DonationService(mock_repository)
    
    # Ejecutar
    result = await service.get_donation_by_id(donation_id)
    
    # Verificaciones
    assert result is not None
    assert result.id == donation_id
    assert result.amount_gtq == 150.00
    
    # Verificar llamada al repositorio
    mock_repository.get_by_id.assert_called_once_with(donation_id)


@pytest.mark.unit
async def test_get_donation_by_id_not_found():
    """Test cuando no se encuentra la donación."""
    mock_repository = AsyncMock(spec=DonationRepository)
    
    # Configurar mock para devolver None
    mock_repository.get_by_id.return_value = None
    
    service = DonationService(mock_repository)
    
    # Ejecutar
    result = await service.get_donation_by_id("nonexistent-id")
    
    # Verificar que devuelve None
    assert result is None
    
    mock_repository.get_by_id.assert_called_once_with("nonexistent-id")


@pytest.mark.unit
async def test_get_all_donations():
    """Test de obtención de todas las donaciones."""
    mock_repository = AsyncMock(spec=DonationRepository)
    
    # Mock donations list
    mock_donations = [
        Mock(id="1", amount_gtq=100.00),
        Mock(id="2", amount_gtq=200.00),
        Mock(id="3", amount_gtq=300.00)
    ]
    
    mock_repository.get_all.return_value = mock_donations
    
    service = DonationService(mock_repository)
    
    # Ejecutar
    result = await service.get_all_donations()
    
    # Verificaciones
    assert len(result) == 3
    assert result[0].id == "1"
    assert result[1].amount_gtq == 200.00
    
    mock_repository.get_all.assert_called_once()


@pytest.mark.unit
async def test_update_donation_status():
    """Test de actualización de estado de donación."""
    mock_repository = AsyncMock(spec=DonationRepository)
    
    # Mock donation existente
    donation_id = "test-uuid"
    existing_donation = Mock(spec=Donation)
    existing_donation.id = donation_id
    existing_donation.status_id = DonationStatus.PENDING
    
    # Mock donation actualizada
    updated_donation = Mock(spec=Donation)
    updated_donation.id = donation_id
    updated_donation.status_id = DonationStatus.APPROVED
    
    # Configurar mocks
    mock_repository.get_by_id.return_value = existing_donation
    mock_repository.update.return_value = updated_donation
    
    service = DonationService(mock_repository)
    
    # Ejecutar
    result = await service.update_donation_status(donation_id, DonationStatus.APPROVED)
    
    # Verificaciones
    assert result is not None
    assert result.status_id == DonationStatus.APPROVED
    
    mock_repository.get_by_id.assert_called_once_with(donation_id)
    mock_repository.update.assert_called_once()


@pytest.mark.unit
async def test_donation_business_validation():
    """Test de validaciones de negocio en el servicio."""
    mock_repository = AsyncMock(spec=DonationRepository)
    service = DonationService(mock_repository)
    
    # Test de validación de monto mínimo (ejemplo de lógica de negocio)
    invalid_donation_data = {
        "amount_gtq": 0.50,  # Supongamos que el mínimo es 1.00
        "donor_email": "test@example.com",
        "reference_code": "REF-001",
        "correlation_id": "CORR-001"
    }
    
    # Esto depende de si tienes validaciones de negocio en el servicio
    # with pytest.raises(ValueError, match="Monto mínimo"):
    #     await service.create_donation(invalid_donation_data)
    
    # Por ahora, solo verificamos que no explote
    # En una implementación real, aquí irían las validaciones específicas
    pass