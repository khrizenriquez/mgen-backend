"""
Test de ejemplo para validar la configuración de pytest.
Test del endpoint de health check.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.unit
@pytest.mark.api
async def test_health_endpoint(async_client: AsyncClient):
    """Test del endpoint de health check."""
    response = await async_client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


@pytest.mark.unit
def test_sample_fixture(sample_donation_data):
    """Test para validar que las fixtures funcionan."""
    assert "amount_gtq" in sample_donation_data
    assert sample_donation_data["amount_gtq"] == 100.00
    assert "donor_email" in sample_donation_data
    assert sample_donation_data["donor_email"] == "test@example.com"


@pytest.mark.unit
def test_sample_user_fixture(sample_user_data):
    """Test para validar fixture de usuario."""
    assert "email" in sample_user_data
    assert "password" in sample_user_data
    assert sample_user_data["email"] == "testuser@example.com"
    assert sample_user_data["is_active"] is True

