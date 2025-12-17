<div align="center">
  <img src="../../assets/images/D02.png" alt="D02: CAP Theorem & Consistency Patterns" width="600"/>
</div>

# CAP Theorem & Consistency Patterns: From Theory to Practice

Hiểu về CAP Theorem không chỉ dừng ở lý thuyết suông; đây là vũ khí để bạn đưa ra các quyết định kiến trúc (Architecture Decision Records - ADRs) sắn bén. Trong thế giới phân tán (Distributed Systems), mạng không bao giờ tin cậy được (Partition Tolerance là hiển nhiên). Vì vậy, cuộc chơi thực sự nằm ở việc bạn **chấp nhận hy sinh Consistency (C) hay Availability (A)** khi sự cố xảy ra.

Dưới đây không phải là bài giảng hàn lâm, mà là playbook đúc kết các trade-off thực tế để bạn áp dụng ngay vào bản thiết kế của mình.

## 1. Top 10 Chiến thuật đánh đổi (The Trade-off Playbook)

| # | Chiến thuật (Gain/Pain) | Bản chất kỹ thuật (Deep Dive) |
|---|---|---|
| 1 | **Chọn CP (Consistency over Availability)**<br>_Được:_ Dữ liệu luôn đúng và mới nhất (Atomic).<br>_Mất:_ Sẵn sàng hy sinh trải nghiệm người dùng: request sẽ bị lỗi hoặc treo (timeout) nếu có sự cố mạng. | Hệ thống thà "chết" (unavailable) còn hơn trả về dữ liệu sai. Nó phải chờ node bị phân tách phản hồi thì mới dám confirm. |
| 2 | **Chọn AP (Availability over Consistency)**<br>_Được:_ Hệ thống "bất tử", luôn trả lời request cực nhanh.<br>_Mất:_ Dữ liệu có thể là đồ cũ (stale). Nhất quán chỉ là chuyện "sớm muộn" (eventual).<br><br>_⚠️ Sau khi P được kết nối lại:_<br>• **Dữ liệu cũ (write trong lúc partition) KHÔNG tự động đồng bộ** - cần cơ chế recovery.<br>• **Write mới sẽ được đồng bộ bình thường** - nhưng data loss từ partition window là vĩnh viễn nếu không có recovery mechanism.<br><br>_🔧 Các cơ chế Recovery trong Production:_<br>• **Anti-entropy repair** (Cassandra): Background process chạy định kỳ so sánh dữ liệu giữa các nodes và tự động sync phần khác biệt. Giống như "đối soát sổ sách" tự động.<br>• **Hinted handoff** (DynamoDB): Node còn sống lưu "ghi chú" về writes cần gửi cho node đang offline. Khi node online lại, ghi chú được replay để bù dữ liệu thiếu.<br>• **Read repair**: Khi client đọc dữ liệu, hệ thống phát hiện inconsistency giữa các replicas và trigger sync ngay lập tức. "Vá lỗ hổng" theo kiểu lazy.<br>• **Merkle trees** (Cassandra/DynamoDB): So sánh hash tree của toàn bộ dataset để nhanh chóng tìm ra phần dữ liệu nào khác biệt, tránh phải so sánh từng record.<br>• **Gossip protocol** (Cassandra): Các nodes "tán gẫu" với nhau về metadata và phát hiện ai đang có dữ liệu cũ, sau đó tự động đồng bộ.<br>• **Manual reconciliation**: Script đối soát chạy batch job để fix data inconsistency - phương án cuối cùng khi các cơ chế tự động thất bại. | Thích hợp cho các feature "nhìn thấy là được", không cần chính xác tuyệt đối từng mili-giây (ví dụ: like count, news feed). |
| 3 | **Strong Consistency (2PC/Paxos)**<br>_Được:_ Chắc chắn như "bàn thạch". Tiền đã trừ là trừ, không có chuyện trừ xong rollback ngầm.<br>_Mất:_ Chậm. Rất chậm. Latency tăng vọt và Throughput giảm thê thảm. | Sync replication buộc hệ thống phải chờ đa số (majority) gật đầu. Chỉ dùng cho những logic "sống còn" (tiền nong, inventory). |
| 4 | **Eventual Consistency**<br>_Được:_ Tốc độ bàn thờ. Scale dễ dàng.<br>_Mất:_ Có những khoảnh khắc người dùng thấy dữ liệu "ma" (vừa xóa xong F5 vẫn thấy). | Writes thành công ngay lập tức ở local, sau đó mới âm thầm đồng bộ sang chỗ khác. |
| 5 | **Master-Slave Replication (Async)**<br>_Được:_ Ghi nhanh như gió (vì ghi local master). Vẫn an toàn hơn Single DC.<br>_Mất:_ Nếu Master chết bất đắc kỳ tử trước khi kịp sync sang Slave --> Mất dữ liệu vĩnh viễn (Data Loss Window). | Trade-off kinh điển: Hy sinh một chút rủi ro mất data để đổi lấy Performance ngon nghẻ. |
| 6 | **Paxos/Raft (Distributed Consensus)**<br>_Được:_ "Chuẩn không cần chỉnh" (Strong Consistency) mà vẫn chịu lỗi tốt (không cần 100% node sống).<br>_Mất:_ Chi phí vận hành cực cao. Cực khó debug. Latency cũng không hề dễ chịu. | Chỉ dành cho các hệ thống nền tảng (Core Infrastructure) như ZooKeeper, Etcd, Consuls. Đừng dùng lung tung cho App Logic. |
| 7 | **Weak Consistency (Caching/VoIP)**<br>_Được:_ Real-time, siêu nhanh.<br>_Mất:_ Rớt gói tin? Kệ nó. Dữ liệu cũ? Chấp nhận luôn. | Dùng cho Video Streaming, VoIP, Game realtime hoặc Cache layer. |
| 8 | **Geo-locality (Đa vùng)**<br>_Được:_ Người dùng ở đâu phục vụ ở đó (Low Read Latency).<br>_Mất:_ Tiền server và băng thông (Backbone cost) sẽ làm bạn "đau ví". Đồng bộ dữ liệu xuyên lục địa là ác mộng về độ trễ. | Cân nhắc kỹ: Chỉ nên edge caching hay cần full replication? |
| 9 | **Single Data Center (Đơn giản là nhất)**<br>_Được:_ Mọi thứ đều nhanh (Local LAN), rẻ và dễ quản lý.<br>_Mất:_ "Bỏ hết trứng vào một giỏ". Sập DC là sập tiệm (Catastrophic Failure). | Phù hợp giai đoạn đầu (Startups) hoặc các hệ thống internal không quá critical. |
| 10 | **Cross-DC Transactions (2PC)**<br>_Được:_ An toàn tuyệt đối bất chấp địa lý.<br>_Mất:_ Hiệu năng thảm hại. Một node mạng chập chờn ở Mỹ có thể kéo sập cả giao dịch ở Việt Nam. | "Dao mổ trâu": Chỉ dùng khi pháp lý hoặc business bắt buộc phải vậy. |

