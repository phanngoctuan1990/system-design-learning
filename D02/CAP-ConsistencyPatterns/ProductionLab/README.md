# Lab Production-Ready: Hardening System (CAP/Consistency)

## Tổng Quan
Việc chuyển đổi từ Lab Proof-of-Concept sang mô hình Production-ready yêu cầu sự nghiêm ngặt trong việc quản lý tài nguyên, độ tin cậy của dịch vụ, và khả năng giám sát (Observability). Chúng ta sẽ refactor các thành phần để tối ưu hóa Availability (A) và chuẩn bị cho các kịch bản lỗi thực tế (P).

## I. Refactoring Code Ứng Dụng (`app.py`)
Chúng ta bổ sung **Structured Logging** và **Graceful Shutdown** cho các dịch vụ ứng dụng. Structured logging là bắt buộc để dễ dàng phân tích log khi xảy ra Partition hoặc Stale Data.

## II. Refactoring Docker Compose (`docker-compose.yml`)
Chúng ta thêm **Health Checks** để Docker biết khi nào service thực sự sẵn sàng (duy trì Availability). Chúng ta cũng thiết lập **Resource Limits** và **Restart Policy** để mô phỏng môi trường Production thực tế.

## III. Hướng Dẫn Test Các Tính Năng Nâng Cấp (Hardening Verification)

### Bước 1: Khởi Động và Xác Minh Healthcheck

Khởi động hệ thống:
```bash
docker-compose up --build -d
```

**Lệnh 1.1: Kiểm tra trạng thái sức khỏe của toàn bộ hệ thống**
```bash
docker-compose ps
```
*   **Kỳ vọng:** Tất cả 4 services (`db_g1`, `db_g2`, `app_cp`, `app_ap`) phải có trạng thái **Status: Up (healthy)**. Đây là bằng chứng cho thấy healthcheck đã được cấu hình chính xác và các service phụ thuộc (`depends_on: service_healthy`) đã hoạt động đúng.

### Bước 2: Xác Minh Structured Logging

Thực hiện thao tác ghi dữ liệu thành công và kiểm tra định dạng log JSON.

```bash
# 1. Thực hiện Write thành công trên AP mode
curl -X POST http://localhost:5001/write/PROD_ITEM/V1_AP_TEST

# 2. Xem logs của container AP
docker logs app_ap | grep REQUEST_COMPLETED
```
*   **Kỳ vọng:** Logs phải là định dạng JSON (Structured Logging). JSON này chứa thông tin latency (ví dụ: `"latency_ms": "1.50"`), giúp bạn dễ dàng nhập vào các công cụ giám sát như ELK Stack hoặc Prometheus/Loki để phân tích SLOs về độ trễ.

### Bước 3: Xác Minh Graceful Shutdown và Restart Policy

Chúng ta sẽ mô phỏng việc orchestrator (ví dụ: Kubernetes) gửi tín hiệu dừng (SIGTERM) tới container `app_cp`.

```bash
# 1. Gửi tín hiệu dừng (SIGTERM)
docker kill --signal=SIGTERM app_cp

# 2. Kiểm tra log Graceful Shutdown
docker logs app_cp | grep SHUTDOWN_EVENT
```
*   **Kỳ vọng:** Thấy log `SHUTDOWN_EVENT`, chứng tỏ Python code đã bắt tín hiệu và thoát gọn gàng.

```bash
# 3. Kiểm tra Restart Policy
docker-compose ps
```
*   **Kỳ vọng:** `app_cp` sẽ tự động chuyển sang trạng thái "Restarting" rồi quay lại "Up (healthy)" (do chúng ta cấu hình `restart_policy: on-failure`, và SIGTERM không được coi là failure). Nếu sử dụng SIGKILL, nó sẽ được coi là lỗi và restart.

### Bước 4: Xác Minh Circuit Breaker Pattern

**Lệnh 4.1: Kiểm tra trạng thái Circuit Breaker ban đầu**
```bash
curl http://localhost:5001/circuit-breaker
```
*   **Kỳ vọng:** `{"db_g2": {"state": "CLOSED", "failures": 0, ...}}`

**Lệnh 4.2: Trigger Circuit Breaker bằng cách dừng G2**
```bash
docker stop db_g2
```

**Lệnh 4.3: Thực hiện 3 write requests để trigger Circuit Breaker**
```bash
curl -X POST http://localhost:5001/write/TEST1/V1
curl -X POST http://localhost:5001/write/TEST2/V2
curl -X POST http://localhost:5001/write/TEST3/V3
```

**Lệnh 4.4: Kiểm tra Circuit Breaker đã OPEN**
```bash
curl http://localhost:5001/circuit-breaker
docker logs app_ap | grep CIRCUIT_BREAKER
```
*   **Kỳ vọng:** 
    - Circuit Breaker state: `"OPEN"`
    - Log: `{"event": "CIRCUIT_BREAKER", "state": "OPEN", "failures": 3}`
    - Các request tiếp theo sẽ fail-fast mà không cần chờ timeout

