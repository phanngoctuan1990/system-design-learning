# Phỏng vấn Giả lập: CAP & Consistency Patterns (Mock Interview)

Đây là 3 câu hỏi phỏng vấn được thiết kế để đánh giá tư duy hệ thống và khả năng ra quyết định kiến trúc của bạn về chủ đề **CAP & Consistency Patterns**, theo tiêu chuẩn của một Senior Software Engineer tại Google.

> **Bối cảnh:** Xin chào, tôi là Lead Architect. Hôm nay chúng ta sẽ tập trung vào các trade-off trong hệ thống phân tán, cụ thể là CAP Theorem và các Consistency Patterns. Tôi kỳ vọng bạn không chỉ nhắc lại định nghĩa mà còn phân tích được ý nghĩa kinh doanh và chi phí vận hành của mỗi lựa chọn.

---

## 1. Level Junior (Kiến thức Cơ bản & Ứng dụng)

### Câu hỏi: Trade-off Bắt buộc và Sự khác biệt Mềm dẻo (Software Trade-off)
"Trong hệ thống phân tán, **sự cố mạng (network failures)** là một định luật (fallacy). Điều này khiến Partition Tolerance (P) trở thành yêu cầu bắt buộc, buộc chúng ta phải thực hiện sự đánh đổi giữa **Consistency (C)** và **Availability (A)**.

1.  Hãy định nghĩa **Consistency** theo chuẩn Atomic/Linearizable và **Availability** theo ngữ cảnh của CAP.
2.  Phân tích trade-off **Software Trade-off** giữa CP và AP. Hãy đưa ra hai ví dụ nghiệp vụ điển hình: một nơi bạn buộc phải chọn CP và một nơi bạn nên chọn AP để tối ưu hóa hiệu năng."

### ✅ Trả lời:

#### 1. Định nghĩa Consistency và Availability

**Consistency (Atomic/Linearizable):**
*   Mọi thao tác đọc (read) sau một thao tác ghi (write) thành công **phải** trả về giá trị mới nhất đó, bất kể client đọc từ node nào trong hệ thống.
*   Nói cách khác: Hệ thống hoạt động như thể chỉ có **một bản sao dữ liệu duy nhất** (single replica illusion). Mọi thao tác đều có vẻ như xảy ra ngay lập tức tại một thời điểm duy nhất giữa lúc bắt đầu và kết thúc.
*   **Ví dụ:** Nếu User A gửi tiền vào tài khoản lúc 10:00:00.000, thì User B đọc số dư lúc 10:00:00.001 **phải** thấy số tiền đã được cộng.

**Availability (trong ngữ cảnh CAP):**
*   Mọi request gửi đến một node **non-failing** (không bị lỗi phần cứng) **phải** nhận được response trong một khoảng thời gian hợp lý (bounded time).
*   Quan trọng: Response có thể là dữ liệu cũ (stale), nhưng **không được là lỗi timeout hoặc error**.
*   **Ví dụ:** Khi user refresh newsfeed, họ luôn thấy *một cái gì đó* (có thể là feed cũ 5 giây), chứ không phải màn hình trắng hoặc lỗi 503.

#### 2. Phân tích Trade-off CP vs. AP

| Khía cạnh | CP (Consistency + Partition Tolerance) | AP (Availability + Partition Tolerance) |
|---|---|---|
| **Khi Partition xảy ra** | Hệ thống **từ chối phục vụ** (trả về lỗi 503/timeout) để đảm bảo không ai đọc được dữ liệu sai. | Hệ thống **vẫn phục vụ** (trả về 200 OK) nhưng dữ liệu có thể là bản cũ (stale). |
| **Ưu tiên** | Tính đúng đắn của dữ liệu (Data Integrity) | Trải nghiệm người dùng (User Experience/Uptime) |
| **Chi phí ẩn** | Latency cao (chờ đồng bộ), Throughput thấp. Client phải xử lý retry. | Cần cơ chế Conflict Resolution khi partition heal. Logic phức tạp ở tầng Application. |

**Ví dụ nghiệp vụ BẮT BUỘC chọn CP:**
*   **Hệ thống chuyển tiền ngân hàng:** Nếu User A chuyển 10 triệu cho User B, hệ thống **không được phép** trừ tiền A mà không cộng tiền B (hoặc ngược lại). Nếu có partition, thà trả về lỗi "Giao dịch thất bại, vui lòng thử lại" còn hơn để xảy ra tình trạng tiền "bốc hơi" hoặc "sinh sôi".
*   **Hệ thống quản lý tồn kho (Inventory):** Nếu chỉ còn 1 sản phẩm, không thể để 2 người cùng mua thành công.

