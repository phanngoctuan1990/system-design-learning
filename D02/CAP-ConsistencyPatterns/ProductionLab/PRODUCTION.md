# Production Deployment Guide

## Pre-deployment Checklist

### 1. Security
- [ ] Change `SECRET_KEY` in environment variables
- [ ] Review and update all default passwords
- [ ] Enable TLS/SSL for external connections
- [ ] Configure firewall rules (only expose necessary ports)
- [ ] Run security scan: `docker scan <image>`
- [ ] Review non-root user in Dockerfile

### 2. Configuration
- [ ] Copy `.env.example` to `.env` and update values
- [ ] Set appropriate `NETWORK_TIMEOUT_SEC` based on network latency
- [ ] Configure `MAX_STALENESS_MS` based on business requirements
- [ ] Set `LOG_LEVEL` to `WARNING` or `ERROR` in production
- [ ] Configure resource limits in docker-compose.yml

### 3. Monitoring & Observability
- [ ] Set up Prometheus to scrape `/metrics` endpoint
- [ ] Configure alerting rules for:
  - Circuit breaker state changes
  - High staleness (> MAX_STALENESS_MS)
  - Connection failures
  - High error rates
- [ ] Set up log aggregation (ELK, Splunk, CloudWatch)
- [ ] Configure dashboards for key metrics

### 4. Data Persistence
- [ ] Verify volume mounts for Redis data
- [ ] Set up backup strategy for volumes
- [ ] Test restore procedures
- [ ] Configure Redis persistence (AOF enabled)

### 5. High Availability
- [ ] Deploy across multiple availability zones
- [ ] Configure load balancer for app instances
- [ ] Set up health check monitoring
- [ ] Test failover scenarios
- [ ] Document runbooks for common incidents

## Deployment Steps

### Step 1: Prepare Environment
```bash
# Copy and configure environment file
cp .env.example .env
nano .env  # Update all values

# Generate secure secret key
python3 -c "import secrets; print(secrets.token_hex(32))"
# Add to .env: SECRET_KEY=<generated_key>
```

### Step 2: Build and Test Locally
```bash
# Build images
docker-compose build

# Run tests
docker-compose up -d
./run_tests.sh  # Your test suite

# Check logs
docker-compose logs -f

# Verify metrics endpoint
curl http://localhost:5001/metrics
curl http://localhost:5002/metrics
```

### Step 3: Deploy to Production
```bash
# Pull latest code
git pull origin main

# Build with production tag
docker-compose -f docker-compose.yml build

# Deploy with zero-downtime
docker-compose up -d --no-deps --build app_cp
docker-compose up -d --no-deps --build app_ap

# Verify health
curl http://<production-host>:5001/health
curl http://<production-host>:5002/health
```

### Step 4: Post-Deployment Verification
```bash
# Check all services are healthy
docker-compose ps

# Monitor logs for errors
docker-compose logs -f --tail=100

# Test write operations
curl -X POST http://<host>:5001/write/test/value1
curl -X POST http://<host>:5002/write/test/value2

# Verify metrics collection
curl http://<host>:5001/metrics | grep app_requests_total
```

## Monitoring Endpoints

| Endpoint | Purpose | Port |
|----------|---------|------|
| `/health` | Health check | 5001, 5002 |
| `/metrics` | Prometheus metrics | 5001, 5002 |
| `/circuit-breaker` | Circuit breaker status | 5001, 5002 |

## Key Metrics to Monitor

### Application Metrics
- `app_requests_total` - Total requests by mode, operation, status
- `app_request_latency_seconds` - Request latency histogram
- `circuit_breaker_state` - Circuit breaker state (0=CLOSED, 1=HALF_OPEN, 2=OPEN)
- `data_staleness_ms` - Data staleness by node
- `db_connection_failures_total` - Database connection failures

### Alert Thresholds (Recommended)
- Circuit breaker OPEN for > 1 minute
- Staleness > MAX_STALENESS_MS for > 30 seconds
- Error rate > 5% for > 1 minute
- P99 latency > 500ms for > 2 minutes
- Connection failure rate > 10% for > 30 seconds

## Scaling Considerations

### Horizontal Scaling
```bash
# Scale app instances
docker-compose up -d --scale app_ap=3 --scale app_cp=3

# Use load balancer (nginx, HAProxy, AWS ALB)
# Configure session affinity for Read-Your-Writes consistency
```

### Vertical Scaling
```yaml
# Update resource limits in docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M
```

## Backup and Recovery

### Backup Redis Data
```bash
# Manual backup
docker exec db_g1 redis-cli BGSAVE
docker cp db_g1:/data/dump.rdb ./backups/db_g1_$(date +%Y%m%d).rdb

# Automated backup (add to cron)
0 2 * * * /path/to/backup_script.sh
```

### Restore from Backup
```bash
# Stop container
docker stop db_g1

# Restore data
docker cp ./backups/db_g1_20250112.rdb db_g1:/data/dump.rdb

# Start container
docker start db_g1
```

## Troubleshooting

### High Latency
1. Check circuit breaker state: `curl http://localhost:5001/circuit-breaker`
2. Review metrics: `curl http://localhost:5001/metrics | grep latency`
3. Check network timeout settings
4. Verify database performance

### Circuit Breaker Stuck OPEN
1. Check db_g2 health: `docker exec db_g2 redis-cli ping`
2. Review connection logs: `docker logs app_ap | grep DB_CONNECT_FAILURE`
3. Verify network connectivity between containers
4. Restart db_g2 if necessary: `docker restart db_g2`

### Data Inconsistency
1. Check staleness metrics: `curl http://localhost:5001/read/<key>`
2. Verify replication status
3. Check for partition events in logs
4. Review Circuit Breaker events

## Security Hardening

### Network Security
```yaml
# Use custom network with encryption
networks:
  cap_network:
    driver: overlay
    driver_opts:
      encrypted: "true"
```

### Secrets Management
```bash
# Use Docker secrets instead of environment variables
echo "my-secret-key" | docker secret create app_secret_key -
```

### Rate Limiting
```python
# Add to app.py
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.remote_addr,
    default_limits=["1000 per hour", "100 per minute"]
)
```

## Performance Tuning

### Redis Optimization
```bash
# Increase max connections
redis-server --maxclients 10000

# Enable pipelining
redis-cli --pipe < commands.txt

# Monitor slow queries
redis-cli SLOWLOG GET 10
```

### Application Optimization
- Enable connection pooling for Redis
- Implement caching layer (Redis cache)
- Use async I/O for non-blocking operations
- Optimize session storage (use Redis instead of cookies)

## Compliance and Auditing

### Logging Requirements
- All write operations logged with timestamp
- Circuit breaker state changes logged
- Authentication/authorization events logged
- Data access patterns logged for audit

### Data Retention
- Configure log rotation: max 10MB per file, keep 3 files
- Archive logs to S3/GCS for long-term storage
- Implement log anonymization for PII data

## Disaster Recovery

### RTO/RPO Targets
- Recovery Time Objective (RTO): < 15 minutes
- Recovery Point Objective (RPO): < 5 minutes

### DR Procedures
1. Maintain standby environment in different region
2. Replicate data asynchronously to DR site
3. Test failover quarterly
4. Document runbooks for all scenarios
5. Train team on DR procedures
