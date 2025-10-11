"""
Monitoring module for metrics and observability - Donations Guatemala
"""
from app.infrastructure.monitoring.metrics import (
    # HTTP Metrics
    REQUEST_COUNT,
    REQUEST_DURATION,

    # Authentication & User Metrics
    USER_REGISTRATION_COUNT,
    LOGIN_ATTEMPTS,
    ACTIVE_USERS,

    # Donation Business Metrics
    DONATION_COUNT,
    DONATION_AMOUNT_TOTAL,
    DONATION_STATUS_CHANGES,

    # Financial Metrics
    TOTAL_DONATIONS_AMOUNT,
    AVERAGE_DONATION_AMOUNT,

    # Database Metrics
    DATABASE_CONNECTIONS,
    DATABASE_QUERY_DURATION,

    # Business Intelligence Metrics
    DONATIONS_BY_STATUS,
    TOP_DONOR_AMOUNT,

    # Error Metrics
    BUSINESS_ERRORS,
    VALIDATION_ERRORS,

    # Performance Metrics
    MEMORY_USAGE,
    CPU_USAGE_PERCENT,

    # Organization Metrics
    ORGANIZATION_COUNT,
    DONATIONS_PER_ORGANIZATION,

    # API Performance
    API_RESPONSE_TIME
)

__all__ = [
    # HTTP Metrics
    'REQUEST_COUNT',
    'REQUEST_DURATION',

    # Authentication & User Metrics
    'USER_REGISTRATION_COUNT',
    'LOGIN_ATTEMPTS',
    'ACTIVE_USERS',

    # Donation Business Metrics
    'DONATION_COUNT',
    'DONATION_AMOUNT_TOTAL',
    'DONATION_STATUS_CHANGES',

    # Financial Metrics
    'TOTAL_DONATIONS_AMOUNT',
    'AVERAGE_DONATION_AMOUNT',

    # Database Metrics
    'DATABASE_CONNECTIONS',
    'DATABASE_QUERY_DURATION',

    # Business Intelligence Metrics
    'DONATIONS_BY_STATUS',
    'TOP_DONOR_AMOUNT',

    # Error Metrics
    'BUSINESS_ERRORS',
    'VALIDATION_ERRORS',

    # Performance Metrics
    'MEMORY_USAGE',
    'CPU_USAGE_PERCENT',

    # Organization Metrics
    'ORGANIZATION_COUNT',
    'DONATIONS_PER_ORGANIZATION',

    # API Performance
    'API_RESPONSE_TIME'
]
