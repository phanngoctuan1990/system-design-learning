#!/bin/bash
# Dùng ab (Apache Benchmark)

CONCURRENCY=50
REQUESTS=2000
DELAY=3 

echo "--- BẮT ĐẦU LAB PERFORMANCE VS SCALABILITY (PRODUCTION-READY) ---"
echo "Cấu hình tải: ${REQUESTS} requests, ${CONCURRENCY} concurrent users."
echo "--------------------------------------------------------"

function run_test() {
    TEST_CASE=$1
    ENDPOINT=$2
    
    echo "CASE $TEST_CASE: Testing $ENDPOINT..."
    
    # Chạy ab và lọc ra metrics quan trọng: P95 Latency và Throughput (Req/sec)
    ab -n $REQUESTS -c $CONCURRENCY "http://localhost/$ENDPOINT" | grep -E 'Time per request|95%'
    
    echo "--------------------------------------------------------"
    sleep $DELAY
}

run_test "A (Baseline - Simple RR)" "test/baseline"
run_test "B (Optimized - Weighted RR)" "test/optimized"
run_test "C (Failover - 1 Node Down)" "test/failover"