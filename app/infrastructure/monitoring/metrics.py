"""
Prometheus metrics definitions
"""
from prometheus_client import Counter, Histogram, Gauge

# HTTP metrics
REQUEST_COUNT = Counter('donations_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('donations_request_duration_seconds', 'Request duration')

# Business metrics
USER_REGISTRATION_COUNT = Counter('user_registrations_total', 'Total user registrations', ['role'])
LOGIN_ATTEMPTS = Counter('login_attempts_total', 'Total login attempts', ['success'])
DONATION_COUNT = Counter('donations_created_total', 'Total donations created', ['status', 'organization_id'])
ACTIVE_USERS = Gauge('active_users', 'Number of active users')
DATABASE_CONNECTIONS = Gauge('database_connections_active', 'Active database connections')
