import os
import time
from flask import Flask, jsonify, request
import redis

DB_G1_HOST = os.environ.get('DB_G1_HOST')
DB_G2_HOST = os.environ.get('DB_G2_HOST')
APP_MODE = os.environ.get('APP_MODE', 'CP')

app = Flask(__name__)
# Thiết lập timeout ngắn để mô phỏng sự cố mạng/độ trễ.
# Trong môi trường phân tán, không thể phân biệt Slow Machine và Partition [1, 2].
TIMEOUT = 0.1 

def get_db_connection(host):
    try:
        r = redis.Redis(host=host, port=6379, socket_timeout=TIMEOUT, socket_connect_timeout=TIMEOUT)
        r.ping()
        return r
    except Exception:
        return None

# --- Logic CP: Consistency Priority ---
# Phải chờ G1 VÀ G2 thành công. Bất kỳ lỗi nào (kể cả timeout) sẽ hủy giao dịch.
def cp_write(key, value):
    g1 = get_db_connection(DB_G1_HOST)
    g2 = get_db_connection(DB_G2_HOST)
    
    if g1 is None or g2 is None:
        # CP must return an error because it cannot guarantee the most recent write on all nodes [3, 4].
        raise Exception("Consistency Failure: One or both nodes unreachable (Partition detected). Sacrificing Availability (A).")
    
    # Simulate synchronous, atomic transaction (Two-Phase Commit approximation)
    g1.set(key, value)
    g2.set(key, value)
    return "CP Success: Strong Consistency maintained."

# --- Logic AP: Availability Priority ---
# Chỉ cần G1 thành công. G2 là best effort/asynchronous.
def ap_write(key, value):
    g1 = get_db_connection(DB_G1_HOST)
    
    if g1 is None:
        # Critical failure: Primary node down.
        raise Exception("Critical Failure: Primary G1 node is down.")

    # Write locally to G1 first
    g1.set(key, value)
    
    # Best effort replication to G2 (Eventual Consistency mechanism)
    g2_status = "Skipped"
    try:
        g2 = get_db_connection(DB_G2_HOST)
        if g2:
            g2.set(key, value)
            g2_status = "G2 Replicated"
        else:
            # G2 is down (Partition). Write accepted anyway, leading to stale data on G2 [3].
            g2_status = "G2 Unreachable/Stale"
    except:
        g2_status = "G2 Replication Failed"

    # Crucial for AP: Return success immediately [5].
    return f"AP Success: High Availability maintained. G2 Status: {g2_status}"

# API Endpoints (Read and Write)
@app.route('/write/<key>/<value>', methods=['POST'])
def write_data(key, value):
    try:
        if APP_MODE == 'CP':
            result = cp_write(key, value)
        else:
            result = ap_write(key, value)
            
        return jsonify({"status": "SUCCESS", "mode": APP_MODE, "message": result}), 200
    except Exception as e:
        # Return 503 Service Unavailable for CAP theorem sacrifice.
        return jsonify({"status": "FAILURE", "mode": APP_MODE, "error": str(e)}), 503

# Read endpoint for verification
@app.route('/read/<key>', methods=['GET'])
def read_data(key):
    g1 = get_db_connection(DB_G1_HOST)
    g2 = get_db_connection(DB_G2_HOST)
    
    g1_val = g1.get(key).decode() if g1 and g1.get(key) else "N/A"
    g2_val = g2.get(key).decode() if g2 and g2.get(key) else "N/A"

    is_consistent = (g1_val == g2_val and g1_val != "N/A")
    consistency_status = "CONSISTENT" if is_consistent else "INCONSISTENT/STALE"
    
    return jsonify({
        "key": key, "mode": APP_MODE, "G1_Value": g1_val, "G2_Value": g2_val,
        "Consistency_Status": consistency_status
    }), 200

if __name__ == '__main__':
    time.sleep(5) # Give DBs time to start
    app.run(host='0.0.0.0', port=5000)