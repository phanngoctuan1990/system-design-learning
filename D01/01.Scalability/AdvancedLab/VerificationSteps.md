# 🧪 Scalability Advanced Lab Verification Steps

Tài liệu này hướng dẫn verify Lab Scalability Nâng cao, so sánh hiệu quả các thuật toán Load Balance và kiểm thử SPOF.

---

## 🏗️ Phase 1: Preparation (Chuẩn bị)

**1. Kiểm tra cấu hình Nginx:**
Đảm bảo bạn có sẵn 2 file cấu hình cho 2 kịch bản test:
```bash
ls -l nginx_A_round_robin.conf nginx_B_least_conn.conf
```

**2. Khởi tạo môi trường (Round Robin mặc định):**
Kiểm tra file `docker-compose.yml`, đảm bảo đang mount `nginx_A_round_robin.conf`.
```bash
docker compose up --build -d
```

---

## 🧪 Phase 2: Test Scenarios

### 🟢 Scenario 1: Round Robin Loading (Baseline)
**Mục tiêu:** Thiết lập baseline hiệu năng khi phân phối tải đều bất kể trạng thái server.

**Thực thi:**
1.  **Cấu hình:** Đảm bảo sử dụng `nginx_A_round_robin.conf`.
2.  **Bắn tải:**
    ```bash
    bash test_traffic.sh
    ```
3.  **Ghi nhận Metrics:**
    *   Quan sát output của `hey`.
    *   **Insight:** RPS và Latency p95 sẽ có sự chênh lệch nếu một số request ngẫu nhiên bị chậm, do RR vẫn dồn tiếp request vào server đang bận.

### 🔵 Scenario 2: Least Connections (Advanced)
**Mục tiêu:** Chứng minh `least_conn` tối ưu hơn khi hệ thống có các request nặng (slow requests).

**Thực thi:**
1.  **Chuyển Config sang Least Conn:**
    *   Sửa `docker-compose.yml`: đổi volume thành `./nginx_B_least_conn.conf:/etc/nginx/nginx.conf:ro`
    *   Restart Nginx:
        ```bash
        docker compose up -d nginx
        ```
2.  **Giả lập Slow Request (Heavy Job):**
    ```bash
    curl http://localhost/slow &
    ```
3.  **Bắn tải ngay lập tức:**
    ```bash
    bash test_traffic.sh
    ```

**Kết quả Mong Đợi:**
*   **Latency p95 giảm / RPS tăng** so với Scenario 1.
*   **Lý do:** Nginx nhận thấy Clone 1 đang bận xử lý `/slow` (1 connection active), nên sẽ dồn traffic nhanh sang Clone 2.
*   **Insight:** Tránh hiện tượng "Head-of-Line Blocking" ở mức application server.

### 🔴 Scenario 3: Failover Simulation (SPOF Mitigation)
**Mục tiêu:** Chứng minh hệ thống tự động loại bỏ thành phần lỗi (Redundancy).

**Thực thi:**
1.  **Giả lập sự cố:** Kill chết 1 process ứng dụng.
    ```bash
    docker stop app_clone_1
    ```
2.  **Bắn tải:**
    ```bash
    bash test_traffic.sh
    ```
3.  **Quan sát:**
    *   **Availability:** Hệ thống vẫn trả về **200 OK**.
    *   **RPS:** Có thể giảm nhẹ (do mất 50% capacity) nhưng không sập.
    *   **Routing:** Tất cả request dồn về `app_clone_2`.

---

## 🛠️ Troubleshooting Playbook

Khi kết quả không như mong đợi, hãy kiểm tra theo quy trình sau:

| Priority | Component | Command | Rationale |
| :--- | :--- | :--- | :--- |
| **P1** | **Container Status** | `docker compose ps` | Đảm bảo Redis, Nginx, App Clones đều UP. |
| **P2** | **App Logs** | `docker compose logs app_clone_1` | Kiểm tra xem App có kết nối được Redis không. |
| **P3** | **Network** | `curl http://localhost/` | Test kết nối cơ bản tới Nginx. |
| **P4** | **Nginx Config** | `docker compose exec nginx nginx -T` | Xem cấu hình thực tế đang chạy có đúng file mount không. |
| **P5** | **Redis State** | `docker compose exec redis redis-cli MONITOR` | (Optional) Xem real-time các lệnh gửi vào Redis. |
| **P6** | **Statelessness/State Access** | `docker exec -it redis_session_cache redis-cli INFO persistence` | (Optional) Nếu session không hoạt động, đảm bảo Redis đang hoạt động và không gặp sự cố về Eviction/Memory. |

---

## 🧹 Cleanup

```bash
docker compose down -v
rm -f /tmp/scalability_test_cookie.txt
```
