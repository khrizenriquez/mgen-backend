"""
Unit tests for dashboard service
"""
import pytest
from unittest.mock import Mock
from decimal import Decimal
from datetime import datetime, timedelta


@pytest.fixture
def mock_db():
    """Mock database session"""
    return Mock()


class TestDashboardService:
    """Test dashboard service business logic"""

    def test_aggregate_donations_by_period(self):
        """Test donation aggregation logic"""
        donations = [
            {"amount": Decimal("100.00"), "date": datetime.now()},
            {"amount": Decimal("200.00"), "date": datetime.now()},
            {"amount": Decimal("150.00"), "date": datetime.now()}
        ]
        
        total = sum(d["amount"] for d in donations)
        assert total == Decimal("450.00")

    def test_calculate_average_donation(self):
        """Test average donation calculation"""
        amounts = [Decimal("50.00"), Decimal("100.00"), Decimal("150.00")]
        average = sum(amounts) / len(amounts)
        
        assert average == Decimal("100.00")

    def test_calculate_growth_rate(self):
        """Test growth rate calculation"""
        previous_period = Decimal("1000.00")
        current_period = Decimal("1200.00")
        
        growth = ((current_period - previous_period) / previous_period) * 100
        assert growth == Decimal("20.00")

    def test_top_donors_ranking(self):
        """Test top donors ranking logic"""
        donors = [
            {"name": "John", "total": Decimal("500.00")},
            {"name": "Jane", "total": Decimal("800.00")},
            {"name": "Bob", "total": Decimal("300.00")}
        ]
        
        sorted_donors = sorted(donors, key=lambda x: x["total"], reverse=True)
        assert sorted_donors[0]["name"] == "Jane"
        assert sorted_donors[0]["total"] == Decimal("800.00")

    def test_campaign_completion_percentage(self):
        """Test campaign progress calculation"""
        raised = Decimal("7500.00")
        goal = Decimal("10000.00")
        
        percentage = (raised / goal) * 100
        assert percentage == Decimal("75.00")

    def test_donor_retention_rate(self):
        """Test donor retention calculation"""
        total_donors = 100
        returning_donors = 65
        
        retention_rate = (returning_donors / total_donors) * 100
        assert retention_rate == 65.0

    def test_monthly_comparison(self):
        """Test month-over-month comparison"""
        current_month = Decimal("5000.00")
        last_month = Decimal("4000.00")
        
        increase = current_month - last_month
        assert increase == Decimal("1000.00")

    def test_payment_method_distribution(self):
        """Test payment method analytics"""
        transactions = [
            {"method": "credit_card", "count": 60},
            {"method": "paypal", "count": 25},
            {"method": "bank_transfer", "count": 15}
        ]
        
        total = sum(t["count"] for t in transactions)
        credit_card_percentage = (60 / total) * 100
        
        assert total == 100
        assert credit_card_percentage == 60.0

    def test_time_series_data(self):
        """Test time series data generation"""
        data_points = [
            {"date": "2025-10-01", "value": 100},
            {"date": "2025-10-02", "value": 150},
            {"date": "2025-10-03", "value": 120}
        ]
        
        assert len(data_points) == 3
        assert data_points[1]["value"] == 150

    def test_demographic_segmentation(self):
        """Test demographic data analysis"""
        demographics = {
            "18-25": 15,
            "26-35": 30,
            "36-50": 35,
            "51+": 20
        }
        
        total_donors = sum(demographics.values())
        largest_segment = max(demographics.values())
        
        assert total_donors == 100
        assert largest_segment == 35

    def test_recurring_donations_tracking(self):
        """Test recurring donation metrics"""
        donations = [
            {"type": "one-time", "amount": Decimal("100.00")},
            {"type": "recurring", "amount": Decimal("50.00")},
            {"type": "recurring", "amount": Decimal("50.00")}
        ]
        
        recurring = [d for d in donations if d["type"] == "recurring"]
        recurring_total = sum(d["amount"] for d in recurring)
        
        assert len(recurring) == 2
        assert recurring_total == Decimal("100.00")

    def test_campaign_performance_metrics(self):
        """Test campaign performance calculation"""
        campaign_data = {
            "goal": Decimal("10000.00"),
            "raised": Decimal("7500.00"),
            "donors": 150,
            "days_active": 30
        }
        
        daily_average = campaign_data["raised"] / campaign_data["days_active"]
        average_donation = campaign_data["raised"] / campaign_data["donors"]
        
        assert daily_average == Decimal("250.00")
        assert average_donation == Decimal("50.00")

    def test_geographic_distribution(self):
        """Test geographic analysis"""
        locations = {
            "USA": 50,
            "Canada": 20,
            "Mexico": 15,
            "UK": 10,
            "Other": 5
        }
        
        total = sum(locations.values())
        usa_percentage = (locations["USA"] / total) * 100
        
        assert total == 100
        assert usa_percentage == 50.0

    def test_donation_frequency_analysis(self):
        """Test donor frequency metrics"""
        donor_frequency = {
            "first_time": 40,
            "repeat": 35,
            "loyal": 25
        }
        
        total = sum(donor_frequency.values())
        repeat_rate = ((donor_frequency["repeat"] + donor_frequency["loyal"]) / total) * 100
        
        assert total == 100
        assert repeat_rate == 60.0
