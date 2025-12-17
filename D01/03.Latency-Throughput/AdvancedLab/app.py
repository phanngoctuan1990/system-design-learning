from flask import Flask, jsonify
import time
import os

app = Flask(__name__)
SERVICE_NAME = os.getenv('SERVICE_NAME', 'DEFAULT')
DELAY_MS = int(os.getenv('SIMULATED_DELAY_MS', 0))

@app.route('/process', methods=['GET', 'POST'])
def process_data():
    start_req = time.time()
    time.sleep(DELAY_MS / 1000.0) 
    
    # Return measured latency for verification
    end_req = time.time()
    
    return jsonify({
        "status": "success",
        "service": SERVICE_NAME,
        "action": f"{SERVICE_NAME} processed data",
        "simulated_latency_ms": DELAY_MS,
        "actual_processing_time_ms": (end_req - start_req) * 1000
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)