**Ví dụ nghiệp vụ NÊN chọn AP:**
*   **Giỏ hàng E-commerce (Shopping Cart):** Nếu user thêm sản phẩm vào giỏ hàng, việc giỏ hàng hiển thị chậm vài giây không phải là thảm họa. Quan trọng là user không bị lỗi và có thể tiếp tục mua sắm. Khi checkout mới cần kiểm tra lại.
*   **Newsfeed/Timeline (Facebook, Twitter):** User thà thấy feed cũ 5 giây còn hơn là màn hình trắng. Tính "real-time" là tương đối, không cần chính xác tuyệt đối.

---

## 2. Level Mid (Troubleshooting & Phân tích Lỗi)

### Câu hỏi: Nhầm lẫn giữa Slow Machine và Network Partition
"Bạn đang vận hành một dịch vụ lưu trữ nhật ký giao dịch (transaction log) sử dụng chiến lược **AP (Availability/Partition Tolerance)** để đảm bảo thông lượng cao. Giao thức sao chép (replication) là bất đồng bộ (asynchronous).

Đột nhiên, đội ngũ giám sát (Observability team) cảnh báo rằng:
1.  **Độ trễ đọc (Read Latency P99)** tăng vọt trên các node Replica (slave).
2.  Users bắt đầu thấy **dữ liệu cũ (stale data)** kéo dài hơn 5 giây.
3.  Tuy nhiên, **không có lỗi timeout 503 nào xảy ra**.

Trong mạng không đồng bộ (asynchronous network), chúng ta không thể phân biệt một máy bị hỏng, bị Partition hay chỉ đơn giản là bị chậm (slow machine).

Trong tình huống này, bạn nghi ngờ hệ thống đang gặp phải **Replication Lag do Slow Machine (ví dụ: GC Pause)** hay **Partial Network Partition**?

Hãy giải thích:
1.  Lý do tại sao hệ thống AP vẫn duy trì Availability (không trả về lỗi 503) dù dữ liệu bị Stale.
2.  Làm thế nào để các chỉ số Latency P99 và Replication Lag giúp bạn phân biệt giữa Slow Machine và Partition?
3.  Biện pháp khắc phục (Mitigation) tức thời nào bạn sẽ áp dụng để giảm thiểu rủi ro dữ liệu Stale?"

### ✅ Trả lời:

#### 1. Tại sao AP vẫn Available dù Stale?

Đây chính là **bản chất của AP mode**: Hệ thống ưu tiên trả về response nhanh chóng, bất kể dữ liệu có mới nhất hay không.

*   Khi client gửi Read request đến Replica, Replica **không cần hỏi Master** xem dữ liệu có mới không. Nó chỉ đơn giản trả về những gì nó có trong local storage.
*   Replication diễn ra **bất đồng bộ (async)**: Master ghi xong trả về 200 OK ngay, sau đó mới *cố gắng* đẩy data sang Replica. Nếu Replica chậm nhận (do bất kỳ lý do gì), client đọc từ Replica sẽ thấy data cũ.
*   **Không có lỗi 503** vì Replica vẫn đang hoạt động bình thường (healthy), nó chỉ đơn giản là có dữ liệu chưa được cập nhật.

> **Insight:** Đây là trade-off cố hữu của Eventual Consistency. Hệ thống đánh đổi tính "mới nhất" để lấy tốc độ và uptime.

#### 2. Phân biệt Slow Machine vs. Partition bằng Metrics

| Signal | Slow Machine (GC Pause) | Partial Network Partition |
|---|---|---|
| **CPU/Memory của Replica** | CPU spike cao (GC chiếm CPU) hoặc Memory pressure. | CPU/Memory bình thường. |
| **Network I/O của Replica** | Network I/O **vẫn có traffic** (đang cố gắng nhận data, chỉ là xử lý chậm). | Network I/O **giảm đột ngột hoặc về 0** (không nhận được gói tin từ Master). |
| **Replication Lag Pattern** | Lag tăng **đều đều** (do xử lý chậm), sau đó **tự hồi phục** khi GC xong. | Lag tăng **vô hạn** (không bao giờ giảm) cho đến khi network được sửa. |
| **Ping/Health Check Master → Replica** | **Thành công** (network vẫn thông). | **Thất bại** hoặc timeout. |
| **Log của Master** | Không có lỗi gửi data. | Log báo lỗi `Connection refused` hoặc `Timeout sending to replica`. |

**Cách điều tra thực tế:**
1.  SSH vào Replica, chạy `top` hoặc `htop` xem CPU có bị một process nào chiếm hết không (thường là Java GC).
2.  Chạy `ping <master_ip>` từ Replica để kiểm tra network connectivity.
3.  Kiểm tra log replication của Master: Nếu thấy `Connection timeout`, đó là Partition. Nếu thấy `Replication queue growing but sending OK`, đó là Slow Machine.

