from flask import Flask, jsonify
import time
import os
import signal
import threading

app = Flask(__name__)
NODE_NAME = os.environ.get('NODE_NAME', 'UNKNOWN')

# Biến cờ để kiểm soát việc shutdown
SHUTDOWN_REQUESTED = False

# Handler cho tín hiệu SIGTERM (Gunicorn gửi khi cần shutdown)
def handle_sigterm(signum, frame):
    global SHUTDOWN_REQUESTED
    print(f"[{NODE_NAME}] Received SIGTERM. Initiating graceful shutdown.")
    SHUTDOWN_REQUESTED = True

# Đăng ký handler (chỉ Gunicorn mới cần)
signal.signal(signal.SIGTERM, handle_sigterm)

@app.route('/')
def handle_request():
    if SHUTDOWN_REQUESTED:
        # Nếu đang trong quá trình shutdown, từ chối request mới (hoặc trả về 503)
        return jsonify({"status": "shutting down", "node": NODE_NAME}), 503

    # Mô phỏng độ trễ xử lý nghiệp vụ (giữ nguyên để benchmark)
    time.sleep(0.5) 
    return jsonify({
        "status": "ok",
        "message": f"Response from {NODE_NAME}",
        "time": time.time()
    })

@app.route('/deep_health')
def deep_health_check():
    # Mô phỏng kiểm tra Database/Cache (độ trễ nhỏ)
    try:
        time.sleep(0.05) 
        # Nếu có database, đây là nơi kiểm tra connection pool
        return jsonify({"status": "healthy", "node": NODE_NAME}), 200
    except Exception as e:
        # Nếu DB lỗi, trả về lỗi 503
        return jsonify({"status": "unhealthy", "error": str(e)}), 503

# Chỉ chạy khi dùng Flask tích hợp (chúng ta dùng Gunicorn)
# if __name__ == '__main__':
#    app.run(host='0.0.0.0', port=8000)