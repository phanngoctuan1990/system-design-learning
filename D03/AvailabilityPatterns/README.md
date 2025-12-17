Đây là phân tích chuyên sâu về các mẫu hình High Availability (HA) dựa trên các nguồn tài liệu được cung cấp, được trình bày theo phong cách của một kiến trúc sư hệ thống cấp cao, tập trung vào các trade-off và chiến lược triển khai.

---

### 1. Tóm tắt 10 Trade-offs Chiến lược

Trong thiết kế hệ thống, việc lựa chọn mẫu hình sẵn sàng cao luôn đi kèm với đánh đổi (trade-off) giữa độ phức tạp, chi phí và hiệu suất. Dưới đây là 10 trade-off quan trọng cần đưa vào Architecture Decision Record (ADR):

1.  **Active-Passive vs. Simplicity:** Bạn đạt được sự đơn giản trong vận hành (chỉ server Active xử lý traffic) nhưng đánh đổi bằng việc tiêu tốn phần cứng cho server Passive vốn chỉ ở trạng thái chờ (standby).
2.  **Fail-over vs. Overhead:** Bạn có được khả năng phục hồi và cơ chế chuyển đổi dự phòng (fail-over) nhưng phải chấp nhận chi phí tăng thêm về phần cứng và gia tăng độ phức tạp của hệ thống.
3.  **Hot vs. Cold Standby:** Bạn có thể giảm thiểu thời gian ngừng hoạt động (downtime) thông qua trạng thái 'hot' standby nhưng phải chịu chi phí vận hành cao hơn do tài nguyên của server Passive được duy trì liên tục.
4.  **Active-Active vs. Routing Complexity:** Bạn có thể phân tán tải (spreading the load) và tối đa hóa việc sử dụng tài nguyên (cả hai server đều xử lý traffic) nhưng yêu cầu phải có logic phức tạp hơn để định tuyến traffic (thông qua DNS cho public-facing hoặc application logic cho internal-facing).
5.  **Fail-over vs. Data Consistency Risk:** Bạn ưu tiên tốc độ ghi tại server Active, nhưng đối mặt với rủi ro tiềm tàng mất dữ liệu nếu hệ thống Active gặp sự cố trước khi dữ liệu mới kịp được sao chép (replicated) sang server Passive.
6.  **Sequential Components vs. Availability:** Bạn đạt được tính mô-đun hóa (modularity) khi các thành phần hoạt động tuần tự nhưng phải chịu sự suy giảm về tổng thể sẵn sàng (Availability (Total) = Avail(Foo) \* Avail(Bar)).
7.  **Parallel Components vs. Cost:** Bạn tăng cường tính sẵn sàng tổng thể lên đáng kể (ví dụ: từ 99.9% lên 99.9999%) thông qua việc chạy song song nhưng buộc phải tăng chi phí đầu tư hạ tầng và độ phức tạp đồng bộ hóa dữ liệu.
8.  **Quantification vs. Constraint:** Bạn có khả năng định lượng độ bền bỉ của dịch vụ bằng "số 9s" (number of 9s) nhưng điều này đặt ra giới hạn nghiêm ngặt về thời gian ngừng hoạt động chấp nhận được (ví dụ: 99.99% chỉ cho phép 52 phút 35.7 giây/năm).
9.  **Active-Passive (Master-Slave) vs. Load:** Bạn duy trì được kiến trúc sao chép đơn giản (master-slave) nhưng phải chấp nhận rằng chỉ Master xử lý việc ghi, giới hạn khả năng mở rộng tải tổng thể.
10. **Active-Active (Master-Master) vs. Synchronization:** Bạn cho phép cả hai node quản lý traffic, nhưng đổi lại là việc giải quyết các vấn đề đồng bộ hóa và xung đột dữ liệu nội tại của kiến trúc master-master.

---

### 2. Bảng Trade-offs Chi tiết (Architecture Decision Playbook)