#### 3. Biện pháp Mitigation tức thời

**Bước 1: Xác nhận và Cách ly (Identify & Isolate)**
*   Nếu là **Slow Machine**: Cách ly node đó khỏi Load Balancer pool (ngừng gửi traffic đọc đến node chậm). Chờ GC xong hoặc restart service.
*   Nếu là **Partition**: Không cần làm gì với node đó (nó đã bị cô lập rồi). Tập trung đảm bảo các node healthy khác phục vụ traffic.

**Bước 2: Tăng cường Read từ Master (Read-Your-Writes)**
*   Đối với các nghiệp vụ nhạy cảm (vừa write xong cần đọc lại ngay), định tuyến Read request đến Master thay vì Replica.
*   Đây là chiến lược **Sticky Session** hoặc **Read-Your-Writes Consistency**.

**Bước 3: Cảnh báo Bounded Staleness**
*   Nếu hệ thống có implement Bounded Staleness (như trong ProductionLab của chúng ta), endpoint Read nên trả về cảnh báo trong response: `"Consistency_Status": "STALE (EXCEEDS_BOUND)"`.
*   Tầng Application có thể dựa vào đó để hiển thị thông báo cho user: "Dữ liệu có thể chưa được cập nhật".

**Bước 4: Dài hạn - Circuit Breaker**
*   Implement Circuit Breaker cho replication connection. Nếu Replica không nhận được data quá lâu (ví dụ > 10s), tự động đánh dấu nó là "degraded" và loại khỏi read pool.

---

## 3. Level Senior (System Design & Tinh chỉnh Kiến trúc)

### Câu hỏi: Đánh đổi Hiệu năng khi Chuyển đổi Consistency
"Công ty của bạn đang sử dụng kiến trúc **Master-Slave Replication** (như App Engine Datastore đã từng chọn) để phục vụ một dịch vụ quan trọng, đạt được **độ trễ ghi (Write Latency) thấp** vì replication diễn ra bất đồng bộ. Tuy nhiên, rủi ro **mất dữ liệu nhỏ (data loss window)** và vấn đề Stale Reads là không chấp nhận được nữa.

**Yêu cầu:** Bạn phải nâng cấp hệ thống lên **Strong Consistency (Atomic/Linearizable)** và mở rộng sang 3 Data Centers (DC) để đạt khả năng phục hồi thảm họa.

1.  Nếu bạn chọn triển khai giao thức **Distributed Consensus (ví dụ: Paxos hoặc 2PC)** để đạt Strong Consistency giữa 3 DC, hãy phân tích tác động trực tiếp và bắt buộc lên **Write Latency**. Cụ thể, tại sao độ trễ lại tăng gấp đôi (hoặc hơn) so với kiến trúc Master-Slave cũ?
2.  Nếu yêu cầu kinh doanh buộc bạn phải duy trì Strong Consistency nhưng không được vượt quá Latency P99 hiện tại (ví dụ: 50ms), bạn sẽ đề xuất chiến lược kiến trúc nào để cân bằng C và Latency? *(Gợi ý: Cân nhắc các kỹ thuật như Sharding hoặc giới hạn phạm vi giao dịch)*.
3.  Làm thế nào việc sử dụng **Entity Groups** trong sharding có thể giúp bạn đạt được tính nguyên tử (atomic transaction) mà không cần Paxos/2PC trên toàn bộ hệ thống?"

### ✅ Trả lời:

#### 1. Tại sao Write Latency tăng gấp đôi (hoặc hơn) với Paxos/2PC?

**Với Master-Slave Async (Kiến trúc cũ):**
```
Client → Master (Write local) → Return 200 OK
         ↓ (Async, không chờ)
       Slave
```
*   **Latency = 1 Round Trip** (Client → Master → Client).
*   Master ghi xong local disk là trả về ngay. Replication diễn ra ngầm sau đó.

**Với Paxos/2PC (Kiến trúc mới - Strong Consistency):**
```
Client → Leader (Propose)
         ↓ (Phase 1: Prepare)
       DC1, DC2, DC3 (Gửi prepare request)
         ↓ (Chờ Majority ACK)
       Leader (Phase 2: Accept)
         ↓ (Gửi accept request)
       DC1, DC2, DC3 (Gửi accept ACK)
         ↓ (Chờ Majority ACK)
       Leader → Return 200 OK to Client
```
*   **Latency = 2 Round Trips** (tối thiểu, thực tế có thể hơn).
    *   Round Trip 1: Leader → Followers (Prepare) → Leader.
    *   Round Trip 2: Leader → Followers (Accept) → Leader.
*   Nếu 3 DC nằm ở các vùng địa lý khác nhau (ví dụ: US, EU, Asia), mỗi round trip có thể mất **50-100ms**. Tổng latency: **100-200ms** thay vì 10-20ms như trước.

