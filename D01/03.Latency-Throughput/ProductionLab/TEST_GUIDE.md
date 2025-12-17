# Hướng Dẫn Test Production Lab

## Chuẩn Bị

```bash
# Khởi động hệ thống
cd /Users/tuanpn/Desktop/DS/SystemDesignLearning/D01/03.Latency-Throughput/ProductionLab
docker-compose up -d

# Kiểm tra trạng thái
docker-compose ps
```

---

## Test 1: Healthcheck và Dependency Management

### Mục tiêu
Kiểm tra Nginx đợi backend services healthy trước khi start và failover tự động khi service down.

### Các bước thực hiện

**Bước 1.1: Kiểm tra Health Status**
```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

**Kết quả mong đợi:**
- Tất cả app_* containers hiển thị `(healthy)`
- nginx_lb start sau khi các app healthy

**Bước 1.2: Test Failover**
```bash
# Stop một replica
docker stop app_fast_1

# Test endpoint READ (sẽ route sang replica còn lại)
curl http://localhost:8080/read

# Kiểm tra response có service="FAST_REPLICA_2"
```

**Kết quả mong đợi:**
- Request vẫn thành công
- Traffic tự động chuyển sang app_fast_2

**Bước 1.3: Khôi phục**
```bash
docker start app_fast_1
```

---

## Test 2: Graceful Shutdown

### Mục tiêu
Kiểm tra container shutdown an toàn, không mất request đang xử lý.

### Các bước thực hiện

**Bước 2.1: Gửi SIGTERM và quan sát logs**
```bash
# Terminal 1: Theo dõi logs
docker logs -f app_slow

# Terminal 2: Gửi SIGTERM
docker kill -s SIGTERM app_slow
```

**Kết quả mong đợi:**
```json
{"level": "INFO", "message": "Received signal 15. Starting graceful shutdown..."}
// Sleep 3 giây
{"level": "INFO", "message": "Graceful shutdown complete. Exiting."}
```

**Bước 2.2: Test 503 During Shutdown**
```bash
# Gửi SIGTERM và NGAY LẬP TỨC test request
docker kill -s SIGTERM app_slow & sleep 0.5 && curl -i http://localhost:8080/write
```

**Kết quả mong đợi:**
- HTTP 502 Bad Gateway (do container đã dừng)
- Hoặc HTTP 503 nếu request đến trong lúc shutdown

**Bước 2.3: Khôi phục**
```bash
docker start app_slow
sleep 3  # Đợi container healthy
```

---

## Test 3: Resource Limits và Saturation

### Mục tiêu
Kiểm tra CPU/Memory limits hoạt động và đo latency/throughput.

### Các bước thực hiện

**Bước 3.1: Kiểm tra Resource Limits**
```bash
# Xem cấu hình limits
docker inspect app_slow | grep -E "NanoCpus|Memory" | head -2

# Kết quả:
# "Memory": 536870912,        # 512MB
# "NanoCpus": 500000000,      # 0.5 CPU
```

**Bước 3.2: Test Latency Comparison**
```bash
# Test WRITE endpoint (50ms delay)
echo "=== WRITE (slow) ===" 
time for i in {1..10}; do curl -s -X POST http://localhost:8080/write > /dev/null; done

# Test READ endpoint (5ms delay)
echo "=== READ (fast) ===" 
time for i in {1..10}; do curl -s http://localhost:8080/read > /dev/null; done
```

**Kết quả mong đợi:**
- WRITE: ~500-700ms cho 10 requests (50ms/request + overhead)
- READ: ~100-250ms cho 10 requests (5ms/request + overhead)

**Bước 3.3: Test CPU Saturation với Load**
```bash
# Terminal 1: Monitor resources
watch -n 1 'docker stats --no-stream app_slow app_fast_1 app_fast_2'

# Terminal 2: Tạo load
seq 1 200 | xargs -P 50 -I {} curl -s -X POST http://localhost:8080/write > /dev/null
```

**Kết quả mong đợi:**
- app_slow CPU không vượt quá 50% (0.5 cores limit)
- Memory usage < 512MB
- Latency tăng khi saturated

**Bước 3.4: Test Throughput**
```bash
# Đo throughput với concurrent requests
ab -n 1000 -c 50 http://localhost:8080/read

# Hoặc dùng curl
time seq 1 100 | xargs -P 20 -I {} curl -s http://localhost:8080/read > /dev/null
```

---

## Test 4: Load Balancing Distribution

### Mục tiêu
Kiểm tra phân phối traffic giữa các replicas.

### Các bước thực hiện

```bash
# Gửi 20 requests và đếm distribution
for i in {1..20}; do 
  curl -s http://localhost:8080/read | grep -o 'FAST_REPLICA_[12]'
done | sort | uniq -c

# Kết quả mong đợi (weight 3:1):
# ~15 FAST_REPLICA_1
# ~5  FAST_REPLICA_2
```

---

## Test 5: Timeout và Error Handling

### Mục tiêu
Kiểm tra Nginx timeout và retry logic.

### Các bước thực hiện

**Bước 5.1: Test Proxy Timeout**
```bash
# Nginx có proxy_read_timeout 5s
# Nếu backend xử lý > 5s sẽ timeout