| Option | Pros | Cons | When to use | When to avoid | Hidden costs (ops/complexity) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Active-Passive Fail-over** (Master-Slave) | Cơ chế phục hồi được xác định rõ ràng (qua heartbeat). Đơn giản hóa việc quản lý traffic (chỉ Active xử lý). | Yêu cầu thêm phần cứng. Tiềm ẩn mất dữ liệu nếu Active sập trước khi replication hoàn tất. Downtime phụ thuộc vào trạng thái standby ('hot' hoặc 'cold'). | Hệ thống có volume traffic thấp, ưu tiên tính nhất quán ghi (write consistency) và yêu cầu quy trình phục hồi đơn giản. | Ứng dụng yêu cầu khả năng chịu tải và khả năng mở rộng cao (high throughput). | Chi phí phần cứng cho máy chủ dự phòng. Độ phức tạp trong việc duy trì trạng thái 'hot' standby và quản lý độ trễ replication. |
| **Active-Active Fail-over** (Master-Master) | Tải được phân tán, tăng hiệu suất sử dụng tài nguyên. Tăng cường khả năng chịu tải tổng thể. | Yêu cầu logic định tuyến traffic phức tạp hơn (cần DNS hoặc application logic biết về cả hai servers). | Hệ thống volume traffic cao, cần tối đa hóa khả năng mở rộng và chịu tải. | Ứng dụng yêu cầu tính nhất quán dữ liệu nghiêm ngặt (strict consistency), nơi xung đột ghi (write conflict) không được chấp nhận. | Chi phí vận hành để quản lý dịch vụ khám phá (service discovery) hoặc DNS routing. Độ phức tạp cao hơn trong việc đồng bộ hóa dữ liệu giữa các Master. |
| **Parallel Components** (Redundancy) | Tăng tính sẵn sàng tổng thể lên gấp bội (Ví dụ: 99.9% -> 99.9999%). Giảm thiểu tác động của lỗi đơn lẻ. | Tăng chi phí hạ tầng do nhân đôi/nhân ba các thành phần. Tăng độ phức tạp quản lý đồng bộ. | Các thành phần quan trọng trong Critical Path (ví dụ: Database, Load Balancer) yêu cầu SLA từ 99.99% trở lên. | Dự án ngân sách eo hẹp hoặc các thành phần có SLA thấp hơn (ví dụ: 99.9%). | Chi phí nhân bản dữ liệu (data duplication) và chi phí logic để xử lý sự cố khi một nhánh lỗi (circuit breaking). |

---

### 3. 8 Failure Modes Thực tế trong Production

Các mẫu hình sẵn sàng cao giới thiệu các điểm yếu mới. Việc hiểu rõ các Failure Modes là bước đầu tiên để xây dựng kịch bản thử nghiệm tính sẵn sàng (Availability Testing/Chaos Engineering) trong NotebookLM.

