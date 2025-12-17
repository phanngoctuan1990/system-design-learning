# Production Lab: Hardening Availability (Fault Tolerance & Failover)

## 1. Executive Summary
Lab này là bước chuyển mình từ **Developer Local** sang **Production Grade**. Chúng ta không chỉ "chạy được app", mà còn xây dựng một hệ thống có khả năng **Tự phục hồi (Self-Healing)** và **Chịu lỗi (Fault Tolerant)**.

**Mục tiêu cốt lõi:**
1.  **Zero-Downtime Deployment:** Sử dụng **Gunicorn** để xử lý Graceful Shutdown.
2.  **Aggressive Failover:** Tinh chỉnh Nginx để loại bỏ node chết trong **1 giây** (thay vì 10-60s mặc định).
3.  **Deep Health Check:** Đảm bảo traffic không đi vào các node "Zombie" (sống nhưng mất kết nối DB).

## 2. Hardened Architecture Configuration

Sự khác biệt nằm ở cấu hình "chiến đấu" trong `nginx/nginx_prod.conf`:

```nginx
upstream backend {
    # Tinh chỉnh fail_timeout xuống 1 giây (Aggressive)
    # Nếu gặp 3 lỗi liên tiếp (max_fails=3), Nginx sẽ loại bỏ server trong 1s.
    server app-server-a:8000 max_fails=3 fail_timeout=1s; 
    server app-server-b:8000 max_fails=3 fail_timeout=1s;
}

server {
    location / {
        proxy_pass http://backend;
        # Circuit Breaker: Tự động chuyển request sang node khác nếu gặp lỗi
        proxy_next_upstream error timeout http_500 http_502 http_503 http_504; 
    }
}
```

> **Why Passive Health Check?** Nginx OSS dùng Passive Check (dựa trên traffic thật). Đây là cách hiệu quả nhất để detect lỗi mà không cần agent phụ trợ. Cấu hình trên đảm bảo **MTTR (Mean Time To Recovery)** cực thấp.

## 3. Verification Playbook (Chaos Engineering)

Chúng ta sẽ thực hiện 3 bài test để chứng minh hệ thống đạt chuẩn Production.

### 🧪 Test 1: Sanity Check (Deep Health)
**Mục tiêu:** Đảm bảo ứng dụng và Nginx đang hoạt động đúng trước khi phá hoại.

1.  **Khởi động Stack:**
    ```bash
    docker compose up -d --build
    ```

2.  **Verify Endpoint:**
    ```bash
    # Test qua Load Balancer
    curl -I http://localhost:8080/health_check
    ```
    > *Kỳ vọng:* `HTTP/1.1 200 OK`
    > - Cả 2 app servers chạy với Gunicorn (4 workers mỗi node)
    > - Nginx load balancer hoạt động bình thường

### 🧪 Test 2: Hard Failure & Fast Failover
**Mục tiêu:** Chứng minh Nginx loại bỏ node chết trong 1-2 giây mà User không nhận ra.

1.  **Chạy k6 Load Test (Background):**
    ```bash
    docker compose run --rm -d k6-runner run --vus 10 --duration 1m /home/k6/test.js
    ```

2.  **Simulate Disaster (Kill Node A):**
    ```bash
    # Đợi 10 giây để load test ổn định
    sleep 10
    echo "💣 Killing Node A..."
    docker stop productionlab-app-server-a-1
    ```

3.  **Quan sát Logs Nginx (Real-time):**
    ```bash
    docker logs nginx-lb 2>&1 | grep -i "upstream\|error\|refused" | tail -15
    ```
    > *Kỳ vọng:*
    > - Bạn sẽ thấy nhiều dòng "upstream server temporarily disabled"
    > - Sau 1-2 giây, không còn request nào được gửi tới Node A
    > - Traffic dồn 100% sang Node B
    > - Không có lỗi 502 kéo dài (circuit breaker hoạt động)

