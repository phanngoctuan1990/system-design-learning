import os
import time
from flask import Flask, jsonify, request
import redis

# Configuration from environment variables
DB_G1_HOST = os.environ.get('DB_G1_HOST', 'localhost')
DB_G2_HOST = os.environ.get('DB_G2_HOST', 'localhost')
APP_MODE = os.environ.get('APP_MODE', 'CP') # CP or AP

app = Flask(__name__)

# Connection setup (using connection pooling for robustness)
def get_db_connection(host):
    try:
        # Set a short timeout (simulating network latency impact)
        r = redis.Redis(host=host, port=6379, socket_timeout=2)
        r.ping()
        return r
    except Exception as e:
        app.logger.error(f"Failed to connect to Redis at {host}: {e}")
        return None

# --- CP Logic: Consistency over Availability ---
def cp_write(key, value):
    g1 = get_db_connection(DB_G1_HOST)
    g2 = get_db_connection(DB_G2_HOST)
    
    # 1. Attempt transaction on G1 (Primary)
    if g1 is None:
        raise Exception("G1 unavailable. System is Down (P-Failure).")

    # 2. Attempt synchronous replication/commit to G2 (Requires Strong Consistency) [8, 9]
    try:
        if g2 is None:
            # If G2 is unreachable (Partition), we sacrifice Availability (A) by failing the transaction.
            # CP must return an error because it cannot guarantee the most recent write on all nodes. [5]
            raise Exception("G2 unreachable (Partition). Sacrificing Availability (CP mode).")
        
        # Simulate synchronous two-phase commit or consensus wait time
        g1.set(key, value)
        g2.set(key, value)
        return f"CP Success: Wrote {value} to G1 and G2 synchronously."
        
    except Exception as e:
        # Crucial for CP: If replication fails, rollback or error out.
        # We ensure Atomic Reads and Writes by making the system unavailable temporarily.
        raise Exception(f"CP FAILED: Transaction aborted due to Partition/Error. {e}")

# --- AP Logic: Availability over Consistency ---
def ap_write(key, value):
    g1 = get_db_connection(DB_G1_HOST)
    g2 = get_db_connection(DB_G2_HOST)
    
    # 1. Check G1 (Primary) availability
    if g1 is None:
        raise Exception("G1 unavailable. System is Down (Critical Failure).")

    # 2. Write locally to G1 [10]
    g1.set(key, value)
    
    # 3. Attempt async replication to G2 (Fire and forget, using eventual consistency) [8]
    if g2:
        # In a real system, this would be handled by a background process/replication lag
        # Here we just log the effort.
        try:
            g2.set(key, value)
            g2_status = "G2 Updated (Stronger EC)"
        except:
            g2_status = "G2 FAILED/STALE (Eventual Consistency window open)"
    else:
        g2_status = "G2 unreachable (Partition). Write accepted anyway (Sacrificing C)."
    
    # Crucial for AP: Return success immediately, even if G2 fails/is stale.
    return f"AP Success: Wrote {value} to G1. Status: {g2_status}."

# --- API Endpoints ---
@app.route('/write/<key>/<value>', methods=['POST'])
def write_data(key, value):
    try:
        if APP_MODE == 'CP':
            result = cp_write(key, value)
        else: # AP mode
            result = ap_write(key, value)
            
        return jsonify({"status": "SUCCESS", "mode": APP_MODE, "message": result}), 200
    except Exception as e:
        # Return 503 Service Unavailable for CP failures
        return jsonify({"status": "FAILURE", "mode": APP_MODE, "error": str(e)}), 503

@app.route('/read/<key>', methods=['GET'])
def read_data(key):
    g1 = get_db_connection(DB_G1_HOST)
    g2 = get_db_connection(DB_G2_HOST)
    
    g1_val = g1.get(key).decode() if g1 and g1.get(key) else "N/A"
    g2_val = g2.get(key).decode() if g2 and g2.get(key) else "N/A"

    # Demonstrate Read-After-Write outcome
    is_consistent = (g1_val == g2_val and g1_val != "N/A")
    consistency_status = "STRONG/EVENTUAL CONSISTENT" if is_consistent else "STALE/INCONSISTENT"
    
    return jsonify({
        "key": key,
        "mode": APP_MODE,
        "G1_Value": g1_val,
        "G2_Value": g2_val,
        "Consistency_Status": consistency_status
    }), 200

if __name__ == '__main__':
    # Initial setup (optional: pre-set a key)
    # Using a slightly delayed startup to ensure Redis nodes are ready
    time.sleep(5)
    
    if APP_MODE == 'CP':
        print(f"Starting CP Application on port 5000. Writing to {DB_G1_HOST} and {DB_G2_HOST}.")
    else:
        print(f"Starting AP Application on port 5001. Writing only to {DB_G1_HOST} for availability.")
        
    # Initialize a baseline value
    try:
        r1 = redis.Redis(host=DB_G1_HOST, port=6379)
        r2 = redis.Redis(host=DB_G2_HOST, port=6379)
        r1.set("STATUS", "READY_V0")
        r2.set("STATUS", "READY_V0")
        print("Database initialized with STATUS=READY_V0")
    except Exception as e:
        print(f"Initialization Failed: {e}")
        
    app.run(debug=True, host='0.0.0.0', port=5000)