from flask import Flask, jsonify
import time
import os

app = Flask(__name__)
NODE_NAME = os.environ.get('NODE_NAME', 'UNKNOWN')

@app.route('/')
def hello():
    # Mô phỏng độ trễ xử lý nghiệp vụ 500ms
    time.sleep(0.5) 
    return jsonify({
        "status": "ok",
        "message": f"Response from {NODE_NAME}",
        "time": time.time()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)