## 2. Bảng quyết định kiến trúc (ADR Cheat Sheet)

Dưới đây là bảng "phao" để bạn chọn vũ khí phù hợp, tránh việc dùng dao mổ trâu giết gà:

| Option | Điểm mạnh (Pros) | Điểm yếu (Cons) | Khi nào dùng? | Né ngay khi... | Cái giá ngầm (Hidden Costs) |
|---|---|---|---|---|---|
| **CP** | Chắc chắn đúng (Strong Consistency). Lý tưởng cho Core Banking, Payment. | Giảm Uptime. User sẽ thấy lỗi khi mạng có vấn đề. | Cần đúng tuyệt đối, sai 1 li đi 1 dặm. | Cần High Availability, quy mô user toàn cầu. | Client phải code xử lý lỗi/retry cực khéo, nếu không sẽ tự DDOS chính mình. |
| **AP** | Luôn available. Trải nghiệm mượt mà. | Dữ liệu có thể sai lệch tạm thời (Stale). | E-commerce (giỏ hàng), Social, DNS. | Quản lý kho, Số dư tài khoản. | Code xử lý conflict (merge data) ở tầng App chua hơn bạn tưởng. |
| **Master-Slave (Async)** | Write nhanh. DR (Disaster Recovery) tốt. | Slave đọc có thể thấy data cũ. Rủi ro mất data khi Master chết. | Read-heavy apps. Cần cân bằng giữa Speed và Safety. | Yêu cầu user A vừa ghi xong user B bên kia địa cầu phải thấy ngay. | Xây dựng quy trình Promote Slave lên Master không downtime là cả một nghệ thuật. |
| **2PC (Two-Phase Commit)** | Nhất quán tuyệt đối xuyên server/DC. | Chậm, dễ bị blocking/deadlock. Cổ chai hiệu năng. | Giao dịch tài chính giá trị cao, ít DC. | Cần High Throughput, Web Scale. | Coordinator trở thành điểm nghẽn (Single point of failure/bottleneck). |
| **Paxos/Raft** | Mạnh mẽ, tự động bầu chọn Master mới, không cần can thiệp thủ công. | Khó hiểu, khó cài đặt, latency cao cho thao tác ghi. | Hệ thống điều phối (Coordination services), metadata store. | Cần low-latency cho user facing request. | Đòi hỏi team vận hành (SRE) trình độ cao mới handle nổi khi có sự cố. |

