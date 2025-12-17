# 🧪 Scalability Verification Steps

Tài liệu này hướng dẫn verify Lab Scalability, tập trung vào 2 kịch bản test chính: **Statelessness** và **High Availability (Failover)**.

---

## 🏗️ Phase 1: Environment Setup

Trước khi chạy bất kỳ test scenario nào, hãy đảm bảo môi trường đã sẵn sàng.

**1. Khởi động hệ thống:**
```bash
docker compose up --build -d
```

**2. Verify Health Check:**
Đảm bảo cả 3 services (nginx, redis, và 2 app clones) đều running và healthy.
```bash
docker compose logs -f redis app_clone_1
# Chờ đến khi thấy log "Running on http://0.0.0.0:5000"
```

---

## 🧪 Phase 2: Test Scenarios

### Scenario 1: Statelessness & Load Distributing
**Mục tiêu:** Chứng minh hệ thống không lưu trạng thái trên App Server và Load Balancer phân phối tải đều.

**Thực thi:**
```bash
# Chạy script gửi request liên tục
bash test_traffic.sh
```

**Kết quả Mong Đợi:**
1.  **Session Counter tăng dần đều** (1, 2, 3...) dù request nhảy qua lại giữa các server.
2.  **Server Hitted** thay đổi luân phiên (`app_clone_1` <-> `app_clone_2`).

| Request | Server Hitted | Session Counter | Insight |
| :--- | :--- | :--- | :--- |
| 1 | `app_clone_1` | 1 | Session created in Redis |
| 2 | `app_clone_2` | 2 | **Stateless**: Clone 2 đọc được session từ Redis |
| 3 | `app_clone_1` | 3 | **Persisted**: Clone 1 đọc update từ Clone 2 |

**Kiểm tra Logs Nginx (Optional):**
```bash
docker compose logs nginx | grep "GET / HTTP/1.1" | awk '{print $NF}'
# Output nên cho thấy traffic được chia đều 50/50
```

### Scenario 2: Least Connections Load Balancing
**Mục tiêu:** Chứng minh `least_conn` ưu tiên server có ít connection đang hoạt động nhất.

**Thực thi:**
```bash
# Terminal 1: Gửi slow request (giữ connection 5s)
curl http://localhost/slow &

# Terminal 2: Chạy script gửi request liên tục
bash test_traffic.sh
```

**Kết quả Mong Đợi:**
- Server đang xử lý `/slow` sẽ ít nhận request mới hơn
- Các request nhanh được ưu tiên gửi đến server rảnh

| Thời điểm | Request | Server | Lý do |
| :--- | :--- | :--- | :--- |
| T0 | `/slow` | `app_clone_1` | Bắt đầu xử lý 5s |
| T0.5 | `/` | `app_clone_2` | clone_1 đang bận → chọn clone_2 |
| T0.6 | `/` | `app_clone_2` | clone_1 vẫn bận |
| T5+ | `/` | `app_clone_1` | clone_1 rảnh → phân phối đều lại |

**So sánh với Round Robin:**
- Round Robin: Phân phối đều bất kể server đang bận hay rảnh
- Least Conn: Tránh dồn request vào server đang xử lý request chậm

---

### Scenario 3: Redundancy & Failover (SPOF Testing)
**Mục tiêu:** Chứng minh hệ thống vẫn hoạt động khi một node application bị chết.

**Thực thi:**
1.  **Kill `app_clone_1`:**
    ```bash
    docker stop app_clone_1
    ```
    > *Chờ khoảng 5-10s để Nginx health check phát hiện node chết.*

2.  **Gửi traffic kiểm tra:**
    ```bash
    bash test_traffic.sh
    ```
    > **Kết quả:** Traffic dồn 100% về `app_clone_2`. Session vẫn tăng đều.

3.  **Recovery (Khôi phục):**
    Trong khi script `test_traffic.sh` vẫn đang chạy (terminal khác), hãy start lại node chết:
    ```bash
    docker start app_clone_1
    ```
    > *Chờ khoảng 5-10s để Nginx health check detect node sống lại.*

**Kết quả Mong Đợi:**
1.  **Failover:** Khi `app_clone_1` chết, traffic chuyển mượt mà sang `app_clone_2`.
2.  **Recovery:** Khi `app_clone_1` sống lại, Nginx tự động điều phối traffic quay lại (Load balancing 50/50 trở lại).
3.  **Data Consistency:** Trong suốt quá trình Chết -> Sống lại, Session Counter không bao giờ bị reset.

| Request | Server Hitted | Status | Insight |
| :--- | :--- | :--- | :--- |
| ... | `app_clone_2` | 200 OK | **Failover**: Nginx loại bỏ node chết |
| ... | `app_clone_2` | 200 OK | **Failover**: Nginx loại bỏ node chết |
| ... | `app_clone_1` | 200 OK | **Recovery**: Nginx tự động thêm lại node sống |
| ... | `app_clone_2` | 200 OK | **Rebalancing**: Traffic chia đều trở lại |

---

## 🧹 Phase 3: Cleanup

Sau khi hoàn thành test, hãy dọn dẹp để trả lại tài nguyên.

```bash
# Stop containers và xóa volumes (để reset Redis data)
docker compose down -v

# Xóa file cookie tạm
rm -f /tmp/scalability_test_cookie.txt
```

---

## 🎯 Key Takeaways (What this proves)

1.  **Horizontal Scaling:** Hệ thống scale out bằng cách thêm App Clones mà không sửa code.
2.  **Statelessness:** Application server không giữ data, cho phép request nhảy tự do giữa các nodes.
3.  **High Availability:** Mất 1 node không làm sập hệ thống.
4.  **SPOF Trade-off:** Redis trở thành điểm yếu mới (Single Point of Failure) cần được xử lý ở production (Redis Cluster/Sentinel).