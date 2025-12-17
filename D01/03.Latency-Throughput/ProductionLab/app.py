from flask import Flask, jsonify
import time
import os
import signal
import sys
import logging

# Setup structured logging
logging.basicConfig(level=logging.INFO, 
                    format='{"time": "%(asctime)s", "level": "%(levelname)s", "service": "%(name)s", "message": "%(message)s"}')
logger = logging.getLogger("APP_SERVER")

# Configuration from Environment Variables
SERVICE_NAME = os.getenv('SERVICE_NAME', 'DEFAULT')
DELAY_MS = int(os.getenv('SIMULATED_DELAY_MS', 0))
GRACEFUL_SHUTDOWN_DELAY_S = 3 # Giả lập thời gian dọn dẹp tài nguyên
IS_RUNNING = True

app = Flask(__name__)

# --- Graceful Shutdown Logic ---
def shutdown_handler(signum, frame):
    """Xử lý tín hiệu SIGTERM/SIGINT (Graceful Shutdown)"""
    global IS_RUNNING
    IS_RUNNING = False
    logger.info(f"Received signal {signum}. Starting graceful shutdown for {SERVICE_NAME}...")
    
    # Mô phỏng quá trình dọn dẹp tài nguyên (đóng DB connections, Flush buffer, v.v.)
    time.sleep(GRACEFUL_SHUTDOWN_DELAY_S) 
    logger.info(f"Graceful shutdown complete for {SERVICE_NAME}. Exiting.")
    sys.exit(0)

# Đăng ký handlers cho các tín hiệu dừng
signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint Healthcheck: Trả về 503 nếu đang trong quá trình shutdown"""
    if not IS_RUNNING:
        return jsonify({"status": "shutdown_in_progress"}), 503
    return jsonify({"status": "ok", "service": SERVICE_NAME}), 200

@app.route('/process', methods=['GET', 'POST'])
def process_data():
    if not IS_RUNNING:
        logger.warning(f"Request denied during shutdown: {SERVICE_NAME}")
        return jsonify({"status": "service_unavailable"}), 503

    start_req = time.time()
    # Thực hiện độ trễ mô phỏng (Latency core)
    time.sleep(DELAY_MS / 1000.0) 
    end_req = time.time()
    
    actual_latency = (end_req - start_req) * 1000
    
    logger.info(f"Processed request. Latency: {actual_latency:.2f}ms")
    
    return jsonify({
        "status": "success",
        "service": SERVICE_NAME,
        "simulated_delay_ms": DELAY_MS,
        "actual_processing_time_ms": actual_latency
    })

if __name__ == '__main__':
    logger.info(f"Starting {SERVICE_NAME} with {DELAY_MS}ms delay.")
    app.run(host='0.0.0.0', port=5000)