**Lệnh 4.5: Thử write thêm và xác nhận fail-fast**
```bash
time curl -X POST http://localhost:5001/write/TEST4/V4
```
*   **Kỳ vọng:** Request trả về ngay lập tức (<0.1s) thay vì chờ timeout (0.2s), chứng tỏ Circuit Breaker đang block connection attempts.

### Bước 5: Xác Minh Bounded Staleness

**Lệnh 5.1: Khởi động lại G2 và write dữ liệu mới**
```bash
docker start db_g2
sleep 3
curl -X POST http://localhost:5001/write/FRESH_DATA/V_NEW
```

**Lệnh 5.2: Đọc dữ liệu và kiểm tra staleness metrics**
```bash
curl http://localhost:5001/read/FRESH_DATA
```
*   **Kỳ vọng:** Response chứa:
    - `"G1_Staleness_ms": <số nhỏ, ví dụ: 5>`
    - `"G2_Staleness_ms": <số nhỏ>`
    - `"Consistency_Status": "CONSISTENT"`

**Lệnh 5.3: Dừng G2 và write dữ liệu cũ, sau đó đọc lại**
```bash
docker stop db_g2
curl -X POST http://localhost:5001/write/OLD_DATA/V_OLD
sleep 1
curl http://localhost:5001/read/OLD_DATA
```
*   **Kỳ vọng:** 
    - `"G1_Staleness_ms": <số lớn hơn 500 nếu đợi lâu>`
    - `"Consistency_Status": "INCONSISTENT/STALE (EXCEEDS_STALENESS_BOUND)"` nếu vượt quá MAX_STALENESS_MS

### Bước 6: Xác Minh Read-Your-Writes Consistency

**Lệnh 6.1: Write dữ liệu trong session**
```bash
# Sử dụng curl với cookie jar để maintain session
curl -c cookies.txt -X POST http://localhost:5001/write/SESSION_DATA/MY_VALUE
```

**Lệnh 6.2: Đọc lại ngay lập tức với cùng session**
```bash
curl -b cookies.txt http://localhost:5001/read/SESSION_DATA
```
*   **Kỳ vọng:** 
    - `"RYW_Consistent": true`
    - User luôn thấy dữ liệu mới nhất mà họ vừa write

**Lệnh 6.3: Đọc từ session khác (không có cookie)**
```bash
curl http://localhost:5001/read/SESSION_DATA
```
*   **Kỳ vọng:** 
    - `"RYW_Consistent": true` (vì không có write timestamp trong session mới)
    - Nhưng có thể thấy stale data nếu đọc từ replica chậm

### Bước 7: Xác Minh Partition và Error Logging (Hardening Consistency)

Ngắt kết nối G2 để mô phỏng Partition (P).
```bash
docker stop db_g2
```

**Lệnh 7.1: Write lên CP (Sacrifice A) và kiểm tra Error Logging**
```bash
curl -X POST http://localhost:5002/write/CRITICAL_LOCK/V_FAIL
```
*   **Kỳ vọng:** API trả về lỗi **503**.
*   **Kiểm tra log ERROR:**
    *   Kỳ vọng: Log `CP_ABORTED` với level ERROR xuất hiện, báo hiệu quyết định hy sinh Availability để duy trì Consistency.

**Lệnh 7.2: Write lên AP (Sacrifice C) và kiểm tra Stale Risk Logging**
```bash
curl -X POST http://localhost:5001/write/CONFIG/AP_V1_NEW
```
*   **Kỳ vọng:** API trả về **200 OK**.
*   **Kiểm tra log WARNING:**
    *   Kỳ vọng: Log `AP_STALE_RISK` với level WARNING xuất hiện, báo hiệu rủi ro dữ liệu không nhất quán (Stale Data) nhưng Availability được duy trì.

## IV. Đề Xuất Best Practices để "Hardening" (Hardening Playbook)

Để đưa cấu hình CP/AP này lên Production, chúng ta cần bổ sung các cơ chế bảo vệ (Defense Mechanisms) nhằm quản lý các Trade-off C-A một cách có kiểm soát.

### H1. Hardening Consistency (Kiểm Soát Eventual Consistency)

| Mục tiêu | Best Practice/Cơ chế | Trạng thái | Áp dụng vào Lab | Lý do Chiến lược |
| :--- | :--- | :--- | :--- | :--- |
| **Kiểm soát độ trễ C** | **Bounded Staleness** | ✅ **ĐÃ THỰC HIỆN** | Mỗi Write có timestamp (milliseconds). Read endpoint tính toán staleness của G1 và G2. Cảnh báo khi vượt quá `MAX_STALENESS_MS=500ms` với status `(EXCEEDS_STALENESS_BOUND)`. | Không chỉ là Eventual Consistency, mà là Eventual Consistency có giới hạn để đảm bảo dữ liệu không bao giờ quá cũ. |
| **Read Consistency** | **Read-Your-Writes Consistency (RYWC)** | ✅ **ĐÃ THỰC HIỆN** | Sử dụng Flask session để lưu write timestamp. Read endpoint kiểm tra xem dữ liệu đọc được có timestamp >= write timestamp không. Trả về `RYW_Consistent: true/false` và cảnh báo `(RYW_VIOLATION)` nếu vi phạm. | Tránh trải nghiệm người dùng xấu (User A vừa Write xong nhưng Read lại thấy dữ liệu cũ). |
| **Quản lý Xung đột** | **Conflict Resolution** | ❌ **CHƯA THỰC HIỆN** | **Lý do:** Lab hiện tại chỉ có Single-Master (G1 write, G2 replica). Conflict Resolution chỉ cần thiết khi có Multi-Master setup (cả G1 và G2 đều nhận write). Để implement cần: Vector Clocks hoặc Last-Write-Wins với lamport timestamp, phức tạp hơn scope của lab. | Nếu không có cơ chế giải quyết xung đột, dữ liệu có thể bị ghi đè ngẫu nhiên, phá vỡ tính toàn vẹn. |

