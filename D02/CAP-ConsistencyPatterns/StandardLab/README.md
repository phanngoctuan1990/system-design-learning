# Hands-on Lab: CAP & Consistency Trade-offs

## 1. Goal: Quan sát Hành vi CP vs. AP

Mục tiêu của bài lab này giúp bạn tận mắt chứng kiến sự khác biệt giữa hai mô hình consistency:

1.  **Thiết lập môi trường:** Dựng hệ thống phân tán giả lập với 2 node database.
2.  **Trạng thái bình thường:** Thực hiện thao tác Ghi (Write) khi mạng ổn định (Strong Consistency/High Availability).
3.  **Kích hoạt Partition (P):** Giả lập sự cố ngắt kết nối một node (Network Partition).
4.  **Quan sát hành vi:** Gửi request Ghi (Write) vào cả hai hệ thống CP và AP trong lúc đang bị Partition:
    *   **Hệ thống CP:** Phải trả về lỗi (Sacrifice **A**vailability).
    *   **Hệ thống AP:** Phải trả về thành công (Sacrifice **C**onsistency – chấp nhận Stale Data).

## 2. Architecture & Components

Dưới đây là các thành phần của hệ thống giả lập:

| Component | Role | Logic |
| :--- | :--- | :--- |
| **db_g1 (Redis)** | Node 1 (Primary Write) | Chứa dữ liệu chính, đóng vai trò là node nhận write trực tiếp. |
| **db_g2 (Redis)** | Node 2 (Replica) | Node sẽ bị ngắt kết nối (Partition) để mô phỏng sự cố mạng. |
| **app_cp (Flask/Python)** | CP Service Endpoint | Yêu cầu đồng bộ (**synchronous**) ghi thành công lên cả G1 & G2. <br>Nếu G2 lỗi (do Partition), toàn bộ transaction bị hủy, trả về lỗi **503 Service Unavailable** (Hy sinh Availability). |
| **app_ap (Flask/Python)** | AP Service Endpoint | Chỉ yêu cầu ghi cục bộ (**local write**) thành công lên G1. <br>Trả về **200 OK** ngay lập tức, bất chấp G2 có sống hay chết (Hy sinh Consistency / Chấp nhận Eventual Consistency). |

## 3. Verification Steps (Playbook Thực Thi)

### Bước 1: Setup Môi trường & Baseline Check

**Chạy Docker Compose:**
```bash
docker-compose up --build -d
```

**Lệnh 1.1: Kiểm tra trạng thái ban đầu (Baseline Read)**
Kiểm tra cả hai hệ thống đọc dữ liệu đồng nhất (Consistent) trước khi có Partition.

```bash
# Read từ CP (Port 5002)
curl http://localhost:5002/read/STATUS

# Read từ AP (Port 5001)
curl http://localhost:5001/read/STATUS
```

*   **Kỳ vọng:** Cả hai đều trả về `READY_V0` và `Consistency_Status: "STRONG/EVENTUAL CONSISTENT"`.

### Bước 2: Kích hoạt Partition (P)

Chúng ta mô phỏng sự cố mạng làm Node G2 bị cô lập/mất kết nối (Partition). Trong Docker, cách đơn giản nhất là dừng container `db_g2` (simulating Node Failure, which is indistinguishable from Partition in an asynchronous network).

```bash
docker stop db_g2
```
*   **Signal:** Node G2 hiện tại không thể truy cập được.

### Bước 3: Kiểm tra hành vi CP (Sacrifice Availability)

Thực hiện thao tác Ghi (Write) lên hệ thống CP (`app_cp`).

```bash
# Write key: TRANSACTION, value: CP_WRITE_1 (qua port 5002)
curl -X POST http://localhost:5002/write/TRANSACTION/CP_WRITE_1
```