## 3. Nhật ký chiến trường: 8 Kịch bản lỗi (Incident Response)

Thực tế production khắc nghiệt hơn lý thuyết. Đây là những gì sẽ xảy ra và cách bạn đối mặt:

| # | Triệu chứng (Symptom) | Nguyên nhân gốc rễ (Root Cause) | Cách đỡ đòn (Mitigation) | Hồi sức (Recovery) |
|---|---|---|---|---|
| **1** | **Write Timeout tăng vọt**<br>(Tỉ lệ lỗi cao bất thường) | **Network Partition:** Các DC bị cắt liên lạc. "Não" bị chia cắt. | **Hệ thống CP:** Fail fast (trả lỗi ngay cho user).<br>**Hệ thống AP:** Ghi tạm vào local (chấp nhận rủi ro). | Chờ mạng thông, chạy cơ chế Sync (Gossip/Anti-entropy) để vá dữ liệu. |
| **2** | **User than phiền thấy dữ liệu cũ**<br>(Vừa update xong F5 vẫn như cũ) | **Replication Lag:** Master chưa kịp đẩy data sang Slave chỗ user đọc. | Thiết kế UI lừa tình (Optimistic UI). Hoặc dùng Sticky Session (đọc ngay tại nơi vừa ghi). | Không cần làm gì cả, AP nó thế. Giải thích cho PM hiểu. |
| **3** | **App treo cứng, xoay vòng vòng** | **Không set Timeout:** App ngây thơ chờ đợi một response không bao giờ đến. | Luôn set Timeout và dùng Circuit Breaker cho mọi network call. | Restart service. Điều tra xem bottleneck ở đâu. |
| **4** | **Sập toàn tập (DC Outage)**<br>(Mất điện, cá mập cắn cáp) | **Single Point of Failure:** Chỉ chạy ở 1 DC hoặc config sai High Availability. | Phải thiết kế Multi-DC redundancy từ đầu. Test DR định kỳ. | Kích hoạt quy trình Failover (chuyển traffic sang DC dự phòng). Chấp nhận mất ít data nếu dùng Async replication. |
| **5** | **Hệ thống chậm dần đều** | **Tắc đường (Bottleneck):** Traffic tăng nhưng architecture không scale được. | Sharding (chia nhỏ database). Thêm Cache. Rate limit bớt request rác. | Scale out server (thêm máy). Tắt bớt tính năng phụ (Degradation). |
| **6** | **Tiền mất tật mang (Inconsistent Data)** | **Lỗi Transaction:** Commit một nửa (Partial commit) do lỗi mạng giữa chừng. | Đã đụng đến tiền là phải dùng Strong Consistency (2PC) hoặc Saga Pattern cẩn thận. | Chạy script đối soát (Reconciliation) để sửa data bằng tay hoặc bù trừ (Compensating transactions). |
| **7** | **Một con sâu làm rầu nồi canh (Slow Node)** | **Straggler:** Một node bị đơ (do GC, ổ cứng hỏng) làm chậm cả hệ thống. | Monitoring P99 Latency. Dùng Load Balancer thông minh để né node chậm. | Cách ly (Quarantine) node đó ra khỏi pool, chờ sửa xong cho vào lại. |
| **8** | **Hóa đơn Cloud tăng chóng mặt** | **Cross-AZ/Region Traffic:** Copy data qua lại giữa các vùng quá nhiều thừa thãi. | Tối ưu luồng dữ liệu. Chỉ replicate cái gì thực sự cần (Need-to-know basis). | Review lại architecture xem có đang "dùng dao mổ trâu" cho data rác không. |