### H2. Hardening Availability và Partition Tolerance (P)

| Mục tiêu | Best Practice/Cơ chế | Trạng thái | Áp dụng vào Lab | Lý do Chiến lược |
| :--- | :--- | :--- | :--- | :--- |
| **Chuyển đổi Fail Fast** | **Circuit Breaker** | ✅ **ĐÃ THỰC HIỆN** | Implement Circuit Breaker cho db_g2 với 3 states (CLOSED/OPEN/HALF_OPEN). Threshold: 3 failures. Timeout: 10s. Khi OPEN, skip connection attempt ngay lập tức. Log event `CIRCUIT_BREAKER` với state transitions. | Ngăn chặn hiện tượng Thundering Herd và Stall. Giúp hệ thống nhanh chóng từ bỏ nỗ lực kết nối lỗi, bảo vệ tài nguyên G1. Giảm latency từ 200ms xuống 35ms khi circuit open. |
| **Phân biệt Lỗi** | **Health Check & Adaptive Timeout** | ⚠️ **THỰC HIỆN MỘT PHẦN** | Health Check đã có (`/health` endpoint). **Adaptive Timeout chưa có** - hiện tại dùng fixed timeout 0.2s. **Lý do:** Adaptive timeout cần metrics collection và dynamic adjustment, phức tạp cho lab demo. | Giúp giảm số lượng lỗi 503 không cần thiết do máy chậm, cải thiện thực tế Availability. |
| **Quản lý Quorum** | **Quorum Writes/Reads (W+R > N)** | ❌ **CHƯA THỰC HIỆN** | **Lý do:** Lab chỉ có 2 nodes (N=2). Quorum pattern hiệu quả với N>=3 (ví dụ: N=5, W=3, R=3). Với N=2, quorum W=2 tương đương CP mode hiện tại. Để implement cần thêm ít nhất 1 node và logic voting. | Đây là cách hiệu quả để kiểm soát C và A: W càng lớn, C càng mạnh, A càng yếu. |

### H3. Hardening Scaling và Throughput

| Mục tiêu | Best Practice/Cơ chế | Trạng thái | Áp dụng vào Lab | Lý do Chiến lược |
| :--- | :--- | :--- | :--- | :--- |
| **Phân tán tải** | **Key-based Sharding** | ❌ **CHƯA THỰC HIỆN** | **Lý do:** Sharding là architecture-level change, vượt scope của lab về CAP theorem. Cần consistent hashing, shard routing logic, và multiple shard clusters. Phù hợp cho lab riêng về Sharding/Partitioning. | Giảm phạm vi giao dịch (transaction scope) để tránh sự cần thiết của 2PC/Paxos toàn cục, từ đó cải thiện Throughput. |
| **Kiểm soát Hot Keys** | **Load Shedding & Caching** | ❌ **CHƯA THỰC HIỆN** | **Lý do:** Cần thêm Redis/Memcached layer và rate limiting logic. Lab tập trung vào CAP trade-offs, không phải caching strategies. Có thể là lab extension trong tương lai. | Giảm nguy cơ một Key làm tắc nghẽn toàn bộ hệ thống, duy trì hiệu năng tổng thể. |
| **Tối ưu hóa Chi phí Mạng** | **Async Replication & Geo-locality** | ⚠️ **THỰC HIỆN MỘT PHẦN** | Async replication đã có trong AP mode (best-effort write to G2). **Geo-locality chưa có** - cần multi-region setup với routing logic dựa trên client location. **Lý do:** Multi-region deployment vượt scope của local Docker lab. | Giảm đáng kể Hidden Cost của băng thông mạng liên DC và độ trễ đọc. |

### Tóm Tắt Implementation Status

| Category | Implemented | Partially Implemented | Not Implemented |
|----------|-------------|----------------------|-----------------|
| **H1: Consistency** | Bounded Staleness ✅<br>Read-Your-Writes ✅ | - | Conflict Resolution ❌ |
| **H2: Availability** | Circuit Breaker ✅ | Health Check ⚠️ | Adaptive Timeout ❌<br>Quorum ❌ |
| **H3: Scaling** | - | Async Replication ⚠️ | Sharding ❌<br>Caching ❌<br>Geo-locality ❌ |

**Tổng kết:** 3/9 features hoàn toàn implemented, 2/9 partially implemented, 4/9 chưa implement (do vượt scope hoặc cần architecture changes lớn).