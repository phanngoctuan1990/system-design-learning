#!/bin/bash

# Thời gian chạy test (30 giây)
DURATION=30s

# Số lượng connections đồng thời (50 users cùng lúc)
# Tương đương với việc có 50 tab trình duyệt gửi request liên tục
CONCURRENCY=50

# URL của Load Balancer (Nginx)
URL="http://localhost:81/"

echo "--- Starting Benchmark: C=$CONCURRENCY, D=$DURATION, URL=$URL ---"

# Sử dụng công cụ 'hey' để bắn tải (Load Testing)
# -n 0: Không giới hạn tổng số requests (chạy theo thời gian)
# -z $DURATION: Chạy trong khoảng thời gian DURATION
# -c $CONCURRENCY: Số lượng workers chạy song song
#
# Mục đích:
# 1. Tạo áp lực lên Load Balancer để kiểm tra thuật toán phân phối (Round Robin vs Least Conn)
# 2. Đo lường Throughput (Requests/sec) và Latency (độ trễ)
hey -n 0 -z $DURATION -c $CONCURRENCY $URL
# 95% in 0.0143 secs
# Requests/sec: 5195.6727