Chúng ta cần chuyển tư duy từ việc "chọn C hay A" sang "quản lý trade-off C-A trong các kịch bản lỗi (P)". Hệ thống phân tán, đặc biệt là các ứng dụng web quy mô lớn như Coffee App, luôn bị chi phối bởi các giới hạn về độ trễ (latency), băng thông (bandwidth) và tính nhất quán (consistency).

## 4. Giải mã điểm nghẽn & Chiến lược Scaling (Bottlenecks & Scaling)

Trong thực tế, các điểm tắc nghẽn thường xuất phát từ việc chúng ta ảo tưởng về mạng lưới (Fallacies of Distributed Computing). Dưới đây là cách bắt mạch và kê đơn:

| Bottleneck (Điểm tắc) | Nguyên nhân sâu xa (Root Cause) | Tác động (Impact) | Chiến lược Scale (Action Plan) |
|---|---|---|---|
| **Serialization Point** | Các giao thức Strong Consistency (2PC, Paxos) buộc phải xếp hàng (serialize) transaction qua một Coordinator/Leader. | **Low Throughput & High Latency.** Đặc biệt nghiêm trọng khi các DC nằm xa nhau (độ trễ round-trip cao). | **Sharding:** Chia nhỏ phạm vi transaction (Entity Group Sharding). Đừng cố lock cả thế giới, chỉ lock những gì cần thiết. |
| **Partition-induced Stall** | Cố chấp chọn CP khi mạng bị chia cắt. Hệ thống chờ node bị mất tích trả lời. | **Availability giảm thê thảm.** User gặp timeout hoặc chờ vô vọng. | **Circuit Breakers & Timeouts:** Fail fast là thượng sách. Khi thấy độ trễ tăng vọt, chuyển ngay sang chế độ AP hoặc trả lỗi ngay lập tức để giải phóng tài nguyên. |
| **Hot Key / Hot Shard** | Phân bố dữ liệu không đều (Skewed workload). Một vài key nhận traffic gấp 100 lần key khác. | **Nghẽn cổ chai cục bộ.** Một shard quá tải sẽ kéo lùi hiệu năng cả hệ thống. | **Re-sharding tự động:** Sử dụng DB có khả năng tự cân bằng tải. Nếu không, phải dùng Write Throttling hoặc Load Shedding cho các Hot Key đó. |
| **Replication Lag & Network Cost** | Sync data giữa các DC một cách ngây thơ (copy toàn bộ). | **Stale Reads & Hóa đơn mạng khổng lồ.** | **Tối ưu Replication:** Chỉ gửi Log diff thay vì Snapshot. Tận dụng Geo-locality để Slave gần user nhất phục vụ Read. |

