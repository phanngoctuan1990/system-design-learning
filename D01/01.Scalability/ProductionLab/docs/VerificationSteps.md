# Production Lab Verification Steps

## 1. Kiểm tra các service healthy

### Khởi động hệ thống
```bash
docker-compose up -d
```

### Kiểm tra trạng thái containers
```bash
docker-compose ps
```
**Kết quả mong đợi:** Tất cả services hiển thị `(healthy)`

### Kiểm tra health endpoints
```bash
curl http://localhost:81/health
```
**Kết quả mong đợi:** `OK: Application and Redis healthy.`

## 2. Kiểm tra Resource Isolation (Bulkheads)

### Xem resource limits
```bash
docker inspect app_clone_1 --format='{{.HostConfig.Memory}}'
docker inspect app_clone_1 --format='{{.HostConfig.CpuQuota}}'
```
**Kết quả mong đợi:** 
- Memory: `134217728` (128MB)
- CPU: `50000` (0.5 CPU core)

### Kiểm tra resource usage
```bash
docker stats app_clone_1 app_clone_2
# Mở terminal khác
bash test_traffic.sh
```
**Kết quả mong đợi:** Memory và CPU usage nằm trong giới hạn đã set

## 3. Kiểm tra Graceful Shutdown (Resilience)

### Test graceful shutdown
```bash
# Gửi SIGTERM signal
docker kill --signal=SIGTERM app_clone_1
```

### Kiểm tra logs graceful shutdown
```bash
docker-compose logs app_clone_1 | tail -10
```
**Kết quả mong đợi:** Logs hiển thị graceful shutdown process với timeout 3s

### Restart container
```bash
docker-compose up -d app_clone_1
```

## 4. Kiểm tra Failover (Redundancy)

### Test Redis failover
```bash
# Stop Redis
docker stop redis_session_cache

# Kiểm tra app health status
docker-compose ps
```
**Kết quả mong đợi:** Cả app_clone_1 và app_clone_2 chuyển sang `(unhealthy)` sau ~45s

### Test app failover
```bash
# Restart Redis
docker start redis_session_cache

# Stop một app instance
docker stop app_clone_1

# Test load balancer vẫn hoạt động
curl http://localhost:81/
```
**Kết quả mong đợi:** Request vẫn được xử lý bởi app_clone_2

### Test load balancing
```bash
# Restart app_clone_1
docker start app_clone_1

# Gửi nhiều requests
for i in {1..10}; do curl http://localhost:81/; echo; done
```
**Kết quả mong đợi:** Requests được phân phối giữa app_clone_1 và app_clone_2

### Kiểm tra nginx load balancer config
```bash
docker exec nginx_lb cat /etc/nginx/nginx.conf
```
**Kết quả mong đợi:** Cấu hình least_conn với cả hai upstream servers

## Cleanup
```bash
docker-compose down
```