**Lý do sâu xa:**
*   Strong Consistency **bắt buộc** hệ thống phải **chờ xác nhận từ majority (đa số)** trước khi trả về thành công.
*   Đây là cái giá không thể tránh khỏi của CAP: Muốn C (Consistency), phải hy sinh Latency/Throughput.

#### 2. Chiến lược cân bằng C và Latency (Giữ P99 < 50ms)

**Chiến lược 1: Geo-Colocation (Đặt DC gần nhau)**
*   Thay vì đặt 3 DC ở 3 châu lục, đặt cả 3 DC trong cùng một Region (ví dụ: 3 Availability Zones trong AWS us-east-1).
*   Latency giữa các AZ trong cùng region: **< 2ms**.
*   Latency 2 round trips: **< 4ms** → Đạt P99 < 50ms dễ dàng.
*   **Trade-off:** Giảm khả năng DR (Disaster Recovery) vì cả 3 DC đều nằm trong một region. Nếu cả region bị sự cố (hiếm nhưng có thể xảy ra), mất toàn bộ.

**Chiến lược 2: Sharding + Local Consensus (Entity Groups)**
*   Không chạy Paxos trên **toàn bộ dataset**, mà chỉ chạy Paxos trong phạm vi **một Shard (Entity Group)**.
*   Mỗi Shard được đặt trong một cụm 3 nodes **gần nhau** (cùng region hoặc cùng DC).
*   Transaction chỉ cần consensus trong phạm vi Shard đó, không cần đợi các Shard khác.
*   **Ví dụ:** User A ở Việt Nam, data của User A nằm trong Shard "VN-Shard" được replicate trong 3 nodes ở Singapore. Latency consensus: ~5-10ms.

**Chiến lược 3: Hierarchical Consensus**
*   Kết hợp Sync và Async:
    *   **Intra-Region:** Sync replication (Paxos/Raft) giữa 3 AZ trong cùng region. → Strong Consistency.
    *   **Cross-Region:** Async replication giữa các Region. → Eventual Consistency cho DR.
*   User được phục vụ bởi Region gần nhất. Nếu Region đó sập, failover sang Region khác (chấp nhận mất một ít data trong data loss window).

#### 3. Entity Groups và Atomic Transactions không cần Global Paxos

**Khái niệm Entity Group:**
*   **Entity Group** là một nhóm các entities (records) có quan hệ logic với nhau và **thường được truy cập cùng nhau**.
*   **Ví dụ:** Một `Order` và tất cả `OrderItems` của nó thuộc cùng một Entity Group. Một `User` và `UserProfile`, `UserSettings` của họ thuộc cùng một Entity Group.

**Cách hoạt động:**
1.  **Sharding theo Entity Group:** Toàn bộ data của một Entity Group được lưu trên **cùng một Shard (cùng một cụm Paxos)**.
2.  **Transaction trong Entity Group:** Vì tất cả data liên quan nằm trên cùng một Shard, transaction chỉ cần **local Paxos** trong Shard đó. Không cần 2PC/Paxos xuyên Shard.
3.  **Transaction xuyên Entity Group:** Nếu cần (hiếm khi), sử dụng các pattern như Saga hoặc chấp nhận Eventual Consistency.

**Ví dụ cụ thể (E-commerce):**
```
Entity Group: Order #12345
├── Order { id: 12345, user_id: 100, total: 500k }
├── OrderItem { order_id: 12345, product_id: A, qty: 2 }
└── OrderItem { order_id: 12345, product_id: B, qty: 1 }
```
*   Khi user đặt hàng, cần tạo 1 Order + 2 OrderItems atomically.
*   Vì cả 3 records thuộc cùng Entity Group (cùng Shard), chỉ cần một local transaction. Không cần distributed transaction.

**Tại sao cách này hiệu quả?**
*   **Giảm phạm vi coordination:** Thay vì phải đồng thuận trên toàn bộ 3 DC x tất cả data, chỉ cần đồng thuận trong phạm vi 1 Shard (3 nodes gần nhau).
*   **Horizontal Scaling:** Thêm Shards để tăng throughput. Mỗi Shard có thể xử lý ~10k writes/sec nếu được tối ưu.
*   **Đây chính xác là cách Google App Engine Datastore hoạt động:** Strong Consistency trong Entity Group, Eventual Consistency giữa các Entity Groups.

> **Kết luận Senior-level:** Bí quyết không phải là "chọn C hay A", mà là **thu hẹp phạm vi cần Strong Consistency** xuống mức nhỏ nhất có thể (Entity Group), và chấp nhận Eventual Consistency cho phần còn lại. Đây là trade-off thực tế mà các hệ thống lớn như Spanner, CockroachDB, và Datastore đều áp dụng.