## 5. Bộ công cụ giám sát (Observability Pack)

Không đo lường thì không cải thiện được. Đây là những chỉ số "mạch máu" mà SRE cần watch 24/7:

| Tín hiệu (Metrics) | Tại sao quan trọng? | Ngưỡng báo động (Threshold) | Hành động của Operator (Runbook) |
|---|---|---|---|
| **Request Latency (P99)** | Chỉ số tiên quyết của User Experience. Cao bất thường = Tắc nghẽn hoặc Node chậm. | **P99 > 100ms** (Writes Multi-DC) hoặc **> 30ms** (Writes Local). | **Critical (PagerDuty):** Kiểm tra Circuit Breakers. Tìm node "con sâu làm rầu nồi canh" để cách ly ngay. |
| **Error Rate (5xx)** | Đo lường mức độ "chết" của hệ thống. Dấu hiệu của CP mode đang reject request. | **> 0.1%** tổng traffic. | **Critical:** Kích hoạt Failover hoặc Scale Out. Check logs xem có phải lỗi mạng liên DC không. |
| **Replication Lag** | Đo lường "độ cũ" của dữ liệu. Quyết định trải nghiệm Eventual Consistency. | **> 5s** (hoặc tuỳ business SLA). | **Warning:** Kiểm tra băng thông backbone. Replica có đang bị quá tải CPU không xử lý kịp log không? |
| **Cross-DC Drop Rate** | Dấu hiệu sớm của Partition. Mạng trục trặc là khởi đầu của mọi rắc rối. | **Packet loss > 1%** | **Critical:** Xác nhận sự cố mạng. Hệ thống phải chuyển sang mode phòng thủ (CP hoặc AP) theo kịch bản đã định. |

## 6. Sizing Nhanh: Bài toán Coffee App 10k RPS

Dưới đây là bài toán ước lượng tài nguyên (Back-of-the-envelope estimation) để bạn có cái nhìn định lượng cho hệ thống quy mô vừa (Coffee App).

**Giả định:**
1.  **Traffic:** 10,000 RPS (Requests Per Second) lúc cao điểm.
2.  **Payload:** Trung bình 5KB/Request.
3.  **Architecture:** 3 Data Centers (Multihoming) để đảm bảo HA/DR.

### A. Throughput & Volume
*   **QPS đỉnh:** 10,000 req/s.
*   **Tổng requests/ngày:** ~172.8 triệu requests (Giả sử traffic trung bình bằng 20% traffic đỉnh trong 24h).

### B. Băng thông (Bandwidth Planning)
Cần phân biệt rõ băng thông phục vụ User (External) và băng thông đồng bộ nội bộ (Internal Replication).

| Metric | Cách tính | Kết quả | Ghi chú (Hidden Cost) |
|---|---|---|---|
| **External Bandwidth**<br>(Client I/O) | `10k RPS * 5KB * 2 (In/Out)` | **~800 Mbps** | Đây là traffic Internet (CDN/LB). Chia đều cho 3 DC thì mỗi DC chịu tải nhẹ nhàng. |
| **Internal Backbone**<br>(Replication) | `100 MB/s Write * 2 Replicas` | **~1.6 Gbps** | **CHI PHÍ ẨN LỚN:** Traffic này chạy trên đường truyền riêng (Backbone) giữa các DC, đắt đỏ hơn Internet thường. Cần tối ưu protocol. |

### C. Lưu trữ (Capacity Planning)
Giả sử tỉ lệ Write là 20% (2,000 RPS). Lưu trữ trong 1 năm.

*   **Write Volume:** ~173 triệu records mới mỗi ngày.
*   **Raw Data/Năm:** `173M * 365 * 5KB` ≈ **315 TB**.
*   **Tổng lưu trữ (3 Replicas):** `315 TB * 3` ≈ **~1 PB (Petabyte)**.
    > *Lưu ý: Thực tế cần cộng thêm 30-50% cho Index, Metadata và Snapshot backup.*

