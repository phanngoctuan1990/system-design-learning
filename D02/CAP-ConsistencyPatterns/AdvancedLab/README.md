# Lab Nâng cao: CAP & Consistency Patterns (Advanced Benchmark)

Đây là Lab nâng cao về CAP & Consistency Patterns, được thiết kế dưới dạng **Test Case Matrix** để bạn có thể đo lường trực tiếp các trade-off về hiệu năng và độ tin cậy trong môi trường hệ thống phân tán mô phỏng.

Chúng ta sẽ sử dụng `app_cp` (CP - Strong Consistency) và `app_ap` (AP - Eventual Consistency), kết hợp với công cụ `hey` để tạo tải và đo lường.

## I. Architecture & Test Matrix Overview (ADR V2.1)

Hệ thống bao gồm hai Database Nodes (Redis G1 & G2) và hai Application Server (CP Mode và AP Mode).

| Case | Cấu hình Consistency | Mục tiêu (Trade-off) | Đo lường |
|---|---|---|---|
| **A** | **CP Baseline**<br>(Synchronous Write G1 & G2) | Đảm bảo **C** (Consistency). Dự kiến Latency cao và Throughput thấp. | Benchmark (Load Test) |
| **B** | **AP Advanced**<br>(Local Write G1 only, Async G2 effort) | Đảm bảo **A** (Availability/Performance). Dự kiến Latency thấp và Throughput cao. | Benchmark (Load Test) |
| **C** | **P Simulation**<br>(Partition: G2 Down) | Quan sát hành vi Failover/Circuit Breaker.<br>• **CP:** Phải trả về lỗi (Sacrifice A).<br>• **AP:** Phải thành công (Sacrifice C/Stale Data). | Logs & Read Verification |

## II. File Configuration

Sử dụng cấu trúc thư mục sau:

```
.
├── docker-compose.yml
├── requirements.txt
└── app.py
```

## III. Hands-on Execution & Benchmarking Playbook

### Bước 1: Khởi động và Baseline Check

Build và khởi động các container:
```bash
docker-compose up --build -d
```

Kiểm tra trạng thái hệ thống ban đầu:
```bash
curl http://localhost:5002/read/TEST_KEY
```
*   **Kỳ vọng:** `G1_Value` và `G2_Value` là `N/A`.

### Bước 2: Benchmark Case A (CP Baseline)

Chúng ta đo lường hiệu năng của hệ thống Strong Consistency (CP) khi nó phải chờ commit từ cả hai node (G1 và G2).
*(Yêu cầu: Bạn cần cài đặt công cụ `hey` hoặc `ab` trên máy local. Ở đây sử dụng `hey`.)*

Sử dụng `hey` để bắn tải 1000 requests (50 concurrent) vào endpoint CP (Port 5002):

```bash
# Bắn tải 1000 requests, 50 concurrency vào CP mode (5002)
hey -n 1000 -c 50 -m POST http://localhost:5002/write/USER_1/CP_TEST_A
```

### Bước 3: Benchmark Case B (AP Advanced)

Chúng ta đo lường hiệu năng của hệ thống Eventual Consistency (AP) khi nó chỉ cần commit cục bộ lên G1 và không chờ G2.

```bash
# Bắn tải tương tự vào AP mode (5001)
hey -n 1000 -c 50 -m POST http://localhost:5001/write/USER_2/AP_TEST_B
```

## IV. Phân tích Metrics (So sánh A vs. B)

Sau khi chạy hai benchmark, hãy so sánh các metrics sau:

| Metric | CP Baseline (A) | AP Advanced (B) | Kết quả chứng minh |
|---|---|---|---|
| **Requests/sec**<br>(Throughput) | **Thấp hơn** | **Cao hơn** | AP tối ưu hóa Throughput bằng cách hy sinh tính đồng bộ hóa (không chờ round-trip thứ 2). |
| **Latency**<br>(p95, p99) | **Cao hơn** | **Thấp hơn đáng kể** | CP trả giá bằng Latency do yêu cầu giao dịch phải serialized (tuần tự hóa) qua cả G1 và G2. |
| **Success/Error Count** | 100% Success | 100% Success | Cả hai đều Available khi không có Partition (Mạng ổn định). |

