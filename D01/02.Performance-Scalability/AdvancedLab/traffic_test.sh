#!/bin/bash
# Dùng ab (Apache Benchmark). Cài đặt trên máy Host: `sudo apt install apache2-utils`

CONCURRENCY=50  # Số người dùng đồng thời
REQUESTS=2000   # Tổng số request
DELAY=1         # Dừng 1 giây giữa các bài test

echo "--- BẮT ĐẦU LAB PERFORMANCE VS SCALABILITY ---"
echo "Cấu hình tải: ${REQUESTS} requests, ${CONCURRENCY} concurrent users."
echo "--------------------------------------------------------"

function run_test() {
    TEST_CASE=$1
    ENDPOINT=$2
    
    echo "CASE $TEST_CASE: Testing $ENDPOINT..."
    
    # Chạy ab và lọc ra metrics quan trọng: P95 Latency và Throughput (Req/sec)
    ab -n $REQUESTS -c $CONCURRENCY "http://localhost:81/$ENDPOINT" | grep -E 'Time per request|95%'
    
    echo "--------------------------------------------------------"
    sleep $DELAY
}

# CASE A: BASELINE (Simple Round Robin)
# Tổng tài nguyên: 4 workers (App1: 3 worker, App2: 1 worker)
run_test "A (Baseline)" "test/baseline"

# CASE B: OPTIMIZED (Weighted Round Robin)
# Tổng tài nguyên: 4 workers. Sử dụng Weighted LB (3:1)
run_test "B (Optimized)" "test/optimized"

# CASE C: FAILOVER (Stability Test)
# Tổng tài nguyên: 4 workers, nhưng App2 bị đánh dấu là DOWN. Chỉ 3 workers hoạt động.
run_test "C (Failover)" "test/failover"