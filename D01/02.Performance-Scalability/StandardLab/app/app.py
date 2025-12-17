import time
import os
import sys
from flask import Flask, jsonify
import redis

TASK_LATENCY_MS = 100
TASK_LATENCY_SECONDS = TASK_LATENCY_MS / 1000.0

app = Flask(__name__)

try:
    redis_client = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, decode_responses=True)
    redis_client.ping()
    print("Connected to Redis successfully!")
except Exception as e:
    print(f"Could not connect to Redis: {e}", file=sys.stderr)
    # Thoát nếu không kết nối được Redis (để đảm bảo tính Shared State)
    sys.exit(1)

@app.route("/test/performance", methods=["GET"])
def high_performance_low_scalability():
    """Endpoint mô phỏng tác vụ đòi hỏi CPU/IO, chậm 100ms."""
    
    start_time = time.time()

    # 1. Simulate IO/CPU work (High Performance)
    time.sleep(TASK_LATENCY_SECONDS)

    # 2. Simulate Shared State access (Contention)
    try:
        current_count = redis_client.incr('total_requests')
    except Exception:
        current_count = "ERROR"

    end_time = time.time()

    return jsonify({
        "status": "ok", 
        "worker_id": os.getpid(),
        "simulated_latency_ms": TASK_LATENCY_MS,
        "actual_response_time_ms": round((end_time - start_time) * 1000, 2),
        "total_requests": current_count
    }), 200

@app.route('/test/fast_ping', methods=['GET'])
def fast_ping():
    """Endpoint rất nhanh, chứng minh hệ thống không có Performance problem."""
    return "PONG", 200

if __name__ == '__main__':
    # Gunicorn sẽ override phần này
    app.run(host='0.0.0.0', port=8000)