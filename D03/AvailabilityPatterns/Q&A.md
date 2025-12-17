# Tech Interview: Availability Patterns at Scale

Chào mừng. Tôi sẽ đóng vai Senior Interviewer tại Google để thực hiện buổi Mock Interview này. Mục tiêu không chỉ là check kiến thức, mà là đánh giá **System Thinking** của bạn dưới áp lực.

Chúng ta sẽ đi qua 3 level: **Junior, Mid, và Senior**.

---

## 🟢 Level 1: Junior (Core Concepts)

**Câu hỏi A:**
> "Active-Passive và Active-Active khác nhau cơ bản thế nào về Triết lý thiết kế (Design Philosophy)?"

**Câu hỏi B:**
> "Trong Active-Passive, yếu tố nào quyết định Downtime khi Failover? Trade-off ở đây là gì?"

<details>
<summary><b>💡 Gợi ý trả lời (Click để xem)</b></summary>

1.  **Triết lý cốt lõi:**
    *   **Active-Passive (Master-Slave):** Ưu tiên **Sự đơn giản (Simplicity)** & **Consistency**. Chỉ 1 nơi ghi, dễ quản lý state.
    *   **Active-Active (Master-Master):** Ưu tiên **Utilization** & **Scalability**. Tận dụng 100% tài nguyên phần cứng. Đổi lại là sự phức tạp trong Conflict Resolution.

2.  **Downtime determinant:**
    *   Phụ thuộc vào trạng thái của Passive Node: **Hot** (sẵn sàng ngay) vs **Cold** (phải boot up).
    *   **Trade-off:** Muốn Failover nhanh (Hot Standby) thì tốn tiền nuôi server "ngồi chơi". Muốn tiết kiệm (Cold Standby) thì chấp nhận Downtime lâu hơn.
</details>

---

## 🟡 Level 2: Mid-Level (Troubleshooting & Risk Analysis)

**Tình huống:**
> "Bạn dùng Active-Passive cho Database. Mọi chỉ số (CPU, RAM) đều xanh. Đột nhiên Master sập nguồn. Sau khi Failover sang Slave thành công, Business team hét toáng lên là **mất 10 giây dữ liệu transaction vừa rồi**.
> Tại sao việc này xảy ra dù hệ thống báo 'Healthy'? Bạn dùng Metric nào để bắt được lỗi này trước khi nó nổ ra?"

<details>
<summary><b>💡 Gợi ý trả lời (Click để xem)</b></summary>

1.  **Root Cause Analysis:**
    *   Vấn đề nằm ở cơ chế **Async Replication**. Master đã nhận `ACK` từ Client nhưng *chưa kịp* đẩy log sang Slave thì chết.
    *   Đây là sự vi phạm **RPO (Recovery Point Objective)**. "Healthy" về mặt resource (CPU/RAM) không có nghĩa là "Safe" về mặt Data.

2.  **Observability & Solution:**
    *   **Metric:** Phải monitor **`Replication Lag`** (tính bằng milli-seconds hoặc bytes).
    *   **Fix:** Chuyển sang **Semi-Sync Replication**.
    *   **New Trade-off:** Write Latency sẽ tăng lên (vì phải chờ ít nhất 1 Slave confirm).
</details>

---

## 🔴 Level 3: Senior (Architecture & Strategy)

**Tình huống:**
> "Sếp muốn tăng Availability từ 99.9% (Three 9s) lên 99.99% (Four 9s) cho sự kiện Black Friday. Traffic dự kiến tăng gấp 10 lần.
> Hiện tại kiến trúc gồm 5 services (A->B->C->D->E) gọi nối tiếp nhau. Mỗi service đang đạt 99.9%."

**Câu hỏi:**
1.  Tính Availability hiện tại của chuỗi 5 service này?
2.  Làm thế nào để đạt 99.99% mà không cần viết lại toàn bộ code của 5 service này?

<details>
<summary><b>💡 Gợi ý trả lời (Click để xem)</b></summary>

1.  **The Math of Serial Availability:**
    - Công thức: `A_total = A1 × A2 × ... × An`
    - Tính toán:
      ```
      0.999^5 ≈ 0.995 (99.5%)
      ```
    - **Insight:** Càng microservices nối tiếp, hệ thống càng dễ chết. 99.5% là thảm họa so với mục tiêu 99.99%.

2.  **Strategic Solution (Parallelism):**
    - Không thể bắt mỗi team dev nâng code lên 99.999% ngay lập tức. Cách duy nhất là **Redundancy (Parallelism)**.
    - Triển khai **Read Replicas** hoặc **Caching Layer** song song cho các service chịu tải đọc cao.
    - Công thức song song:
      ```
      A = 1 - (1 - 0.999)^2 ≈ 99.9999%
      ```
    - **Chiến thuật:** Tách Read/Write path. Sharding database để cách ly lỗi (Blast Radius reduction). Active-Active cho các stateless services.
</details>