*   **Kỳ vọng:** Do `app_cp` yêu cầu ghi đồng bộ lên cả G1 và G2, và G2 đã dừng, hệ thống phải trả về lỗi **503 Service Unavailable**.
*   **Xác minh:** Kiểm tra dữ liệu trên G1 (Node Primary).

```bash
docker exec db_g1 redis-cli GET TRANSACTION
```
*   **Kỳ vọng:** Trả về `(nil)` hoặc `READY_V0`. Dữ liệu ghi không được commit (Atomic Transaction).

### Bước 4: Kiểm tra hành vi AP (Sacrifice Consistency)

Thực hiện thao tác Ghi (Write) lên hệ thống AP (`app_ap`).

```bash
# Write key: ORDER, value: AP_WRITE_1 (qua port 5001)
curl -X POST http://localhost:5001/write/ORDER/AP_WRITE_1
```

*   **Kỳ vọng:** Hệ thống AP phải trả về **200 OK** ngay lập tức (High Availability).

**Xác minh Consistency Trade-off (Stale Data):**

1.  **Kiểm tra G1 (Write Local Success):**
    *   **Kết quả:** Trả về `AP_WRITE_1`. (Write thành công tại node Primary).
2.  **Kiểm tra G2 (Partitioned/Stale Data):** Chúng ta không thể kiểm tra G2 vì nó đã dừng. Thay vào đó, chúng ta đọc lại qua `app_ap` endpoint để xem trạng thái inconsistency.

```bash
curl http://localhost:5001/read/ORDER
```
*   **Kỳ vọng:** `G1_Value` là `AP_WRITE_1`, `G2_Value` là `N/A` (hoặc giá trị cũ nếu G2 chạy lại). `Consistency_Status`: Sẽ không phải là CONSISTENT.

### Bước 5: Giải quyết Partition (Heal Partition)

Khởi động lại Node G2 để mô phỏng Partition đã được giải quyết.

```bash
docker start db_g2
```

**Kiểm tra Eventual Consistency:**
Sau khi G2 khởi động, G1 và G2 cần thời gian để đồng bộ (nếu có cơ chế replication).

```bash
# Đợi vài giây, sau đó đọc lại qua AP
curl http://localhost:5001/read/ORDER
```
*   **Kỳ vọng:** Nếu `app_ap` hoặc Redis có cơ chế tự động đồng bộ sau khi G2 kết nối lại, `G1_Value` và `G2_Value` sẽ khớp nhau, và trạng thái trở lại **CONSISTENT**.

## 4. What this proves (Tóm tắt Chiến lược)

Lab này chứng minh trực quan **CAP Impossibility Theorem**:

1.  **CP (Consistency/P. Tolerance):** Khi `db_g2` bị Partition, thao tác ghi lên `app_cp` phải trả về lỗi (**503**).
    *   **Trade-off:** Chúng ta bảo vệ được tính toàn vẹn dữ liệu (transaction là Atomic), nhưng phải trả giá bằng Availability. Đây là lựa chọn bắt buộc cho các nghiệp vụ yêu cầu tính toàn vẹn tuyệt đối (ví dụ: giao dịch tài chính, kiểm kho).

2.  **AP (Availability/P. Tolerance):** Khi `db_g2` bị Partition, thao tác ghi lên `app_ap` vẫn thành công (**200 OK**).
    *   **Trade-off:** Chúng ta đảm bảo được Availability (mọi yêu cầu đều nhận được phản hồi hợp lý), nhưng phải chấp nhận rằng dữ liệu trên `db_g2` sẽ Stale (cũ). Hệ thống rơi vào trạng thái Eventual Consistency, phù hợp cho các nghiệp vụ chịu lỗi như giỏ hàng hoặc email.

> **Insight Chiến lược:** Việc lựa chọn CP hay AP không phải là ngẫu nhiên, mà là một sự đánh đổi (trade-off) được cài đặt cứng vào logic ứng dụng và giao thức cơ sở dữ liệu để quản lý rủi ro khi mạng gặp sự cố.