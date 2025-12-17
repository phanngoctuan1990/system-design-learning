#!/bin/bash

# Thiết lập CURL để lưu và sử dụng cookie
COOKIE_FILE="/tmp/scalability_test_cookie.txt"
URL="http://localhost:81/"
REQUESTS=20

echo "--- 1. Testing Statelessness and Centralized State (10 Requests) ---"
echo "Sending requests to $URL while maintaining the session cookie..."

# Khởi tạo hoặc xóa file cookie
rm -f $COOKIE_FILE

for i in $(seq 1 $REQUESTS); do
    echo -n "Request $i: "
    # -s: silent
    # -c: lưu cookie
    # -b: gửi cookie
    curl -s -c $COOKIE_FILE -b $COOKIE_FILE $URL | grep -E 'Server Hitted|Session Counter' | tr -d '\n'
    echo ""
    sleep 0.5
done

echo "--- 2. Load Balancer Status ---"
echo "Checking Nginx logs to confirm requests are distributed..."