| Signal/Symptom | Root Cause (Based on Source) | Mitigation Strategy | Recovery Steps |
| :--- | :--- | :--- | :--- |
| 1. Active server bị ngắt kết nối, traffic không chuyển hướng. | Heartbeat bị gián đoạn giữa Active và Passive server, khiến cơ chế fail-over không kích hoạt. | Cấu hình tần suất Heartbeat và timeout cực kỳ nhạy bén (aggressive tuning) và đa kênh giám sát. | Kích hoạt chuyển đổi dự phòng cưỡng bức (force failover) và cô lập server lỗi. Review nhật ký để hiểu nguyên nhân gián đoạn heartbeat. |
| 2. Phục hồi sau fail-over nhưng dữ liệu mới nhất bị mất. | Hệ thống Active bị lỗi trước khi dữ liệu vừa ghi xong có thể được replicated hoàn toàn sang Passive. | Triển khai Replication bán đồng bộ (Semi-synchronous) hoặc đồng bộ (Synchronous) nếu SLA về RPO (Recovery Point Objective) yêu cầu zero data loss. | Thực hiện kiểm tra tính nhất quán (consistency check) thủ công hoặc tự động giữa hai node, sau đó dùng log giao dịch để khôi phục dữ liệu bị thiếu. |
| 3. Downtime quá dài (ví dụ: vài phút) sau khi Active sập. | Passive server đang ở trạng thái 'cold' standby, cần thời gian khởi động (startup) để tiếp quản dịch vụ. | Đảm bảo Passive server luôn chạy ở chế độ 'hot' standby, hoặc ít nhất là 'warm' standby. | Kích hoạt thủ công các service còn thiếu trên Passive và cập nhật playbook để ưu tiên 'hot' standby. |
| 4. Active-Active routing không hiệu quả, một server bị quá tải. | Logic ứng dụng (internal-facing) hoặc DNS (public-facing) không nhận biết được IP của cả hai servers, dẫn đến định tuyến sai. | Sử dụng Load Balancer/Reverse Proxy thông minh (L7) và quản lý TTL (Time-to-Live) của DNS cực thấp để đảm bảo cập nhật nhanh. | Buộc làm mới cache DNS/Load Balancer. Tạm thời hạ tải server bị quá tải để kiểm tra cấu hình định tuyến. |
| 5. Tổng thể sẵn sàng (Total Availability) thấp hơn dự kiến SLA. | Các thành phần phụ thuộc (dependency) quan trọng (có Avail < 100%) được thiết kế chạy nối tiếp (in sequence), làm giảm tổng Avail. | Tái cấu trúc Critical Path, áp dụng mẫu hình Parallel Redundancy cho các thành phần có tính sẵn sàng thấp. | Xây dựng mô hình tính toán Availability dựa trên công thức tuần tự/song song và xác định thành phần yếu nhất để gia tăng redundancy. |
| 6. Phát sinh chi phí vận hành và quản lý hạ tầng vượt mức. | Quyết định triển khai Fail-over đòi hỏi nhiều phần cứng và gia tăng độ phức tạp vận hành. | Định kỳ thực hiện TCO (Total Cost of Ownership) Audit và so sánh chi phí với giá trị SLA mang lại. | Rà soát cấu hình để đảm bảo phần cứng bổ sung (extra hardware) được sử dụng tối ưu (ví dụ: dùng Passive node cho các tác vụ báo cáo/phân tích). |
| 7. (Active-Active) Xung đột ghi dữ liệu (write conflict) xảy ra. | Độ phức tạp nội tại của Master-Master replication khiến các giao dịch đồng thời (concurrent transactions) không được giải quyết thống nhất. | Triển khai các cơ chế giải quyết xung đột (Conflict Resolution) dựa trên thuật toán (ví dụ: Last-Write-Wins, Versioning). | Tạm thời chuyển sang chế độ Active-Passive, đồng bộ hóa lại dữ liệu từ node chính xác và fix logic Conflict Resolution. |
| 8. Không thể chuyển giao IP của Active server cho Passive server. | Lỗi cấu hình mạng hoặc giao thức chuyển đổi IP (Virtual IP/Floating IP) giữa hai node. | Xây dựng quy trình kiểm thử thường xuyên (Failover Drills) để xác minh cơ chế chuyển giao IP hoạt động chính xác. | Khôi phục thủ công IP trên Passive server và điều tra lỗi cấu hình giao tiếp mạng giữa hai node. |

Với vai trò là kiến trúc sư hệ thống, tôi sẽ định hướng bạn phân tích các khía cạnh vận hành và định lượng của các mẫu hình sẵn sàng cao (Availability patterns) để chuẩn bị cho việc xây dựng NotebookLM.

---

### 1. Bottlenecks & Scaling (Operational Insight)

Các mẫu hình Active-Passive và Active-Active giúp tăng tính sẵn sàng, nhưng đồng thời chúng cũng tạo ra các điểm nghẽn mới liên quan đến I/O, độ trễ và quản lý trạng thái.

