#!/bin/bash
# ============================================
# Chaos Engineering Lab: Replication Lag Demo
# ============================================
#
# Script này chứng minh 2 scenarios quan trọng của async replication:
#
# TEST CASE 1: Happy Path
#   - Chứng minh async replication HOẠT ĐỘNG khi có đủ thời gian
#   - 1000 records, chờ 3s → 100% replication success
#
# TEST CASE 2: Partial Data Loss
#   - Chứng minh PARTIAL LOSS với dataset lớn
#   - Kill master ĐANG INSERT → partial replication
#   - 100K records, kill sau 5s → ~30-50% data loss
#
# Bài học: High Availability ≠ Data Durability
# ============================================

set -e

echo "=========================================="
echo "🧪 Chaos Engineering Lab: Data Loss Demo"
echo "=========================================="
echo ""

# Bước 1: Khởi động
echo "📦 Bước 1: Khởi động môi trường..."
docker compose up -d
echo "⏳ Chờ slave khởi tạo (10s)..."
sleep 10

# Bước 2: Sanity Check
echo ""
echo "🔍 Bước 2: Kiểm tra replication..."
docker exec db-slave psql -U admin -d appdb -c "SELECT pg_is_in_recovery();" | grep -q "t" && echo "✅ Slave đang ở recovery mode" || echo "❌ Slave KHÔNG ở recovery mode"

docker exec db-master psql -U admin -d appdb -c "INSERT INTO transactions (value) VALUES ('Record A - Baseline');"
sleep 2
docker exec db-slave psql -U admin -d appdb -c "SELECT value FROM transactions WHERE value LIKE 'Record A%';" | grep -q "Baseline" && echo "✅ Replication hoạt động" || echo "❌ Replication KHÔNG hoạt động"

# ============================================
# TEST CASE 1: Replication thành công (Happy Path)
# ============================================
echo ""
echo "=========================================="
echo "📗 TEST CASE 1: Replication Thành Công"
echo "=========================================="
echo ""
echo "🎯 Mục tiêu: Chứng minh async replication hoạt động khi có đủ thời gian"
echo ""

docker cp high_write_load.sql db-master:/high_write_load.sql
echo "🚀 Bắt đầu insert 1000 records..."
docker exec db-master psql -U admin -d appdb -f /high_write_load.sql

echo "⏳ Chờ replication hoàn tất (3s)..."
sleep 3

MASTER_COUNT=$(docker exec db-master psql -U admin -d appdb -t -c "SELECT COUNT(*) FROM transactions WHERE value LIKE 'Transaction-%';" | xargs)
SLAVE_COUNT=$(docker exec db-slave psql -U admin -d appdb -t -c "SELECT COUNT(*) FROM transactions WHERE value LIKE 'Transaction-%';" | xargs)

echo ""
echo "📊 Kết quả Test Case 1:"
echo "   Master: $MASTER_COUNT records"
echo "   Slave:  $SLAVE_COUNT records"

if [ "$MASTER_COUNT" -eq "$SLAVE_COUNT" ] && [ "$SLAVE_COUNT" -eq 1000 ]; then
    echo "   ✅ PASS: Replication hoạt động hoàn hảo (100%)"
else
    echo "   ⚠️  WARNING: Có vấn đề với replication"
fi


# ============================================
# TEST CASE 2: Partial Data Loss (Large Dataset)
# ============================================
echo ""
echo "=========================================="
echo "📘 TEST CASE 2: Partial Data Loss"
echo "=========================================="
echo ""
echo "🎯 Mục tiêu: Chứng minh DATA LOSS khi master chết trước khi replicate xong"
echo ""
echo "📋 Chiến lược:"
echo "   1. Bơm tải liên tục (100K records) → tạo replication lag tự nhiên"
echo "   2. Kill master + đồng thời ghi lại số records trong master"
echo "   3. Check slave để đo data loss"
echo ""

# Restart containers để có môi trường sạch (vì Test Case 1 và các hoạt động trước đó có thể ảnh hưởng)
echo "🔄 Restart containers để chuẩn bị môi trường mới..."
docker compose down -v > /dev/null 2>&1
sleep 2
docker compose up -d > /dev/null 2>&1
echo "⏳ Chờ containers khởi động (20s)..."
sleep 20
echo "✅ Môi trường đã sẵn sàng"
echo ""

# ============================================
# Bước 1: Bơm tải liên tục để tạo replication lag
# ============================================
docker cp massive_write_load.sql db-master:/massive_write_load.sql
echo "🚀 Bước 1: Bắt đầu bơm tải liên tục..."
echo "   - 100,000 transactions (mỗi transaction riêng biệt)"
echo "   - Delay 0.5ms/transaction = ~50 giây total"
echo "   - Tạo replication lag tự nhiên"
echo ""

# Chạy trong background để có thể kill giữa chừng
docker exec db-master bash -c "psql -U admin -d appdb -f /massive_write_load.sql" &
SQL_PID=$!

# Chờ 5 giây để tạo workload đủ lớn (~10K records)
echo "⏳ Đang bơm tải... (chờ 5s để tạo replication lag)"
sleep 5

# ============================================
# Bước 2: Kill master + capture final count
# ============================================
echo ""
echo "🔥 Bước 2: Kill master + capture final count..."