### D. Bộ nhớ Cache (Redis/Memcached)
Cache là lớp phòng thủ đầu tiên. Chúng ta cần cache "Working Set" (dữ liệu nóng).
*   **Working Set (1 giờ cao điểm):** `10k RPS * 3600s * 5KB` ≈ **180 GB**.
*   **Chiến lược:** Cần cluster Redis với RAM tối thiểu **200GB - 256GB** để đảm bảo hit-rate cao.

---
**Lời kết:** Với quy mô 10k RPS, "chìa khóa" không phải là máy mạnh (Vertical Scaling) mà là kiến trúc **Sharding & Async Replication**. Hãy dùng Master-Slave Async để đảm bảo Performance cho 99% tác vụ, và chỉ dùng Strong Consistency (Paxos) cho 1% tác vụ nhạy cảm liên quan đến túi tiền của khách hàng.

## 7. Tổng kết: CAP & Consistency Patterns (Senior Architect Note)

Làm kiến trúc không phải là học thuộc lòng định lý, mà là hiểu sâu sắc những điểm neo chốt (anchors) để ra quyết định. Dưới đây là 5 "nguyên tắc vàng" và bảng ma trận quyết định giúp bạn định hướng nhanh trong mọi cuộc tranh luận kỹ thuật.

### 5 Điểm Cốt Lõi (Core Strategic Insights)

1.  **Partition Tolerance (P) là Mệnh Lệnh:**
    *   Mạng không bao giờ đáng tin cậy (Fallacy of Distributed Computing).
    *   Do đó, **P** là bất biến. Quyết định của bạn chỉ còn là **hy sinh C hay A** khi Partition xảy ra.
    
2.  **Consistency là Định nghĩa "Mạnh":**
    *   Trong CAP, Consistency = **Atomic/Linearizable** (tức thì, toàn cục).
    *   Eventual Consistency không được tính là "C" trong CAP. Đừng nhầm lẫn!

3.  **Cân bằng C và A là "Software Trade-off":**
    *   CP hay AP được quyết định bởi dòng code bạn viết, bởi logic app bạn chọn (chờ đồng bộ hay ghi liều?).
    *   Quyền lực nằm trong tay Developer, không phải DB Vendor.

4.  **Cái giá cắt cổ của Strong Consistency:**
    *   Muốn C, bạn phải trả bằng **Latency** (gấp đôi round-trip time) và **Throughput** (do phải xếp hàng xử lý).
    *   Thận trọng khi dùng 2PC hay Paxos cho user-facing features.

5.  **Sự Mơ hồ của Lỗi Mạng (Network Ambiguity):**
    *   Hệ thống không bao giờ biết chắc node bên kia bị chết, bị chậm hay đứt mạng.
    *   **Timeout** chính là "lời tiên tri" duy nhất mà bạn có để đoán lỗi và quyết định hy sinh.

### Bảng Trade-offs Quan Trọng Nhất (CAP Decision Matrix)

| Feature | **CP (Consistency Priority)** | **AP (Availability Priority)** |
| :--- | :--- | :--- |
| **Mục tiêu chính** | Bảo toàn Invariants (Tính toàn vẹn). | Tối ưu hóa Performance & Uptime. |
| **Consistency Level** | Strong (Atomic/Linearizable). | Eventual/Weak. |
| **Hành vi khi P xảy ra** | Trả về **Lỗi 503** hoặc **Timeout** (Sacrifice A). | Trả về dữ liệu **Stale** hoặc Chấp nhận **Write cục bộ** (Sacrifice C). |
| **Đặc điểm Performance** | Low Throughput, High Latency (Do Serialization & Synchronous waits). | High Throughput, Low Latency (Do Local Write & Async replication). |
| **Phù hợp Nghiệp vụ** | Giao dịch tài chính, Kiểm kho (Inventory), Lock Servers, Leader Election. | Giỏ hàng, News Feed, DNS, Email, Streaming Media, Analytics. |
