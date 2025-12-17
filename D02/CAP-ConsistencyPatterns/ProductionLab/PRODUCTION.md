# Hướng Dẫn Triển Khai Production

## Checklist Trước Khi Triển Khai

### 1. Bảo Mật
- [ ] Thay đổi `SECRET_KEY` trong biến môi trường
- [ ] Xem xét và cập nhật tất cả mật khẩu mặc định
- [ ] Bật TLS/SSL cho kết nối bên ngoài
- [ ] Cấu hình firewall rules (chỉ mở các cổng cần thiết)
- [ ] Chạy quét bảo mật: `docker scan <image>`
- [ ] Xem xét non-root user trong Dockerfile

### 2. Cấu Hình
- [ ] Copy `.env.example` sang `.env` và cập nhật giá trị
- [ ] Đặt `NETWORK_TIMEOUT_SEC` phù hợp dựa trên độ trễ mạng
- [ ] Cấu hình `MAX_STALENESS_MS` dựa trên yêu cầu nghiệp vụ
- [ ] Đặt `LOG_LEVEL` thành `WARNING` hoặc `ERROR` trong production
- [ ] Cấu hình resource limits trong docker-compose.yml

### 3. Monitoring & Observability
- [ ] Thiết lập Prometheus để scrape endpoint `/metrics`
- [ ] Cấu hình alerting rules cho:
  - Thay đổi trạng thái circuit breaker
  - Staleness cao (> MAX_STALENESS_MS)
  - Lỗi kết nối
  - Tỷ lệ lỗi cao
- [ ] Thiết lập log aggregation (ELK, Splunk, CloudWatch)
- [ ] Cấu hình dashboards cho các metrics quan trọng

### 4. Lưu Trữ Dữ Liệu
- [ ] Xác minh volume mounts cho dữ liệu Redis
- [ ] Thiết lập chiến lược backup cho volumes
- [ ] Test quy trình restore
- [ ] Cấu hình Redis persistence (AOF enabled)

### 5. High Availability
- [ ] Triển khai trên nhiều availability zones
- [ ] Cấu hình load balancer cho app instances
- [ ] Thiết lập health check monitoring
- [ ] Test các kịch bản failover
- [ ] Tài liệu hóa runbooks cho các sự cố thường gặp

## Các Bước Triển Khai

### Bước 1: Chuẩn Bị Môi Trường
```bash
# Copy và cấu hình file môi trường
cp .env.example .env
nano .env  # Cập nhật tất cả giá trị

# Tạo secret key an toàn
python3 -c "import secrets; print(secrets.token_hex(32))"
# Thêm vào .env: SECRET_KEY=<generated_key>
```

### Bước 2: Build và Test Locally
```bash
# Build images
docker-compose build

# Chạy tests
docker-compose up -d
./run_tests.sh  # Test suite của bạn

# Kiểm tra logs
docker-compose logs -f

# Xác minh metrics endpoint
curl http://localhost:5001/metrics
curl http://localhost:5002/metrics
```

### Bước 3: Triển Khai lên Production
```bash
# Pull code mới nhất
git pull origin main

# Build với production tag
docker-compose -f docker-compose.yml build

# Deploy với zero-downtime
docker-compose up -d --no-deps --build app_cp
docker-compose up -d --no-deps --build app_ap

# Xác minh health
curl http://<production-host>:5001/health
curl http://<production-host>:5002/health
```

### Bước 4: Xác Minh Sau Triển Khai
```bash
# Kiểm tra tất cả services healthy
docker-compose ps

# Monitor logs để tìm lỗi
docker-compose logs -f --tail=100

# Test write operations
curl -X POST http://<host>:5001/write/test/value1
curl -X POST http://<host>:5002/write/test/value2

# Xác minh metrics collection
curl http://<host>:5001/metrics | grep app_requests_total
```

## Monitoring Endpoints

| Endpoint | Mục đích | Port |
|----------|---------|------|
| `/health` | Health check | 5001, 5002 |
| `/metrics` | Prometheus metrics | 5001, 5002 |
| `/circuit-breaker` | Trạng thái circuit breaker | 5001, 5002 |

## Các Metrics Quan Trọng Cần Monitor

