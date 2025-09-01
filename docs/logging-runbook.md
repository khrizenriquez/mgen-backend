# Logging Operations Runbook

## Overview

This document provides operational guidance for managing and querying logs in the Donations Management System. The system uses structured JSON logging with centralized storage via Loki and visualization through Grafana.

## Architecture

- **Application Logs**: Structured JSON format emitted to stdout
- **Collection**: Promtail collects logs from Docker containers
- **Storage**: Grafana Loki stores and indexes logs
- **Visualization**: Grafana dashboards for log analysis
- **Retention**: 14 days (configurable)

## Log Format

All logs follow this JSON structure:

```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "level": "INFO",
  "service": "donations-api",
  "env": "production",
  "version": "1.0.0",
  "logger": "app.main",
  "request_id": "req-123e4567-e89b-12d3-a456-426614174000",
  "method": "GET",
  "path": "/api/v1/donations",
  "status_code": 200,
  "latency_ms": 45.2,
  "user_id": "user-789",
  "message": "Request completed",
  "error_stack": "..."
}
```

## Common Log Queries

### 1. View Recent Application Logs

```logql
{service="donations-api"} | json
```

### 2. Filter by Log Level

```logql
{service="donations-api", level="ERROR"} | json
```

### 3. Search by Request ID

```logql
{service="donations-api"} | json | request_id="req-123e4567-e89b-12d3-a456-426614174000"
```

### 4. Find Slow Requests (>1 second)

```logql
{service="donations-api"} | json | latency_ms > 1000
```

### 5. Error Rate by Endpoint

```logql
sum by (path) (count_over_time({service="donations-api", level="ERROR"} | json [5m]))
```

### 6. 5xx HTTP Errors

```logql
{service="donations-api"} | json | status_code >= 500
```

### 7. Authentication Failures

```logql
{service="donations-api"} | json | message =~ "(?i)(auth|unauthorized|forbidden)"
```

### 8. Database Errors

```logql
{service="donations-api"} | json | message =~ "(?i)(database|sql|connection)"
```

## Grafana Dashboard Usage

### Pre-built Dashboards

1. **Donations API Logs** (`donations-logs`)
   - Log volume by level
   - HTTP status codes over time
   - Error log table
   - Live log stream

### Creating Custom Dashboards

1. Go to Grafana → Dashboards → New
2. Add panel with Loki data source
3. Use LogQL queries from the examples above
4. Configure visualizations (time series, table, logs)

## Operational Procedures

### Investigating Errors

1. **Identify the Issue**
   ```logql
   {service="donations-api", level="ERROR"} | json
   ```

2. **Find Related Requests**
   ```logql
   {service="donations-api"} | json | request_id="EXTRACTED_REQUEST_ID"
   ```

3. **Check for Patterns**
   ```logql
   sum by (path, status_code) (count_over_time({service="donations-api"} | json [1h]))
   ```

### Performance Analysis

1. **Latency Distribution**
   ```logql
   histogram_quantile(0.95, 
     sum(rate({service="donations-api"} | json | unwrap latency_ms [5m])) by (le)
   )
   ```

2. **Slowest Endpoints**
   ```logql
   topk(10, avg by (path) (avg_over_time({service="donations-api"} | json | unwrap latency_ms [1h])))
   ```

### User Activity Tracking

1. **User Requests**
   ```logql
   {service="donations-api"} | json | user_id="USER_ID"
   ```

2. **User Error Rate**
   ```logql
   sum by (user_id) (count_over_time({service="donations-api", level="ERROR"} | json [1h]))
   ```

## Alerting

### Recommended Alerts

1. **High Error Rate**
   ```logql
   sum(rate({service="donations-api", level="ERROR"} | json [5m])) > 0.1
   ```

2. **High Latency**
   ```logql
   histogram_quantile(0.95, 
     sum(rate({service="donations-api"} | json | unwrap latency_ms [5m])) by (le)
   ) > 1000
   ```

3. **Service Down**
   ```logql
   absent_over_time({service="donations-api"} [5m])
   ```

## Troubleshooting

### Common Issues

#### 1. No Logs Appearing

- Check if containers are running: `docker ps`
- Verify Promtail configuration: `docker logs donations-promtail`
- Check Loki status: `curl http://localhost:3100/ready`

#### 2. Logs Not Being Parsed

- Verify JSON format in application logs
- Check Promtail pipeline configuration
- Review Loki ingestion errors

#### 3. High Storage Usage

- Check retention policies in Loki config
- Monitor log volume: `sum(rate({service="donations-api"} [1h]))`
- Consider adjusting log levels

#### 4. Slow Queries

- Use specific label filters
- Limit time ranges
- Use appropriate aggregations

### Emergency Procedures

#### Disable Logging (Emergency)

```bash
# Temporarily reduce log level
docker exec donations-api env LOG_LEVEL=ERROR

# Stop log collection
docker stop donations-promtail
```

#### Log Storage Cleanup

```bash
# Access Loki container
docker exec -it donations-loki sh

# Check storage usage
du -sh /tmp/loki

# Manual cleanup (if needed)
# Note: This will delete ALL logs
rm -rf /tmp/loki/chunks/*
```

## Configuration

### Environment Variables

- `LOG_LEVEL`: Set log verbosity (DEBUG, INFO, WARNING, ERROR)
- `SERVICE_NAME`: Service identifier for logs
- `ENVIRONMENT`: Environment identifier (dev, staging, prod)
- `VERSION`: Application version

### Log Rotation

Docker handles log rotation automatically:
- Max file size: 10MB
- Max files: 3
- Total max: 30MB per container

### Retention Policies

- **Loki Storage**: 14 days (configurable in loki-config.yml)
- **Docker Logs**: 30MB total per container
- **Grafana Dashboards**: No automatic cleanup

## Maintenance

### Regular Tasks

1. **Weekly**: Review error trends and patterns
2. **Monthly**: Analyze storage usage and performance
3. **Quarterly**: Review and update alerting rules

### Updates

When updating logging configuration:

1. Test changes in development environment
2. Update docker-compose.yml if needed
3. Restart affected services
4. Verify log collection continues
5. Update documentation

## Security Considerations

- PII masking is automatically applied
- Logs contain no sensitive authentication data
- Access to Grafana should be restricted
- Log retention should comply with data policies

## Support Contacts

- **Application Logs**: Development Team
- **Infrastructure**: DevOps Team  
- **Grafana/Loki**: Platform Team

---

*Last updated: 2024-01-15*
*Version: 1.0*