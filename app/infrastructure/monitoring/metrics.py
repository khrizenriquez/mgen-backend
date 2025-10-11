"""
Prometheus metrics definitions for Donations Guatemala
"""
from prometheus_client import Counter, Histogram, Gauge, Summary

# HTTP Request Metrics
REQUEST_COUNT = Counter(
    'donations_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint']
)
REQUEST_DURATION = Histogram(
    'donations_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Authentication & User Metrics
USER_REGISTRATION_COUNT = Counter(
    'user_registrations_total',
    'Total user registrations',
    ['role', 'organization_id']
)
LOGIN_ATTEMPTS = Counter(
    'login_attempts_total',
    'Total login attempts',
    ['success', 'method']
)
ACTIVE_USERS = Gauge(
    'active_users_total',
    'Number of active users',
    ['role']
)

# Donation Business Metrics
DONATION_COUNT = Counter(
    'donations_created_total',
    'Total donations created',
    ['status', 'organization_id', 'currency']
)
DONATION_AMOUNT_TOTAL = Counter(
    'donation_amount_total',
    'Total donation amount by currency',
    ['currency', 'status']
)
DONATION_STATUS_CHANGES = Counter(
    'donation_status_changes_total',
    'Total donation status changes',
    ['from_status', 'to_status']
)

# Financial Metrics
TOTAL_DONATIONS_AMOUNT = Gauge(
    'total_donations_amount_gtq',
    'Total donations amount in GTQ'
)
AVERAGE_DONATION_AMOUNT = Gauge(
    'average_donation_amount_gtq',
    'Average donation amount in GTQ'
)

# Database Metrics
DATABASE_CONNECTIONS = Gauge(
    'database_connections_active',
    'Active database connections',
    ['database']
)
DATABASE_QUERY_DURATION = Histogram(
    'database_query_duration_seconds',
    'Database query duration',
    ['operation', 'table'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

# Business Intelligence Metrics
DONATIONS_BY_STATUS = Gauge(
    'donations_by_status',
    'Number of donations by status',
    ['status']
)
TOP_DONOR_AMOUNT = Gauge(
    'top_donor_amount_gtq',
    'Top donor total amount in GTQ',
    ['donor_id']
)

# Error Metrics
BUSINESS_ERRORS = Counter(
    'business_errors_total',
    'Business logic errors',
    ['error_type', 'endpoint']
)
VALIDATION_ERRORS = Counter(
    'validation_errors_total',
    'Request validation errors',
    ['field', 'endpoint']
)

# Performance Metrics
MEMORY_USAGE = Gauge(
    'memory_usage_bytes',
    'Memory usage in bytes',
    ['type']  # heap, rss, etc.
)
CPU_USAGE_PERCENT = Gauge(
    'cpu_usage_percent',
    'CPU usage percentage'
)

# Organization Metrics
ORGANIZATION_COUNT = Gauge(
    'organizations_total',
    'Total number of organizations'
)
DONATIONS_PER_ORGANIZATION = Counter(
    'donations_per_organization_total',
    'Total donations per organization',
    ['organization_id']
)

# API Response Time Percentiles
API_RESPONSE_TIME = Summary(
    'api_response_time_seconds',
    'API response time percentiles',
    ['endpoint', 'method']
)
