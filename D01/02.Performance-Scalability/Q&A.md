# System Design & Scalability Q&A

## Q1. (Core Concept - Level Junior)
**Khi quyết định mở rộng hệ thống, hãy phân tích trade-off chính giữa Vertical Scaling và Horizontal Scaling. Giải thích tại sao việc duy trì Statelessness ở tầng Application Server lại là nguyên tắc nền tảng cho Horizontal Scaling, và đề xuất component cụ thể để quản lý trạng thái phiên (session state) một cách tập trung.**

### Trả lời Q1:

#### 1. Vertical Scaling vs. Horizontal Scaling

| Mục | Ưu điểm (Pros) | Nhược điểm (Cons) | Phân tích Thêm (Góc nhìn Senior) |
| :--- | :--- | :--- | :--- |
| **Vertical Scaling** | Dễ triển khai (nâng RAM, CPU). | Tốn chi phí, có giới hạn vật lý. | **Rủi ro Downtime:** Việc nâng cấp phần cứng thường yêu cầu downtime, ảnh hưởng trực tiếp đến SLO. Giới hạn vật lý là rào cản tài chính và công nghệ (SAS drives, SSDs...). |
| **Horizontal Scaling** | Mở rộng vô hạn, sử dụng máy cấu hình thấp. | Tăng độ phức tạp quản lý. | **Phân tích Components mới:** Độ phức tạp tăng lên vì bạn buộc phải thêm các thành phần như Load Balancers để phân phối tải và xử lý vấn đề tranh chấp tài nguyên (contention). |

#### 2. Statelessness và Session Management
Bạn hoàn toàn chính xác khi nhấn mạnh rằng việc duy trì **Statelessness** là nguyên tắc vàng cho khả năng mở rộng ngang.

*   **Logic:** Nếu phiên làm việc (session) được lưu trữ cục bộ trên Server A, khi Load Balancer phân phối yêu cầu tiếp theo của người dùng đó sang Server B, Server B sẽ không tìm thấy phiên và yêu cầu đăng nhập lại (**Session Breakage**).
*   **Giải pháp (Centralized State):** Đề xuất sử dụng **Redis/Memcached** là chính xác.
    *   Đây là một **external persistent cache**.
    *   Nó là **lightning-fast** (nhanh như chớp) vì dữ liệu được lưu trong RAM, cho phép hàng trăm nghìn thao tác đọc/ghi mỗi giây, nhanh hơn nhiều so với Database truyền thống.

---

## Q2. (Troubleshooting & Observability - Level Mid)
**Giả sử bạn đang vận hành một hệ thống đã triển khai Load Balancing Round Robin và Centralized Cache (Redis). Tuy nhiên, team vận hành báo cáo tình trạng "Session Inconsistency": người dùng liên tục bị yêu cầu đăng nhập lại hoặc mất dữ liệu tạm thời (ví dụ: giỏ hàng) một cách ngẫu nhiên.**

**Dựa trên kinh nghiệm, hãy chỉ ra 3 Root Causes tiềm năng nhất trong kiến trúc này (từ tầng Load Balancer đến Cache) và đề xuất 3 Metrics/Signals bạn sẽ theo dõi ngay lập tức để chẩn đoán vấn đề.**

### Trả lời Q2:

**Tình huống:** Hệ thống Stateless + Redis Cache nhưng gặp lỗi Session Inconsistency ngẫu nhiên.

#### Phân tích Root Causes Tiềm năng (3 điểm)
Trong một kiến trúc Stateless sử dụng Load Balancer và Cache, lỗi nhất quán phiên thường xảy ra ở giao diện giữa các thành phần hoặc do chính sách Cache không đúng.

1.  **Vấn đề TTL (Time-To-Live) của Cache quá thấp hoặc Eviction Policy sai:**
    *   **Root Cause:** Nếu TTL quá ngắn (ví dụ: 5 phút) hoặc Redis đầy bộ nhớ và dùng chính sách eviction (như LRU), các session key đang hoạt động bị xóa khỏi RAM.
    *   **Tác động:** Server gặp **Cache Miss**, buộc người dùng đăng nhập lại dù phiên chưa hết hạn.