| Bottleneck Phổ Biến | Mô Tả/Context HA Pattern | Giải Pháp Scaling Chiến Lược |
| :--- | :--- | :--- |
| **Single Write Master** | Trong mô hình Active-Passive (Master-Slave), chỉ Master xử lý việc ghi. Khi tải ghi tăng cao, Master trở thành điểm nghẽn nghiêm trọng, giới hạn khả năng mở rộng tổng thể. | **Database Sharding:** Phân vùng dữ liệu (Horizontal Scaling) theo chức năng hoặc ID người dùng để phân tán tải ghi ra nhiều Master độc lập. |
| **Replication Lag** | Khoảng cách thời gian giữa thời điểm ghi trên Master và thời điểm dữ liệu xuất hiện trên Passive/Slave. Độ trễ cao vi phạm RPO (Recovery Point Objective) và tăng rủi ro mất dữ liệu. | **Upgrade Link/Topology:** Tăng băng thông kết nối giữa các node. Sử dụng Replication bán đồng bộ (Semi-synchronous) hoặc đồng bộ (Synchronous) để kiểm soát trade-off giữa độ trễ và tính nhất quán. |
| **Thundering Herd** | Khi Active node gặp sự cố và nhiều client hoặc service phụ thuộc cố gắng kết nối lại hoặc fail-over cùng một lúc, tạo ra một làn sóng yêu cầu đột biến (spike) quá tải lên node Passive vừa chuyển trạng thái thành Active. | **Client-Side Resilience:** Bắt buộc áp dụng **Exponential Backoff và Jitter** trong logic retry của client. Điều này dàn trải thời gian retry thay vì dồn tất cả vào cùng một thời điểm. |
| **Hot Key/Data Skew** | Một vài key dữ liệu (ví dụ: một tài khoản người dùng rất nổi tiếng, hoặc một sản phẩm bán chạy) được truy cập quá thường xuyên, tập trung tải lên một Shard hoặc một Cache node duy nhất. | **Client-Side Fanout (Layer 7):** Sử dụng hàm băm (hashing function) để phân tán yêu cầu đọc/ghi cho key đó sang nhiều node Cache/DB dự phòng. Áp dụng Cache tầng L1 (Local Cache). |
| **DNS/Routing Cooldown** | Trong Active-Active, việc chuyển đổi dự phòng có thể bị chậm do TTL (Time-to-Live) của DNS quá cao, khiến client tiếp tục truy cập vào IP cũ đã bị lỗi. | **Low TTL Configuration:** Cấu hình TTL cực thấp (dưới 60 giây) cho các bản ghi A (hoặc CNAME) của service công cộng. Sử dụng các dịch vụ định tuyến thông minh (ví dụ: AWS Route 53 Health Checks). |

---

### 2. Observability Pack (Operational Checklist)

Việc duy trì tính sẵn sàng đòi hỏi phải có khả năng quan sát (Observability) xuất sắc, đặc biệt là theo dõi trạng thái chuyển giao (fail-over) và đồng bộ hóa (replication).

| Signal | Why it matters | Threshold | Alerting suggestion | Operator action |
| :--- | :--- | :--- | :--- | :--- |
| **Heartbeat Failure Count** | Heartbeat là cơ chế kích hoạt fail-over Active-Passive. Theo dõi lỗi là chìa khóa để đảm bảo cơ chế tự phục hồi hoạt động. | 3 Heartbeat liên tiếp bị gián đoạn (Khoảng 5 - 15 giây). | **P0 - Critical:** Tự động kích hoạt fail-over và gửi thông báo khẩn cấp đến đội SRE/On-Call. | Kiểm tra tình trạng kết nối mạng và tài nguyên của server Active. Chuẩn bị kịch bản failback (chuyển về trạng thái ban đầu). |
| **Replication Lag (Time/Bytes)** | Đo lường RPO (Recovery Point Objective). Nếu lag cao, rủi ro mất dữ liệu tiềm tàng sẽ tăng lên. | Độ trễ > 5 giây (hoặc vượt quá RPO định nghĩa của hệ thống). | **P1 - High Warning:** Báo động nếu xu hướng lag tăng nhanh trong 5 phút. | Tạm dừng các tác vụ nền (background jobs) trên Master. Kiểm tra I/O Wait và tối ưu hóa các câu truy vấn chậm (slow queries). |
| **QPS Ratio (A/B)** | Áp dụng cho Active-Active. Theo dõi sự phân tán tải (spreading the load) giữa các node để phát hiện lỗi định tuyến. | Chênh lệch QPS giữa các node > 20% (Ví dụ: Node A 7k RPS, Node B 3k RPS). | **P2 - Warning:** Báo động khi độ lệch tải kéo dài trên 10 phút. | Kiểm tra cấu hình DNS hoặc logic định tuyến ứng dụng. Cân nhắc làm ấm (warm-up) lại cache. |
| **CPU/Memory Utilization (Passive)** | Xác minh trạng thái "hot" standby. Nếu tài nguyên quá thấp hoặc không ổn định, Passive có thể không sẵn sàng để tiếp quản. | CPU Idle < 20% (nếu Passive chạy tác vụ phụ), hoặc CPU Utilization đột ngột giảm về 0%. | **P2 - Warning:** Cảnh báo nếu Passive không hoạt động đúng như mong đợi. | Xác minh tất cả các dịch vụ nền tảng (Database services, Caching) trên Passive đang chạy và được cấp phát tài nguyên đầy đủ. |

---

### 3. Sizing Nhanh (Baseline Estimation)

Đây là ước lượng cấp tốc cho hệ thống Coffee App (10k RPS, 5KB Payload) dựa trên nguyên tắc tính toán dung lượng cơ bản, cần được đưa vào NotebookLM để bắt đầu Capacity Planning.

