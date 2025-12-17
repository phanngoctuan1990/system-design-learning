import time
import os
from flask import Flask, jsonify
import random

# Giả định Performance: Mỗi request mất 100ms (100ms Latency)
TASK_LATENCY_SECONDS = 0.1

app = Flask(__name__)
SERVICE_NAME = os.getenv('SERVICE_NAME', 'Unknown')
WORKER_ID = os.getpid()

@app.route('/test/baseline', methods=['GET'])
@app.route('/test/optimized', methods=['GET'])
@app.route('/test/failover', methods=['GET'])
def simulated_work():
    start_time = time.time()
    
    # Simulate IO/CPU work
    time.sleep(TASK_LATENCY_SECONDS) 
    
    end_time = time.time()
    
    return jsonify({
        "status": "ok", 
        "service": SERVICE_NAME,
        "worker_pid": WORKER_ID,
        "simulated_latency_ms": TASK_LATENCY_SECONDS * 1000,
        "actual_response_time_ms": round((end_time - start_time) * 1000, 2)
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)