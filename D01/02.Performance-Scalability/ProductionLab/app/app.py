import time
import os
import sys
import signal
import json
from flask import Flask, jsonify
from datetime import datetime

# Performance setup: Simulate a task that takes 100ms (Performance Baseline)
TASK_LATENCY_SECONDS = 0.1 

app = Flask(__name__)
SERVICE_NAME = os.getenv('SERVICE_NAME', 'Unknown')
WORKER_ID = os.getpid()

# --- GRACEFUL SHUTDOWN HANDLER ---
# Bắt tín hiệu SIGTERM (do Docker/Kubernetes gửi khi shutdown)
def signal_handler(signum, frame):
    log_structured("INFO", f"[{SERVICE_NAME}] Received signal {signum}. Starting graceful shutdown...")
    # Thực hiện các tác vụ dọn dẹp (ví dụ: đóng kết nối DB, hoàn thành tác vụ đang chạy)
    time.sleep(2) # Giả định thời gian dọn dẹp
    log_structured("INFO", f"[{SERVICE_NAME}] Shutdown complete. Exiting.")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def log_structured(level, message, **kwargs):
    """Sử dụng structured logging thay vì print"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "level": level,
        "service": SERVICE_NAME,
        "pid": WORKER_ID,
        "message": message
    }
    log_entry.update(kwargs)
    print(json.dumps(log_entry), file=sys.stderr)

@app.route('/test/baseline', methods=['GET'])
@app.route('/test/optimized', methods=['GET'])
@app.route('/test/failover', methods=['GET'])
def simulated_work():
    start_time = time.time()
    
    # 1. Verify resource availability before starting expensive task (Fail Fast Principle)
    # Trong môi trường thực tế, đây là nơi kiểm tra kết nối DB/Cache.
    if WORKER_ID % 2 == 0:
        log_structured("DEBUG", "Simulating worker processing task.", endpoint=app.url_map.bind("").match(app.request.path))
    
    # Simulate IO/CPU work
    time.sleep(TASK_LATENCY_SECONDS) 
    
    end_time = time.time()
    latency_ms = round((end_time - start_time) * 1000, 2)
    
    log_structured("INFO", "Request processed successfully.", latency_ms=latency_ms)

    return jsonify({
        "status": "ok", 
        "service": SERVICE_NAME,
        "worker_pid": WORKER_ID,
        "latency_ms": latency_ms
    }), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint cho Healthcheck"""
    # Trong môi trường production, health check phải bao gồm cả kiểm tra down-stream dependencies
    return jsonify({"status": "healthy", "service": SERVICE_NAME}), 200

if __name__ == '__main__':
    log_structured("INFO", f"Starting service {SERVICE_NAME} with PID {WORKER_ID}")
    app.run(host='0.0.0.0', port=8000)