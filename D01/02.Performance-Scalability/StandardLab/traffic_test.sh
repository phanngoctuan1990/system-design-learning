#!/bin/bash

TARGET_URL="http://localhost:81/test/performance"

echo "============================================================"
echo "   LAB 1: KIỂM TRA PERFORMANCE (FAST FOR SINGLE USER)"
echo "============================================================"
# -n 1 request, -c 1 concurrency (Tải nhẹ)
echo "Chạy ab -n 1 -c 1 (1 request, 1 concurrent): Performance test"
ab -n 1 -c 1 $TARGET_URL

echo ""
echo "============================================================"
echo "   LAB 2: KIỂM TRA SCALABILITY (SLOW UNDER HEAVY LOAD)"
echo "============================================================"
# -n 200 requests, -c 50 concurrency (Tải nặng)
echo "Chạy ab -n 200 -c 50 (200 requests, 50 concurrent): Scalability test"
# Yêu cầu 50 kết nối đồng thời, nhưng chỉ có 2 Gunicorn worker
ab -n 200 -c 50 $TARGET_URL

echo ""
echo "--- Hoàn thành kiểm tra ---"