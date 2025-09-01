# Docker Development Standards

## Container-First Development
- All development must run in Docker containers
- Use `docker-compose.yml` for local development
- Never install dependencies globally on host system
- Test changes by rebuilding containers: `docker-compose build api`

## Service Configuration
Required services for full functionality:
- `api`: Main FastAPI application
- `db`: PostgreSQL database 
- `loki`: Log storage and indexing
- `promtail`: Log collection from containers
- `grafana`: Observability dashboards
- `prometheus`: Metrics collection
- `rabbitmq`: Message queue

## Environment Variables
Configure services via environment variables in `docker-compose.yml`:
```yaml
environment:
  - DATABASE_URL=${DATABASE_URL}
  - SERVICE_NAME=donations-api
  - VERSION=1.0.0
  - LOG_LEVEL=INFO
  - ENVIRONMENT=development
```

## Logging Configuration
- Use JSON file logging driver with rotation:
```yaml
logging:
  driver: json-file
  options:
    max-size: "10m"
    max-file: "3"
```
- Add `logging=promtail` label for log collection
- Logs flow: stdout → Docker → Promtail → Loki → Grafana

## Development Workflow
1. Make code changes
2. Build container: `docker-compose build api`
3. Restart service: `docker-compose restart api`
4. Check logs: `docker logs donations-api`
5. Test endpoints: `curl http://localhost:8000/health/`

## Health Checks
- Include health checks for all services
- Use proper intervals and timeouts
- Example for database:
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
  interval: 10s
  timeout: 5s
  retries: 5
```

## Port Mapping
Standard port assignments:
- API: `8000:8000`
- Database: `5432:5432`
- Grafana: `3000:3000`
- Loki: `3100:3100`
- Prometheus: `9090:9090`

## Volume Management
- Use named volumes for persistent data
- Mount source code for development: `.:/app`
- Exclude node_modules: `/app/node_modules`

## Container Dependencies
- Use `depends_on` with health conditions
- Wait for database to be ready before starting API
- Proper startup order: db → loki → promtail → api