## V. Mô phỏng Lỗi Mạng (Case C: Failure/Partition Tolerance)

Mô phỏng sự cố mạng làm Node G2 bị cô lập (Partition).

```bash
docker stop db_g2
```

### 5.1. Thử nghiệm Write lên CP (Fail Fast / Sacrifice A)
Ghi dữ liệu mới lên CP:
```bash
curl -X POST http://localhost:5002/write/CRITICAL_DATA/V1
```
*   **Kỳ vọng:** Phải trả về lỗi **503 Service Unavailable**.
*   **Chứng minh:** Hệ thống CP đã chọn Consistency (không chấp nhận ghi nếu không thể đồng bộ hóa) và hy sinh Availability khi xảy ra Partition.

### 5.2. Thử nghiệm Write lên AP (High Availability / Sacrifice C)
Ghi dữ liệu mới lên AP:
```bash
curl -X POST http://localhost:5001/write/TEMP_DATA/V_AP_SUCCESS
```
*   **Kỳ vọng:** Phải trả về **200 OK**. Message sẽ báo `G2 Unreachable/Stale`.
*   **Chứng minh:** Hệ thống AP đã chọn Availability và chấp nhận rằng `TEMP_DATA` = `V_AP_SUCCESS` sẽ không tồn tại trên G2 (dữ liệu Stale) cho đến khi Partition được giải quyết (Eventual Consistency).

### 5.3. Xác minh Inconsistency (Stale Data)
Khôi phục Node G2 (Heal Partition) và đọc lại.

```bash
docker start db_g2
sleep 3 # Đợi G2 khởi động lại

# Đọc dữ liệu từ AP
curl http://localhost:5001/read/TEMP_DATA
```
*   **Kỳ vọng:** `G1_Value` là `V_AP_SUCCESS`, `G2_Value` có thể là giá trị cũ (`N/A` hoặc `READY_V0`).
*   **Status:** `Consistency_Status` sẽ là **INCONSISTENT/STALE** (cho đến khi cơ chế đồng bộ hóa ngầm giải quyết xung đột).

## VI. Troubleshooting Playbook

Việc vận hành hệ thống phân tán trên máy local dễ gặp phải các vấn đề liên quan đến mạng nội bộ Docker hoặc lỗi ứng dụng chưa xử lý (Fallacies of Distributed Computing).

| Signal/Symptom | Root Cause (Fallacy) | Mitigation (Hành động vận hành) | Checklist để thực hành |
|---|---|---|---|
| **Docker container không up** | Lỗi trong `Dockerfile` hoặc `requirements.txt`. Cổng bị chiếm dụng (e.g., 5002, 5001 đã dùng). | Kiểm tra `docker logs` chi tiết để tìm lỗi Python/Flask. Đảm bảo cổng local không bị chiếm. | `docker-compose logs <service_name>` |
| **API trả về 503 ngay lập tức** | Ứng dụng không thể kết nối tới DB (DNS Resolution Failed) hoặc DB chưa sẵn sàng. | **DNS check:** Đảm bảo `DB_G1_HOST` và `DB_G2_HOST` (tên service) trong `app.py` khớp với `docker-compose.yml`. | `docker exec <app_cp_id> ping db_g1` |
| **hey trả về connection refused** | Flask app chưa thực sự lắng nghe trên port 5002/5001 hoặc Docker không map port đúng. | Kiểm tra ports mapping trong `docker-compose.yml` (e.g., "5002:5002"). Đảm bảo `app.run(host='0.0.0.0')`. | `docker ps` để kiểm tra port. |
| **CP Write luôn trả về Timeout/Error** | Timeout quá ngắn (0.1s) hoặc độ trễ mạng Docker quá cao (Simulation is too aggressive). | Tăng `TIMEOUT` trong `app.py` lên 0.5 giây để nới lỏng giới hạn A. Đảm bảo G1 và G2 đều đang chạy. | `docker exec db_g1 redis-cli ping` |
| **AP Write trả về 503 khi G2 Down** | Lỗi logic AP: Đã cố gắng chờ G2 thay vì ghi cục bộ G1. | Kiểm tra lại `ap_write` trong `app.py`. AP chỉ được trả về lỗi khi G1 (Primary) gặp sự cố nghiêm trọng, không phải G2. | Review code `ap_write` logic. |