### Application Metrics
- `app_requests_total` - Tổng requests theo mode, operation, status
- `app_request_latency_seconds` - Histogram độ trễ request
- `circuit_breaker_state` - Trạng thái circuit breaker (0=CLOSED, 1=HALF_OPEN, 2=OPEN)
- `data_staleness_ms` - Độ cũ dữ liệu theo node
- `db_connection_failures_total` - Lỗi kết nối database

### Ngưỡng Cảnh Báo (Khuyến Nghị)
- Circuit breaker OPEN > 1 phút
- Staleness > MAX_STALENESS_MS > 30 giây
- Tỷ lệ lỗi > 5% > 1 phút
- P99 latency > 500ms > 2 phút
- Tỷ lệ lỗi kết nối > 10% > 30 giây

## Cân Nhắc Về Scaling

### Horizontal Scaling
```bash
# Scale app instances
docker-compose up -d --scale app_ap=3 --scale app_cp=3

# Sử dụng load balancer (nginx, HAProxy, AWS ALB)
# Cấu hình session affinity cho Read-Your-Writes consistency
```

### Vertical Scaling
```yaml
# Cập nhật resource limits trong docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M
```

## Backup và Recovery

### Backup Dữ Liệu Redis
```bash
# Manual backup
docker exec db_g1 redis-cli BGSAVE
docker cp db_g1:/data/dump.rdb ./backups/db_g1_$(date +%Y%m%d).rdb

# Automated backup (thêm vào cron)
0 2 * * * /path/to/backup_script.sh
```

### Restore từ Backup
```bash
# Dừng container
docker stop db_g1

# Restore dữ liệu
docker cp ./backups/db_g1_20250112.rdb db_g1:/data/dump.rdb

# Khởi động container
docker start db_g1
```

## Troubleshooting

### Độ Trễ Cao
1. Kiểm tra trạng thái circuit breaker: `curl http://localhost:5001/circuit-breaker`
2. Xem xét metrics: `curl http://localhost:5001/metrics | grep latency`
3. Kiểm tra cài đặt network timeout
4. Xác minh hiệu năng database

### Circuit Breaker Bị Stuck OPEN
1. Kiểm tra db_g2 health: `docker exec db_g2 redis-cli ping`
2. Xem xét connection logs: `docker logs app_ap | grep DB_CONNECT_FAILURE`
3. Xác minh kết nối mạng giữa các containers
4. Restart db_g2 nếu cần: `docker restart db_g2`

### Dữ Liệu Không Nhất Quán
1. Kiểm tra staleness metrics: `curl http://localhost:5001/read/<key>`
2. Xác minh trạng thái replication
3. Kiểm tra partition events trong logs
4. Xem xét Circuit Breaker events

## Security Hardening

### Network Security
```yaml
# Sử dụng custom network với encryption
networks:
  cap_network:
    driver: overlay
    driver_opts:
      encrypted: "true"
```

### Secrets Management
```bash
# Sử dụng Docker secrets thay vì environment variables
echo "my-secret-key" | docker secret create app_secret_key -
```

### Rate Limiting
```python
# Thêm vào app.py
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.remote_addr,
    default_limits=["1000 per hour", "100 per minute"]
)
```

## Performance Tuning

### Tối Ưu Redis
```bash
# Tăng max connections
redis-server --maxclients 10000

# Bật pipelining
redis-cli --pipe < commands.txt

# Monitor slow queries
redis-cli SLOWLOG GET 10
```

### Tối Ưu Application
- Bật connection pooling cho Redis
- Implement caching layer (Redis cache)
- Sử dụng async I/O cho non-blocking operations
- Tối ưu session storage (dùng Redis thay vì cookies)

## Compliance và Auditing

### Yêu Cầu Logging
- Tất cả write operations được log với timestamp
- Thay đổi trạng thái circuit breaker được log
- Authentication/authorization events được log
- Data access patterns được log để audit

### Data Retention
- Cấu hình log rotation: max 10MB per file, giữ 3 files
- Archive logs sang S3/GCS để lưu trữ lâu dài
- Implement log anonymization cho PII data

## Disaster Recovery

### RTO/RPO Targets
- Recovery Time Objective (RTO): < 15 phút
- Recovery Point Objective (RPO): < 5 phút

### Quy Trình DR
1. Duy trì standby environment ở region khác
2. Replicate dữ liệu async sang DR site
3. Test failover hàng quý
4. Tài liệu hóa runbooks cho tất cả kịch bản
5. Đào tạo team về quy trình DR
