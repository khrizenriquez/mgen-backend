"""
Business metrics calculation module for Donations Guatemala
Generates slower-refreshing business intelligence metrics
"""
import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy import func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.database import get_db
from app.infrastructure.logging import get_logger
from app.infrastructure.monitoring.metrics import (
    TOTAL_DONATIONS_AMOUNT,
    AVERAGE_DONATION_AMOUNT,
    DONATIONS_BY_STATUS,
    ORGANIZATION_COUNT,
    TOP_DONOR_AMOUNT
)

logger = get_logger(__name__)


async def generate_business_metrics() -> Dict[str, Any]:
    """
    Generate business intelligence metrics
    This data changes less frequently than technical metrics
    """
    try:
        async with get_db() as db:
            metrics = await _calculate_business_metrics(db)

            # Update Prometheus Gauges with current values
            await _update_prometheus_gauges(metrics)

            return {
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": metrics,
                "update_interval": "5m",  # Recommended refresh interval
                "description": "Business intelligence metrics for Donations Guatemala"
            }

    except Exception as e:
        logger.error("Error calculating business metrics", error=str(e), exc_info=True)
        return {
            "error": "Failed to calculate business metrics",
            "timestamp": datetime.utcnow().isoformat()
        }


async def _calculate_business_metrics(db: AsyncSession) -> Dict[str, Any]:
    """Calculate all business metrics from database"""

    # Total donations amount
    total_amount_result = await db.execute(
        text("SELECT COALESCE(SUM(amount_gtq), 0) as total FROM donations WHERE status_id = 2")  # APPROVED
    )
    total_amount = total_amount_result.scalar() or 0

    # Average donation amount
    avg_amount_result = await db.execute(
        text("SELECT COALESCE(AVG(amount_gtq), 0) as avg FROM donations WHERE status_id = 2")
    )
    avg_amount = avg_amount_result.scalar() or 0

    # Donations by status
    status_counts_result = await db.execute(
        text("""
            SELECT status_id, COUNT(*) as count
            FROM donations
            GROUP BY status_id
        """)
    )
    status_counts = {row[0]: row[1] for row in status_counts_result.fetchall()}

    # Total organizations
    org_count_result = await db.execute(
        text("SELECT COUNT(*) FROM organizations WHERE active = true")
    )
    org_count = org_count_result.scalar() or 0

    # Top donors (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    top_donors_result = await db.execute(
        text("""
            SELECT
                COALESCE(d.user_id::text, 'anonymous') as donor_id,
                COALESCE(SUM(d.amount_gtq), 0) as total_amount
            FROM donations d
            WHERE d.status_id = 2
            AND d.created_at >= :thirty_days_ago
            GROUP BY d.user_id
            ORDER BY total_amount DESC
            LIMIT 10
        """),
        {"thirty_days_ago": thirty_days_ago}
    )
    top_donors = [{"donor_id": row[0], "amount": float(row[1])} for row in top_donors_result.fetchall()]

    # Monthly donation trends (last 12 months)
    monthly_trends_result = await db.execute(
        text("""
            SELECT
                DATE_TRUNC('month', created_at) as month,
                COUNT(*) as donation_count,
                COALESCE(SUM(amount_gtq), 0) as total_amount
            FROM donations
            WHERE status_id = 2
            AND created_at >= :one_year_ago
            GROUP BY DATE_TRUNC('month', created_at)
            ORDER BY month DESC
        """),
        {"one_year_ago": datetime.utcnow() - timedelta(days=365)}
    )
    monthly_trends = [
        {
            "month": row[0].isoformat() if row[0] else None,
            "count": row[1],
            "amount": float(row[2])
        }
        for row in monthly_trends_result.fetchall()
    ]

    # Success rate calculation
    total_donations_result = await db.execute(text("SELECT COUNT(*) FROM donations"))
    total_donations = total_donations_result.scalar() or 0

    approved_donations_result = await db.execute(text("SELECT COUNT(*) FROM donations WHERE status_id = 2"))
    approved_donations = approved_donations_result.scalar() or 0

    success_rate = (approved_donations / total_donations * 100) if total_donations > 0 else 0

    return {
        "financial_metrics": {
            "total_donations_amount_gtq": float(total_amount),
            "average_donation_amount_gtq": float(avg_amount),
            "total_donations_count": total_donations,
            "approved_donations_count": approved_donations,
            "success_rate_percent": round(success_rate, 2)
        },
        "status_breakdown": {
            "pending": status_counts.get(1, 0),    # PENDING
            "approved": status_counts.get(2, 0),   # APPROVED
            "declined": status_counts.get(3, 0),   # DECLINED
            "expired": status_counts.get(4, 0)     # EXPIRED
        },
        "organization_metrics": {
            "total_organizations": org_count,
            "active_organizations": org_count  # Assuming all are active
        },
        "top_donors_30_days": top_donors,
        "monthly_trends": monthly_trends,
        "performance_indicators": {
            "conversion_rate": round(success_rate, 2),
            "average_transaction_value": float(avg_amount),
            "monthly_growth_rate": _calculate_growth_rate(monthly_trends)
        }
    }


def _calculate_growth_rate(monthly_trends: List[Dict]) -> float:
    """Calculate month-over-month growth rate"""
    if len(monthly_trends) < 2:
        return 0.0

    current_month = monthly_trends[0]["amount"] if monthly_trends else 0
    previous_month = monthly_trends[1]["amount"] if len(monthly_trends) > 1 else 0

    if previous_month == 0:
        return 0.0 if current_month == 0 else 100.0

    growth_rate = ((current_month - previous_month) / previous_month) * 100
    return round(growth_rate, 2)


async def _update_prometheus_gauges(metrics: Dict[str, Any]) -> None:
    """Update Prometheus Gauges with calculated business metrics"""
    try:
        # Update financial metrics
        TOTAL_DONATIONS_AMOUNT.set(metrics["financial_metrics"]["total_donations_amount_gtq"])
        AVERAGE_DONATION_AMOUNT.set(metrics["financial_metrics"]["average_donation_amount_gtq"])

        # Update status breakdown
        for status, count in metrics["status_breakdown"].items():
            DONATIONS_BY_STATUS.labels(status=status).set(count)

        # Update organization count
        ORGANIZATION_COUNT.set(metrics["organization_metrics"]["total_organizations"])

        # Update top donor metrics (simplified - just the highest amount)
        if metrics["top_donors_30_days"]:
            top_amount = max(donor["amount"] for donor in metrics["top_donors_30_days"])
            TOP_DONOR_AMOUNT.labels(donor_id="top").set(top_amount)

        logger.debug("Prometheus business metrics gauges updated successfully")

    except Exception as e:
        logger.error("Error updating Prometheus gauges", error=str(e), exc_info=True)


# Utility function for manual testing
async def test_business_metrics():
    """Test function to manually verify business metrics calculation"""
    print("🔍 Testing business metrics calculation...")
    metrics = await generate_business_metrics()

    print("✅ Business metrics generated successfully!")
    print(f"📊 Total donations: {metrics['metrics']['financial_metrics']['total_donations_amount_gtq']} GTQ")
    print(f"📈 Success rate: {metrics['metrics']['financial_metrics']['success_rate_percent']}%")
    print(f"🏢 Organizations: {metrics['metrics']['organization_metrics']['total_organizations']}")

    return metrics


if __name__ == "__main__":
    # Allow running this module directly for testing
    asyncio.run(test_business_metrics())
