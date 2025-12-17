#!/bin/bash

# Thiết lập CURL để lưu và sử dụng cookie
COOKIE_FILE="/tmp/production_lab_cookie.txt"
URL="http://localhost:81/"

# ============================================================
# PART 1: Session Testing (với Cookie)
# Mục đích: Kiểm tra session tracking và Redis caching
# ============================================================
echo "============================================================"
echo "--- 1. Testing Session Tracking with Cookies (10 Requests) ---"
echo "============================================================"
echo "Sending requests to $URL while maintaining the session cookie..."
echo ""

# Khởi tạo hoặc xóa file cookie
rm -f $COOKIE_FILE

REQUESTS=10
for i in $(seq 1 $REQUESTS); do
    echo -n "Request $i: "
    # -s: silent
    # -c: lưu cookie vào file
    # -b: gửi cookie từ file
    response=$(curl -s -c $COOKIE_FILE -b $COOKIE_FILE $URL)
    
    # Extract thông tin từ JSON response
    visits=$(echo $response | grep -o '"visits":[0-9]*' | cut -d':' -f2)
    server=$(echo $response | grep -o '"server_id":"[^"]*"' | cut -d'"' -f4)
    
    echo "Server=$server, Visits=$visits"
    sleep 0.3
done

echo ""
echo "✅ Session test completed! Visits should increment from 1 to $REQUESTS"
echo ""

# ============================================================
# PART 2: Health Check
# ============================================================
echo "============================================================"
echo "--- 2. Health Check ---"
echo "============================================================"
curl -s ${URL}health | python3 -m json.tool 2>/dev/null || curl -s ${URL}health
echo ""

# ============================================================
# PART 3: Server Info
# ============================================================
echo "============================================================"
echo "--- 3. Server Info ---"
echo "============================================================"
curl -s ${URL}info | python3 -m json.tool 2>/dev/null || curl -s ${URL}info
echo ""

# ============================================================
# PART 4: Load Testing (với hey)
# Mục đích:
# 1. Tạo áp lực lên Load Balancer để kiểm tra thuật toán phân phối
# 2. Đo lường Throughput (Requests/sec) và Latency (độ trễ)
# ============================================================
echo "============================================================"
echo "--- 4. Load Testing with 'hey' ---"
echo "============================================================"

# Kiểm tra xem 'hey' có được cài đặt không
if command -v hey &> /dev/null; then
    DURATION=30s
    CONCURRENCY=50
    
    echo "Starting benchmark: C=$CONCURRENCY, D=$DURATION, URL=$URL"
    echo ""
    
    # -n 0: Không giới hạn tổng số requests (chạy theo thời gian)
    # -z $DURATION: Chạy trong khoảng thời gian DURATION
    # -c $CONCURRENCY: Số lượng workers chạy song song
    hey -z $DURATION -c $CONCURRENCY $URL
else
    echo "⚠️  'hey' is not installed. Skipping load test."
    echo "   Install with: brew install hey (macOS) or go install github.com/rakyll/hey@latest"
fi

echo ""
echo "============================================================"
echo "--- Test Complete! ---"
echo "============================================================"