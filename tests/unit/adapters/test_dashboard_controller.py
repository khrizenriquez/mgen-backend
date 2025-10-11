"""
Unit tests for dashboard controller
"""
import pytest
from unittest.mock import Mock
from decimal import Decimal
from datetime import datetime, timedelta


@pytest.fixture
def mock_dashboard_service():
    """Mock dashboard service"""
    return Mock()


@pytest.fixture
def mock_current_user():
    """Mock current user"""
    user = Mock()
    user.id = "user-123"
    user.organization_id = "org-123"
    user.roles = ["admin"]
    return user


class TestDashboardController:
    """Test dashboard controller endpoints"""

    def test_get_dashboard_overview(self, mock_dashboard_service, mock_current_user):
        """Test getting dashboard overview"""
        mock_overview = {
            "total_donations": 100,
            "total_amount": Decimal("10000.00"),
            "active_campaigns": 5,
            "total_donors": 75
        }
        
        mock_dashboard_service.get_overview.return_value = mock_overview
        
        assert mock_overview["total_donations"] == 100
        assert mock_overview["total_amount"] == Decimal("10000.00")

    def test_get_recent_donations(self, mock_dashboard_service, mock_current_user):
        """Test getting recent donations"""
        mock_donations = [Mock() for _ in range(10)]
        mock_dashboard_service.get_recent_donations.return_value = mock_donations
        
        assert len(mock_donations) == 10

    def test_get_donation_trends(self, mock_dashboard_service, mock_current_user):
        """Test getting donation trends"""
        mock_trends = {
            "daily": [100, 150, 200, 180, 220],
            "weekly": [500, 600, 700],
            "monthly": [2000, 2500, 3000]
        }
        
        mock_dashboard_service.get_trends.return_value = mock_trends
        
        assert len(mock_trends["daily"]) == 5
        assert len(mock_trends["monthly"]) == 3

    def test_get_top_campaigns(self, mock_dashboard_service, mock_current_user):
        """Test getting top campaigns"""
        mock_campaigns = [Mock() for _ in range(5)]
        mock_dashboard_service.get_top_campaigns.return_value = mock_campaigns
        
        assert len(mock_campaigns) == 5

    def test_get_donor_demographics(self, mock_dashboard_service, mock_current_user):
        """Test getting donor demographics"""
        mock_demographics = {
            "age_groups": {
                "18-25": 10,
                "26-35": 25,
                "36-50": 30,
                "51+": 35
            },
            "locations": {
                "USA": 50,
                "Canada": 20,
                "Mexico": 15,
                "Other": 15
            }
        }
        
        mock_dashboard_service.get_demographics.return_value = mock_demographics
        
        assert mock_demographics["age_groups"]["26-35"] == 25

    def test_get_payment_methods_distribution(self, mock_dashboard_service, mock_current_user):
        """Test getting payment methods distribution"""
        mock_distribution = {
            "credit_card": 60,
            "paypal": 25,
            "bank_transfer": 10,
            "crypto": 5
        }
        
        mock_dashboard_service.get_payment_distribution.return_value = mock_distribution
        
        assert mock_distribution["credit_card"] == 60

    def test_get_campaign_performance(self, mock_dashboard_service, mock_current_user):
        """Test getting campaign performance"""
        campaign_id = "campaign-123"
        
        mock_performance = {
            "total_raised": Decimal("5000.00"),
            "goal": Decimal("10000.00"),
            "donors_count": 50,
            "completion_percentage": 50.0
        }
        
        mock_dashboard_service.get_campaign_performance.return_value = mock_performance
        
        assert mock_performance["completion_percentage"] == 50.0

    def test_get_monthly_report(self, mock_dashboard_service, mock_current_user):
        """Test getting monthly report"""
        year = 2025
        month = 10
        
        mock_report = {
            "total_donations": 150,
            "total_amount": Decimal("15000.00"),
            "new_donors": 25,
            "returning_donors": 125
        }
        
        mock_dashboard_service.get_monthly_report.return_value = mock_report
        
        assert mock_report["new_donors"] == 25

    def test_get_real_time_stats(self, mock_dashboard_service, mock_current_user):
        """Test getting real-time statistics"""
        mock_stats = {
            "active_users": 15,
            "donations_today": 23,
            "amount_today": Decimal("2300.00")
        }
        
        mock_dashboard_service.get_realtime_stats.return_value = mock_stats
        
        assert mock_stats["active_users"] == 15

    def test_export_dashboard_data(self, mock_dashboard_service, mock_current_user):
        """Test exporting dashboard data"""
        date_range = {
            "start_date": datetime.now() - timedelta(days=30),
            "end_date": datetime.now()
        }
        
        mock_dashboard_service.export_data.return_value = "export-file-url"
        
        result = mock_dashboard_service.export_data(date_range)
        assert result == "export-file-url"
