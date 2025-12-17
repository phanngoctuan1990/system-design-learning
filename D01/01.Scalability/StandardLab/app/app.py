import time
import os
import sys
import uuid
from flask import Flask, request, make_response
import redis

app = Flask(__name__)

# Kết nối tới Redis, sử dụng service name 'redis' trong Docker Compose
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")

# Lấy Server ID từ biến môi trường
SERVER_ID = os.getenv("SERVER_ID", "unknown")

try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    redis_client.ping()
    print("Connected to Redis successfully!")
except Exception as e:
    print(f"Could not connect to Redis: {e}", file=sys.stderr)
    sys.exit(1)

@app.route("/")
def index():
    # 1. Lấy Session ID từ Cookie
    session_id = request.cookies.get("session_id")

    # 2. Xử lý logic Session
    if not session_id:
        # Nếu chưa có session, tạo ID mới và lưu trữ counter = 1
        session_id = str(uuid.uuid4())
        redis_client.set(session_id, 1)
        visit_count = 1
        source = "New Session Created"
    else:
        # Nếu có session, tăng counter lên 1. Thao tác này là Atomic.
        try:
            visit_count = redis_client.incr(session_id)
            source = "Existing Session Loaded"
        except Exception as e:
            # Xử lý lỗi nếu Redis không kết nối được
            visit_count = -1
            source = f"Error connecting to Redis: {e}"

    # 3. Tạo response với Session ID và counter
    response_html = f"""
    <html>
    <head><title>Scalability Lab</title></head>
    <body>
        <h1>Horizontal Scaling Demo</h1>
        <p><strong>Server Hitted:</strong> {SERVER_ID}</p>
        <p><strong>Session ID:</strong> {session_id}</p>
        <p><strong>Session Counter (from Redis):</strong> {visit_count}</p>
        <p><strong>Status:</strong> {source}</p>
    </body>
    </html>
    """
    response = make_response(response_html)
    # Gán session_id vào Cookie để trình duyệt gửi lại lần sau
    # time.sleep(1)

    response.set_cookie("session_id", session_id, max_age=3600) # 3600s = 1 hour
    return response

@app.route("/slow")
def slow():
    time.sleep(5)
    response_html = f"""
    <html>
    <head><title>Scalability Lab</title></head>
    <body>
        <h1>Slow Response</h1>
        <p><strong>Server Hitted:</strong> {SERVER_ID}</p>
    </body>
    </html>
    """
    response = make_response(response_html)
    return response