#### Dữ liệu đầu vào:
*   RPS (Request Per Second): $R = 10,000$
*   Payload Size (trung bình): $P = 5 \text{ KB}$
*   Tỷ lệ đọc/ghi giả định: 90% Đọc / 10% Ghi.
*   Cache Hit Ratio (CHR) giả định: 90%.

#### A. Bandwidth (Yêu cầu Mạng)

Chúng ta cần tính toán tổng lưu lượng ra/vào (In/Out) tại Load Balancer.

1.  **Tính toán Lưu lượng Dữ liệu (Bytes/giây):**
    $$\text{Traffic (B/s)} = R \times P \times 2 \text{ (In/Out)}$$
    $$ = 10,000 \text{ RPS} \times 5 \text{ KB/req} \times 2$$
    $$ = 100,000 \text{ KB/s} = 100 \text{ MB/s}$$
2.  **Chuyển đổi sang Bit/giây (Tốc độ mạng):**
    $$100 \text{ MB/s} \times 8 \text{ bits/byte} = 800 \text{ Mbps} \approx 0.8 \text{ Gbps}$$

> **Kết luận Baseline Bandwidth:** Yêu cầu tối thiểu là **1 Gbps** (Gigabit Ethernet) để xử lý tải trung bình. Tuy nhiên, khuyến nghị kiến trúc sư hệ thống nên sử dụng **10 Gbps** để đảm bảo khả năng chịu tải đỉnh (burst traffic) và khả năng mở rộng trong tương lai.

#### B. Storage (Dung lượng Ghi/ngày)

Chủ yếu tập trung vào dữ liệu ghi mới (Write Load).

1.  **Tính toán Tải ghi (Writes/giây):**
    $$\text{Writes/s} = 10,000 \text{ RPS} \times 10\% = 1,000 \text{ Writes/s}$$
2.  **Tính toán Dung lượng Ghi/ngày:**
    $$\text{Storage/day} = 1,000 \text{ Writes/s} \times 5 \text{ KB/write} \times 86,400 \text{ giây/ngày}$$
    $$ \approx 432,000,000 \text{ KB/ngày} \approx 432 \text{ GB/ngày}$$

> **Kết luận Baseline Storage:** Hệ thống Database cần có khả năng xử lý tốc độ ghi **432 GB/ngày** trên các node Master. Việc này đòi hỏi ổ cứng SSD hiệu suất cao (High-IOPS SSD) và chiến lược sao lưu/lưu trữ dài hạn (archiving).

#### C. QPS (Queries Per Second) Internal Load

Đây là tải thực sự đánh vào Database sau khi cache đã lọc.

1.  **Tải Đọc (Read Load) lên DB:**
    $$\text{Read QPS to DB} = \text{Total Read RPS} \times (1 - CHR)$$
    $$ = (10,000 \text{ RPS} \times 90\%) \times (1 - 0.90)$$
    $$ = 9,000 \times 0.10 = 900 \text{ QPS}$$
2.  **Tải Ghi (Write Load) lên DB:**
    $$ = 1,000 \text{ QPS}$$
3.  **Total QPS Internal Load:**
    $$ = 900 (\text{Read}) + 1,000 (\text{Write}) = 1,900 \text{ QPS}$$

> **Kết luận Baseline QPS:** Master Database (trong Active-Passive) hoặc tổng các Master (trong Active-Active) cần xử lý tối thiểu **1,900 QPS** liên tục.

#### D. Memory cho Cache (Working Set)

Giả sử chúng ta cần cache working set trong khoảng thời gian 30 phút cao điểm để đạt được 90% CHR.

1.  **Tính toán Dữ liệu trong 30 phút:**
    $$\text{Cache Memory} = 10,000 \text{ RPS} \times 5 \text{ KB/req} \times 30 \text{ phút} \times 60 \text{ giây/phút}$$
    $$ = 90,000,000 \text{ KB} \approx 90 \text{ GB}$$

> **Kết luận Baseline Cache Memory:** Yêu cầu tối thiểu là **100 GB RAM** cho hệ thống Cache phân tán (ví dụ: Redis cluster). Nếu triển khai Active-Active, bộ nhớ cache này có thể được nhân đôi và phân tán giữa các node để tăng tính sẵn sàng và khả năng chịu tải.