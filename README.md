<div align="center">
  <img src="./assets/images/logo.png" alt="System Design Learning Logo"/>
</div>

# Học Thiết Kế Hệ Thống (System Design Learning)

> Tài liệu học tập toàn diện về các khái niệm thiết kế hệ thống, lấy cảm hứng từ [system-design-primer](https://github.com/donnemartin/system-design-primer)

Repository này chứa các bài lab thực hành, phiên Q&A, và triển khai thực tế các khái niệm cốt lõi về thiết kế hệ thống. Mỗi module bao gồm giải thích lý thuyết, kịch bản thực tế, và ví dụ code có thể chạy được.

## 📚 Mục Lục

- [Tổng Quan](#-tổng-quan)
- [Cấu Trúc Dự Án](#-cấu-trúc-dự-án)
- [Lộ Trình Học Tập](#-lộ-trình-học-tập)
- [Bắt Đầu](#️-bắt-đầu)
- [Đóng Góp](#-đóng-góp)

## 🎯 Tổng Quan

Dự án này được thiết kế để giúp bạn thành thạo thiết kế hệ thống thông qua:
- **Nền tảng lý thuyết**: Đào sâu vào các khái niệm cốt lõi
- **Bài lab thực hành**: Bài tập hands-on với Docker và database thực tế
- **Phiên Q&A**: Câu hỏi phỏng vấn với câu trả lời chi tiết
- **Kịch bản Production**: Trade-offs thực tế và quyết định kiến trúc

## 📊 Tiến Độ Hiện Tại

### ✅ Đã hoàn thành:
- **D01-D03**: Nền tảng Scalability, CAP Theorem, và Availability Patterns
  - ✓ Scalability Basics (Vertical vs Horizontal)
  - ✓ Performance vs Scalability
  - ✓ Latency vs Throughput
  - ✓ CAP Theorem với ví dụ thực tế (Coffee App 10k RPS)
  - ✓ Consistency Patterns (Strong, Eventual, Weak)
  - ✓ Availability Patterns với hands-on labs

### 🚧 Đang phát triển:
- **D04-D30**: Các module tiếp theo đang được xây dựng theo lộ trình 30 ngày

## 📂 Cấu Trúc Dự Án

### [D01: Các Khái Niệm Nền Tảng](./D01)
Nguyên lý thiết kế hệ thống cốt lõi và các yếu tố cơ bản về hiệu năng.

#### Chủ đề:
- **[01. Khả Năng Mở Rộng (Scalability)](./D01/01.Scalability)** - Vertical vs Horizontal scaling, kiến trúc stateless, quản lý session
  - [Q&A](./D01/01.Scalability/Q&A.md) - Câu hỏi phỏng vấn về chiến lược scaling, load balancing, và write scaling

- **[02. Hiệu Năng vs Khả Năng Mở Rộng](./D01/02.Performance-Scalability)** - Hiểu về các trade-offs
  - [Q&A](./D01/02.Performance-Scalability/Q&A.md) - Đào sâu vào tối ưu hiệu năng

- **[03. Độ Trễ vs Thông Lượng (Latency vs Throughput)](./D01/03.Latency-Throughput)** - Các chỉ số quan trọng cho hiệu năng hệ thống
  - [Q&A](./D01/03.Latency-Throughput/Q&A.md) - Kịch bản thực tế và kỹ thuật tối ưu

---

### [D02: Định Lý CAP & Tính Nhất Quán](./D02)
Hiểu về trade-offs trong hệ thống phân tán và các mô hình consistency.

#### Chủ đề:
- **[Định Lý CAP & Các Mô Hình Consistency](./D02/CAP-ConsistencyPatterns)**
  - [README](./D02/CAP-ConsistencyPatterns/README.md) - Hướng dẫn toàn diện bao gồm:
    - Trade-offs giữa CP vs AP
    - Strong Consistency vs Eventual Consistency
    - Master-Slave Replication
    - Distributed Consensus (Paxos/Raft)
    - Kịch bản sự cố production
    - Tính toán sizing thực tế (ví dụ Coffee App 10k RPS)

---

### [D03: Các Mô Hình Khả Dụng (Availability Patterns)](./D03)
Kiến trúc high availability và chiến lược failover.

#### Chủ đề:
- **[Availability Patterns](./D03/AvailabilityPatterns)**
  - [README](./D03/AvailabilityPatterns/README.md) - Tổng quan về kiến trúc availability
  - [Q&A](./D03/AvailabilityPatterns/Q&A.md) - Câu hỏi phỏng vấn về availability patterns
  
  #### Các Lab:
  - **[StandardLab](./D03/AvailabilityPatterns/StandardLab)** - Active-Passive với Async Replication
    - [README](./D03/AvailabilityPatterns/StandardLab/README.md) - Lab thực hành về replication lag và kịch bản mất dữ liệu
    - Bao gồm setup PostgreSQL trên Docker
    - Thí nghiệm chaos engineering
  
  - **[AdvancedLab](./D03/AvailabilityPatterns/AdvancedLab)** - Thiết lập Active-Active Multi-Master
    - Chiến lược replication nâng cao
    - Cơ chế giải quyết xung đột
  
  - **[ProductionLab](./D03/AvailabilityPatterns/ProductionLab)** - Triển khai production-grade
    - Mô hình deployment thực tế
    - Monitoring và observability

---

## 🚀 Lộ Trình Học Tập 30 Ngày

### 📅 TUẦN 1: SCALABILITY & NETWORK
**Chủ đề:** Start Here → Load Balancing

- [ ] **D01: Scalability Basics**
  - Review [Scalability video/article](./D01/01.Scalability/Q&A.md)
  - [Performance vs Scalability](./D01/02.Performance-Scalability/Q&A.md)
  - [Latency vs Throughput](./D01/03.Latency-Throughput/Q&A.md)

- [ ] **D02: CAP & Consistency**
  - [Availability vs Consistency](./D02/CAP-ConsistencyPatterns/README.md)
  - CAP theorem (CP vs AP)
  - Consistency patterns (Weak/Eventual/Strong)

- [ ] **D03: Availability Patterns**
  - [Fail-over (Active-passive/active)](./D03/AvailabilityPatterns/README.md)
  - [Replication Labs](./D03/AvailabilityPatterns/StandardLab/README.md)
  - Availability in numbers

- [ ] **D04: DNS & CDN**
  - Domain Name System
  - CDN (Push vs Pull)

- [ ] **D05: Load Balancer (LB)**
  - L4 vs L7 Load Balancer
  - Horizontal scaling
  - Active-passive/active-active

- [ ] **D06: Reverse Proxy**
  - Reverse proxy (web server)
  - Load Balancer vs Reverse Proxy

- [ ] **D07: Application Layer**
  - Microservices
  - Service discovery

---

### 📅 TUẦN 2: DATABASES (RDBMS & NoSQL)
**Chủ đề:** Database → SQL vs NoSQL

- [ ] **D08: RDBMS Scaling 1**
  - Master-slave replication
  - Master-master replication

- [ ] **D09: RDBMS Scaling 2**
  - Federation
  - Sharding
  - Denormalization

- [ ] **D10: SQL Tuning**
  - SQL tuning (Index, Query optimization)

- [ ] **D11: NoSQL Types**
  - Key-value (Redis)
  - Document (MongoDB)
  - Wide column (Cassandra)
  - Graph (Neo4j)

- [ ] **D12: SQL or NoSQL**
  - SQL or NoSQL selection trade-offs

- [ ] **D13: Basics Review**
  - Powers of two table
  - Latency numbers every programmer should know

- [ ] **D14: Review Week 2**
  - Ôn tập và củng cố kiến thức tuần 2

---

### 📅 TUẦN 3: CACHING & ASYNC
**Chủ đề:** Cache → Security

- [ ] **D15: Caching Layers**
  - Client/CDN/Web/DB/App caching
  - Caching at query vs object level

- [ ] **D16: Caching Strategies**
  - Cache-aside / Write-through
  - Write-behind / Refresh-ahead

- [ ] **D17: Asynchronism 1**
  - Message queues
  - Task queues

- [ ] **D18: Asynchronism 2**
  - Back pressure

- [ ] **D19: Communication**
  - TCP vs UDP
  - RPC vs REST

- [ ] **D20: Security**
  - Common security concepts

- [ ] **D21: Review Week 3**
  - Ôn tập và củng cố kiến thức tuần 3

---

### 📅 TUẦN 4: REAL WORLD & APPENDIX
**Chủ đề:** Real World Architectures & Interview

- [ ] **D22: Design Process**
  - Study: "System design interview questions" section

- [ ] **D23: Design Key-Value Store**
  - Áp dụng kiến thức: Sharding, Consistent Hashing

- [ ] **D24: Design Web Crawler**
  - Áp dụng: Queues, Politeness, DNS

- [ ] **D25: Real World - Timeline/Feed**
  - Study: Twitter/Facebook architecture docs

- [ ] **D26: Real World - Chat System**
  - Study: WhatsApp/Discord architecture

- [ ] **D27: Real World - Video Streaming**
  - Study: Netflix/YouTube architecture

- [ ] **D28: Company Architectures**
  - Review "Company engineering blogs"

- [ ] **D29: Mock Interview Marathon**
  - Luyện tập phỏng vấn system design

- [ ] **D30: Final Retrospective**
  - Tổng kết và đánh giá lại toàn bộ kiến thức

---

### 💡 Gợi ý theo dõi tiến độ

Sử dụng file [PROGRESS.md](./PROGRESS.md) để theo dõi chi tiết tiến độ học tập của bạn:

```bash
# Mở file PROGRESS.md và đánh dấu [x] cho các mục đã hoàn thành
# File này bao gồm:
# - Checklist chi tiết cho từng ngày
# - Không gian ghi chú
# - Theo dõi thời gian học
# - Đánh giá tổng kết
```

## 🛠️ Bắt Đầu

### Yêu cầu
- Docker & Docker Compose
- Hiểu biết cơ bản về database (PostgreSQL/MySQL)
- Quen thuộc với công cụ command-line

### Chạy các Lab

Hầu hết các lab đều có môi trường Docker. Các bước chung:

```bash
# Di chuyển đến thư mục lab
cd D03/AvailabilityPatterns/StandardLab

# Cấp quyền thực thi cho scripts
chmod +x *.sh

# Khởi động môi trường
docker compose up -d

# Làm theo hướng dẫn trong README của lab
```

## 📖 Các Khái Niệm Chính

### Khả Năng Mở Rộng (Scalability)
- Vertical vs Horizontal Scaling
- Kiến trúc Stateless
- Quản lý Session (Redis/Memcached)
- Chiến lược Load Balancing
- Write Scaling (Sharding, NoSQL, Async Queues)

### Định Lý CAP
- Trade-offs giữa Consistency vs Availability
- Partition Tolerance
- Strong Consistency (2PC, Paxos, Raft)
- Eventual Consistency
- Master-Slave Replication
- Cơ chế Recovery (Anti-entropy, Hinted handoff, Read repair)

### Availability Patterns
- Active-Passive (Failover)
- Active-Active (Multi-Master)
- Chiến lược Replication
- Kịch bản mất dữ liệu (RPO/RTO)
- Chaos engineering

### Performance & Observability
- Request Latency (P99)
- Error Rates
- Replication Lag
- Capacity Planning
- Phân tích Bottleneck

## 🎓 Mẹo Học Tập

1. **Đọc file Q&A trước** - Chúng chứa câu hỏi phỏng vấn giúp định hình các khái niệm
2. **Chạy các lab** - Kinh nghiệm thực hành là then chốt để hiểu trade-offs
3. **Tập trung vào trade-offs** - Thiết kế hệ thống là về việc hiểu bạn được gì và mất gì
4. **Học các kịch bản production** - Phản hồi sự cố thực tế dạy bạn nhiều nhất

## 📝 Ghi Chú

- Toàn bộ nội dung bằng tiếng Việt để dễ hiểu hơn
- Mỗi module bao gồm cả lý thuyết và thực hành
- Các lab được thiết kế để minh họa kịch bản production thực tế
- Tập trung vào hiểu trade-offs hơn là học thuộc các pattern

## 🤝 Đóng Góp

Đây là repository học tập cá nhân. Bạn có thể:
- Fork và điều chỉnh cho việc học của riêng bạn
- Đề xuất cải tiến qua issues
- Chia sẻ kinh nghiệm và kịch bản của bạn

## 📚 Tài Liệu Tham Khảo

- [System Design Primer](https://github.com/donnemartin/system-design-primer) - Nguồn cảm hứng ban đầu
- Các bài báo và nghiên cứu về CAP Theorem
- Best practices về production engineering
- Báo cáo sự cố và post-mortems thực tế

---

**Chúc Bạn Học Tốt! 🚀**

> "Cách tốt nhất để học thiết kế hệ thống là phá vỡ mọi thứ trong môi trường được kiểm soát."