# Tạm thời tăng delay trong app.py hoặc test với slow endpoint
curl -i http://localhost:8080/write
```

**Bước 5.2: Test Retry Logic**
```bash
# Stop cả 2 replicas
docker stop app_fast_1 app_fast_2

# Test sẽ fail sau khi thử cả 2 servers
curl -i http://localhost:8080/read

# Khôi phục
docker start app_fast_1 app_fast_2
```

---

## Cải Thiện Đề Xuất

### 1. Sử dụng Production WSGI Server

**Vấn đề hiện tại:** Flask development server không handle concurrent requests tốt, không thể hiện rõ CPU saturation.

**Giải pháp:**

```dockerfile
# Dockerfile
FROM python:3.9-slim
WORKDIR /app
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN pip install flask gunicorn
COPY app.py .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

**Lợi ích:**
- 4 worker processes → tận dụng tốt CPU limit
- Handle concurrent requests tốt hơn
- Gần với production environment

### 2. Thêm Active Health Checks cho Nginx

**Vấn đề hiện tại:** Nginx chỉ phát hiện lỗi khi có request thất bại (passive).

**Giải pháp:** Sử dụng nginx-plus hoặc thêm external health checker

```yaml
# docker-compose.yml - thêm service
healthcheck_service:
  image: nginx/nginx-prometheus-exporter
  command: ["--nginx.scrape-uri=http://nginx_lb/health"]
```

Hoặc dùng script đơn giản:

```bash
# healthcheck.sh
while true; do
  curl -f http://app_fast_1:5000/health || docker-compose restart app_fast_1
  curl -f http://app_fast_2:5000/health || docker-compose restart app_fast_2
  sleep 5
done
```

### 3. Cải thiện Graceful Shutdown

**Vấn đề hiện tại:** Request đến trong lúc shutdown nhận 502/503.

**Giải pháp:** Thêm pre-stop hook

```python
# app.py - cải thiện
@app.route('/health', methods=['GET'])
def health_check():
    if not IS_RUNNING:
        return jsonify({"status": "shutdown_in_progress"}), 503
    return jsonify({"status": "ok", "service": SERVICE_NAME}), 200

def shutdown_handler(signum, frame):
    global IS_RUNNING
    IS_RUNNING = False  # Health check sẽ trả về 503
    logger.info(f"Received signal {signum}. Waiting for health check to propagate...")
    
    # Đợi Nginx phát hiện unhealthy (max_fails * fail_timeout)
    time.sleep(15)  # 3 fails * 5s = 15s
    
    logger.info("Cleaning up resources...")
    time.sleep(GRACEFUL_SHUTDOWN_DELAY_S)
    logger.info("Graceful shutdown complete. Exiting.")
    sys.exit(0)
```

### 4. Thêm Monitoring và Metrics

**Giải pháp:** Thêm Prometheus + Grafana

```yaml
# docker-compose.yml
prometheus:
  image: prom/prometheus
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
  ports:
    - "9090:9090"

grafana:
  image: grafana/grafana
  ports:
    - "3000:3000"
```

```python
# app.py - thêm metrics endpoint
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('app_requests_total', 'Total requests', ['service', 'endpoint'])
REQUEST_LATENCY = Histogram('app_request_latency_seconds', 'Request latency', ['service'])

@app.route('/metrics')
def metrics():
    return generate_latest()
```

### 5. Thêm Load Testing Tool

**Giải pháp:** Sử dụng k6 thay vì hey

```yaml
# docker-compose.yml
load_tester:
  image: grafana/k6
  volumes:
    - ./load-test.js:/scripts/load-test.js
  command: ["run", "/scripts/load-test.js"]
```

```javascript
// load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '30s', target: 20 },  // Ramp up
    { duration: '1m', target: 50 },   // Stay at 50 users
    { duration: '30s', target: 0 },   // Ramp down
  ],
};

export default function () {
  let res = http.get('http://nginx_lb/read');
  check(res, { 'status 200': (r) => r.status === 200 });
  sleep(1);
}
```

### 6. Thêm Circuit Breaker Pattern

**Giải pháp:** Implement trong application hoặc dùng service mesh

```python
# app.py - simple circuit breaker
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func):
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'HALF_OPEN'
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func()
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise e
```

---

## Tổng Kết

### Checklist Test
- [ ] Test 1: Healthcheck và Dependency Management
- [ ] Test 2: Graceful Shutdown
- [ ] Test 3: Resource Limits và Saturation
- [ ] Test 4: Load Balancing Distribution
- [ ] Test 5: Timeout và Error Handling

### Metrics Quan Trọng
- **Latency**: p50, p95, p99
- **Throughput**: requests/second
- **Error Rate**: % requests failed
- **Resource Usage**: CPU%, Memory%
- **Availability**: uptime %

### Best Practices
1. Luôn test graceful shutdown trước khi deploy
2. Monitor resource limits trong production
3. Set timeout phù hợp với SLA
4. Implement retry logic với exponential backoff
5. Sử dụng health checks cho tất cả services
6. Log structured data để dễ analyze