4.  **Verify Node B đang xử lý 100% traffic:**
    ```bash
    docker logs nginx-lb 2>&1 | grep "200" | tail -10
    ```
    > *Kỳ vọng:* Tất cả requests trả về 200 OK

### 🧪 Test 3: Auto Recovery (Fail-back)
**Mục tiêu:** Chứng minh hệ thống tự khôi phục khi Node A sống lại.

1.  **Hồi sinh Node A:**
    ```bash
    docker start productionlab-app-server-a-1
    echo "🚑 Node A is back online"
    ```

2.  **Đợi Nginx phát hiện Node A healthy:**
    ```bash
    sleep 5
    docker logs productionlab-app-server-a-1 2>&1 | tail -10
    ```
    > *Kỳ vọng:* Thấy Gunicorn khởi động thành công với 4 workers

3.  **Verify traffic được phân tán đều:**
    ```bash
    # Gửi 10 requests và đếm phân bố
    for i in {1..10}; do curl -s http://localhost:8080/ | grep -o "NODE_[AB]"; done | sort | uniq -c
    ```
    > *Kỳ vọng:*
    > - NODE_A: ~5 requests (50%)
    > - NODE_B: ~5 requests (50%)
    > - Load balancing được khôi phục hoàn toàn

## 4. Senior Architect Insights

| Hiện tượng quan sát | Giải thích kỹ thuật (The "Why") |
| :--- | :--- |
| **Failover cực nhanh (1-2s)** | Do `fail_timeout=1s` và `max_fails=3`. Nginx phát hiện 3 lỗi liên tiếp và loại bỏ node trong 1 giây. Trong K8s, cái này tương đương với **Readiness Probe** frequency ngắn. Trade-off là có thể bị "flapping" nếu mạng chập chờn, nhưng với internal network thì an toàn. |
| **Không có lỗi 502 kéo dài** | Do `proxy_next_upstream error timeout http_500 http_502 http_503 http_504`. Nginx không trả lỗi ngay cho client mà âm thầm retry sang node khác. Đây là **Client-side Resilience** được implement ở tầng Infrastructure. |
| **"Upstream server temporarily disabled"** | Đây là log của Passive Health Check. Nginx đánh dấu upstream là "down" sau khi gặp `max_fails` lỗi liên tiếp. Node sẽ được thử lại sau `fail_timeout` (1s). Nếu thành công, node được đưa trở lại pool. |
| **Auto Recovery không cần config** | Nginx tự động thử lại các upstream đã bị disabled sau mỗi `fail_timeout`. Khi Node A sống lại và response thành công, nó được đưa trở lại pool ngay lập tức. Đây là **Self-Healing** tự động. |
| **Gunicorn Graceful Shutdown** | Khi nhận SIGTERM (docker stop), Gunicorn đợi các request đang xử lý hoàn thành trước khi tắt workers. Điều này giảm thiểu connection errors. Timeout mặc định là 30s (có thể config với `--graceful-timeout`). |
| **Throughput giảm khi 1 node chết** | Hiển nhiên. Hệ thống mất 50% capacity. Trong thực tế, cần **Autoscaling** (K8s HPA) để bù vào node đã mất, nếu không Node B có thể bị quá tải dẫn đến **Cascading Failure**. |

### Kết quả Lab thực tế:
- **Failover time:** 1-2 giây (đúng như config)
- **Errors during failover:** ~14 warnings, nhưng không có 502 errors cho client
- **Recovery time:** ~5 giây (Gunicorn khởi động + Nginx detect)
- **Final state:** Load balancing 50/50 giữa 2 nodes

---
> **Kết luận:** Lab này chứng minh rằng **Availability** không chỉ là code không lỗi, mà là cấu hình Infrastructure (Nginx/K8s) thông minh để xử lý lỗi khi nó chắc chắn xảy ra. Production-grade system phải có khả năng **Self-Healing** và **Fast Failover** để đạt SLA cao (99.9%+).