# QUAN TRỌNG: Query slave TRƯỚC, master SAU để tránh timing skew
# Nếu query master trước → master insert thêm → slave có thể > master (sai!)
SLAVE_FINAL=$(docker exec db-slave psql -U admin -d appdb -t -c "SELECT COUNT(*) FROM transactions WHERE value LIKE 'BigTransaction-%';" 2>/dev/null | xargs || echo "0")

# Query master SAU để có snapshot mới nhất
MASTER_FINAL=$(docker exec db-master psql -U admin -d appdb -t -c "SELECT COUNT(*) FROM transactions WHERE value LIKE 'BigTransaction-%';" 2>/dev/null | xargs || echo "0")

# Kill master NGAY SAU KHI query
docker kill db-master
kill $SQL_PID 2>/dev/null || true  # Kill background SQL process

echo "   ✅ Master killed!"
echo "   📊 Master final count: $MASTER_FINAL records"
echo "   📊 Slave final count: $SLAVE_FINAL records"

# Promote slave lên master mới
echo ""
echo "🔄 Promote Slave lên Master mới..."

# Check if slave is in standby mode
IS_STANDBY=$(docker exec db-slave psql -U admin -d appdb -t -c "SELECT pg_is_in_recovery();" 2>/dev/null | xargs || echo "f")

if [ "$IS_STANDBY" = "t" ]; then
    docker exec -u postgres db-slave pg_ctl promote -D /var/lib/postgresql/data
    sleep 5
    echo "✅ Slave promoted successfully"
else
    echo "⚠️  Slave is already promoted (not in standby mode)"
    echo "   Continuing with analysis..."
fi

# ============================================
# Bước 3: Phân tích data loss
# ============================================
echo ""
echo "📊 Bước 3: Phân tích data loss..."

# Verify slave count sau khi promote (có thể khác SLAVE_FINAL do replication tiếp tục)
SLAVE_AFTER_PROMOTE=$(docker exec db-slave psql -U admin -d appdb -t -c "SELECT COUNT(*) FROM transactions WHERE value LIKE 'BigTransaction-%';" 2>/dev/null | xargs || echo "0")

# Tính data loss = những gì master đã insert nhưng slave chưa replicate (tại thời điểm kill)
# Dùng SLAVE_FINAL (capture gần đồng thời với MASTER_FINAL) để so sánh chính xác
DATA_LOSS=$((MASTER_FINAL - SLAVE_FINAL))

echo ""
echo "=========================================="
echo "📊 KẾT QUẢ TEST CASE 2"
echo "=========================================="
echo ""
echo "📈 Trạng thái khi master bị kill:"
echo "   Master: $MASTER_FINAL records (đã insert)"
echo "   Slave:  $SLAVE_FINAL records (đã replicate)"
echo ""
echo "📉 Sau khi promote slave:"
echo "   New Master: $SLAVE_AFTER_PROMOTE records"
echo "   Data Loss:  $DATA_LOSS records"
echo ""

if [ "$MASTER_FINAL" -gt 0 ]; then
    LOSS_PERCENT=$((DATA_LOSS * 100 / MASTER_FINAL))
    SURVIVAL_PERCENT=$((100 - LOSS_PERCENT))
    echo "   📊 Data Loss: ${LOSS_PERCENT}%"
    echo "   ✅ Data Survived: ${SURVIVAL_PERCENT}%"
fi

echo ""
if [ "$DATA_LOSS" -gt 0 ] && [ "$DATA_LOSS" -lt "$MASTER_FINAL" ]; then
    echo "   ✅ PASS: Đã chứng minh PARTIAL data loss!"
    echo ""
    echo "   💡 Giải thích:"
    echo "      - Master đã insert $MASTER_FINAL records tại thời điểm bị kill"
    echo "      - Slave chỉ replicate được $SLAVE_FINAL records tại thời điểm đó"
    echo "      - Mất $DATA_LOSS records do replication lag"
    echo "      - Đây là scenario thực tế: master fail khi đang có workload cao"
elif [ "$DATA_LOSS" -eq 0 ]; then
    echo "   ⚠️  WARNING: Không có data loss"
    echo "   💡 Replication quá nhanh hoặc cần tăng workload"
elif [ "$DATA_LOSS" -eq "$MASTER_FINAL" ]; then
    echo "   ⚠️  WARNING: 100% data loss"
    echo "   💡 Killed quá sớm - chưa có transaction nào replicate"
fi

echo ""
echo "=========================================="
echo "🎓 KẾT LUẬN"
echo "=========================================="
echo "Test Case 1: Chứng minh async replication HOẠT ĐỘNG"
echo "Test Case 2: Chứng minh PARTIAL DATA LOSS khi master fail giữa chừng"
echo ""
echo "💡 Bài học: High Availability ≠ Data Durability"
echo "   - Master có thể die BẤT CỨ LÚC NÀO (kể cả đang có workload cao)"
echo "   - Slave chỉ có data đã được replicate → mất data chưa replicate"
echo "   - Async replication: fast nhưng có risk window"
echo "   - Cần sync replication hoặc backup để đảm bảo durability"
echo ""
echo "🧹 Để dọn dẹp, chạy: docker compose down -v"
docker compose down -v > /dev/null 2>&1