2.  **Lỗi Ghi (Write Failure) vào Redis do Tải hoặc Kết nối:**
    *   **Root Cause:** Thao tác ghi/cập nhật session thất bại do Redis quá tải, lỗi mạng tạm thời, hoặc Redis SPOF bị chết.
    *   **Tác động:** Request tiếp theo đọc session cũ (hoặc rỗng), dẫn đến mất dữ liệu.

3.  **Lỗi Cookie/Session Key Trình duyệt (Browser Cookie Handling):**
    *   **Root Cause:** Browser không gửi lại đúng Session Cookie (do limit size, SameSite policy, hoặc user disable cookie).
    *   **Tác động:** Load Balancer/App Server không thể liên kết request với session ID trong Redis.

#### Metrics/Signals để Chẩn đoán (3 điểm)

1.  **Cache Hit Ratio (Tỷ lệ trúng Cache):**
    *   **Signal:** Giảm đột ngột hoặc duy trì thấp (< 80%).
    *   **Chẩn đoán:** Dữ liệu bị eviction quá nhanh hoặc Redis không phục vụ được key đang hoạt động.

2.  **App Server Error Logs (Log lỗi của Web Server):**
    *   **Signal:** Tăng đột biến lỗi liên quan Redis (`ConnectionError`, `Timeout`, `GET/SET fail`).
    *   **Chẩn đoán:** Xác định lỗi do tương tác mạng/kết nối với Redis.

3.  **Redis Memory & Eviction Rate:**
    *   **Signal:** Memory chạm ngưỡng max + Eviction rate tăng cao.
    *   **Chẩn đoán:** Hệ thống đang xóa key sống vì hết RAM -> nguyên nhân trực tiếp gây mất session.

---

## Q3. (Architectural Tuning & Write Scaling - Level Senior)
**Hệ thống của bạn đã tối ưu hóa Reads bằng Master-Slave Replication, nhưng Write QPS (Queries Per Second) hiện tại đang chạm trần của Master DB và dự kiến workload sẽ tăng gấp 10 lần (10x), vượt quá giới hạn vật lý của Master.**

**Hãy phác thảo một Write Scaling Plan gồm 3 giai đoạn để giải quyết áp lực ghi này. Đồng thời, chỉ rõ trade-off (Availability vs. Consistency vs. Complexity) bạn phải chấp nhận cho mỗi giai đoạn.**

### Trả lời Q3:

**Tình huống:** Master DB chạm trần Write QPS, workload dự kiến tăng 10x.
**Chiến lược:** Write Scaling là thách thức lớn. Kế hoạch đi từ giải pháp tức thời đến tái cấu trúc triệt để.

#### Write Scaling Plan (3 Giai đoạn)

| Giai đoạn | Hành động Chiến lược (Action Plan) | Trade-off Chấp nhận |
| :--- | :--- | :--- |
| **1. Tuning & Mitigation (Short-term)** | **a. Tối ưu SQL & Indexing:** Rà soát query ghi chậm.<br>**b. Async Critical Writes:** Chuyển tác vụ ghi không cần phản hồi ngay (Logs, Email, Stats) sang Queue (Kafka/RabbitMQ). | **Complexity:** Tăng thêm Queue System.<br>**Latency:** Eventual Consistency cho một số tác vụ. |
| **2. Architectural Refactoring (Medium-term)** | **Database Denormalization & NoSQL:** Di chuyển dữ liệu ghi đơn giản, không cần ACID (Activity Streams, Counters) sang Redis hoặc NoSQL (MongoDB). | **Consistency:** Mất tính toàn vẹn ACID.<br>**Complexity:** Logic Join phải chuyển về tầng App. |
| **3. Final State: Sharding (Long-term)** | **Database Partitioning (Sharding):** Chia Master thành nhiều Shards dựa trên Sharding Key (User ID/Location ID). Mỗi Shard chịu 1 phần Write workload. | **Availability & Consistency:** Tăng độ phức tạp vận hành gấp N lần.<br>**Complexity:** Mất khả năng Joins toàn cục, cần Routing Layer thông minh. |

**Tư duy Chiến lược:**
*   **Giai đoạn 1:** Mua thời gian bằng cách giảm tải I/O và chuyển workload sang Async.
*   **Giai đoạn 2:** Giảm áp lực lên MySQL bằng cách dùng kho lưu trữ chuyên biệt (NoSQL/Cache).
*   **Giai đoạn 3:** Giải pháp cuối cùng (Sharding) khi vượt quá giới hạn vật lý.