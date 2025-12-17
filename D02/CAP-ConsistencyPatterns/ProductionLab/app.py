import os
import time
import redis
import json
import logging
import signal
import sys
from flask import Flask, jsonify, request, session
from threading import Lock
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# --- Configuration & Setup ---
DB_G1_HOST = os.environ.get('DB_G1_HOST', 'localhost')
DB_G2_HOST = os.environ.get('DB_G2_HOST', 'localhost')
APP_MODE = os.environ.get('APP_MODE', 'CP')
TIMEOUT = float(os.environ.get('NETWORK_TIMEOUT_SEC', 0.2)) 
APP_PORT = int(os.environ.get('FLASK_RUN_PORT', 5000))
MAX_STALENESS_MS = float(os.environ.get('MAX_STALENESS_MS', 500))
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'hardening_secret_key')

# Configure logging with level from env
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format='%(message)s'
)
logger = logging.getLogger('system_log')

# --- Prometheus Metrics ---
request_count = Counter('app_requests_total', 'Total requests', ['mode', 'operation', 'status'])
request_latency = Histogram('app_request_latency_seconds', 'Request latency', ['mode', 'operation'])
circuit_breaker_state = Gauge('circuit_breaker_state', 'Circuit breaker state (0=CLOSED, 1=HALF_OPEN, 2=OPEN)', ['target'])
staleness_gauge = Gauge('data_staleness_ms', 'Data staleness in milliseconds', ['node'])
db_connection_failures = Counter('db_connection_failures_total', 'Database connection failures', ['host'])

# --- Circuit Breaker State ---
circuit_breaker = {
    'db_g2': {
        'failures': 0,
        'last_failure_time': 0,
        'state': 'CLOSED',
        'threshold': int(os.environ.get('CIRCUIT_BREAKER_THRESHOLD', 3)),
        'timeout': int(os.environ.get('CIRCUIT_BREAKER_TIMEOUT', 10))
    }
}
cb_lock = Lock()

# --- Helper Functions ---
def check_circuit_breaker(target):
    """Check if circuit breaker allows connection attempt"""
    with cb_lock:
        cb = circuit_breaker[target]
        if cb['state'] == 'OPEN':
            if time.time() - cb['last_failure_time'] > cb['timeout']:
                cb['state'] = 'HALF_OPEN'
                log_message("CIRCUIT_BREAKER", {"target": target, "state": "HALF_OPEN"}, 'WARNING')
                return True
            return False
        return True

def record_success(target):
    """Record successful connection"""
    with cb_lock:
        cb = circuit_breaker[target]
        cb['failures'] = 0
        if cb['state'] != 'CLOSED':
            cb['state'] = 'CLOSED'
            circuit_breaker_state.labels(target=target).set(0)
            log_message("CIRCUIT_BREAKER", {"target": target, "state": "CLOSED"}, 'INFO')

def record_failure(target):
    """Record failed connection and potentially open circuit"""
    with cb_lock:
        cb = circuit_breaker[target]
        cb['failures'] += 1
        cb['last_failure_time'] = time.time()
        if cb['failures'] >= cb['threshold']:
            cb['state'] = 'OPEN'
            circuit_breaker_state.labels(target=target).set(2)
            log_message("CIRCUIT_BREAKER", {"target": target, "state": "OPEN", "failures": cb['failures']}, 'ERROR')

def log_message(event, details, level='INFO'):
    """Structured Logging (JSON format for Production analysis)"""
    # Ghi lại timestamp và các biến môi trường quan trọng
    log_entry = {
        "timestamp": time.time(),
        "app_mode": APP_MODE,
        "event": event,
        "details": details
    }
    if level == 'INFO':
        logger.info(json.dumps(log_entry))
    elif level == 'ERROR':
        logger.error(json.dumps(log_entry))
    elif level == 'WARNING':
        logger.warning(json.dumps(log_entry))

def get_db_connection(host):
    """Attempt Redis connection with Circuit Breaker pattern"""
    target = 'db_g2' if host == DB_G2_HOST else 'db_g1'
    
    # Circuit Breaker check
    if target == 'db_g2' and not check_circuit_breaker(target):
        log_message("CIRCUIT_BREAKER_BLOCK", {"host": host, "state": "OPEN"}, 'WARNING')
        return None
    
    try:
        r = redis.Redis(
            host=host, 
            port=6379, 
            socket_timeout=TIMEOUT, 
            socket_connect_timeout=TIMEOUT
        )
        r.ping()
        if target == 'db_g2':
            record_success(target)
        return r
    except Exception as e:
        db_connection_failures.labels(host=host).inc()
        if target == 'db_g2':
            record_failure(target)
        log_message("DB_CONNECT_FAILURE", {"host": host, "error": str(e), "timeout_sec": TIMEOUT}, 'ERROR')
        return None

# --- Graceful Shutdown Handler ---
def signal_handler(signum, frame):
    """Handles SIGTERM/SIGINT for clean container shutdown."""
    log_message("SHUTDOWN_EVENT", {"signal": signum, "message": "Received shutdown signal. Exiting gracefully."}, 'WARNING')
    sys.exit(0)

# Register signal handlers for robust exit
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# --- Logic CP: Consistency Priority ---
def cp_write(key, value):
    g1 = get_db_connection(DB_G1_HOST)
    g2 = get_db_connection(DB_G2_HOST)
    
    if g1 is None or g2 is None:
        log_message("CP_ABORTED", {"reason": "Partition or node failure", "key": key}, 'ERROR')
        raise Exception("Consistency Failure: Cannot reach all Quorum nodes. Sacrificing Availability (A).")
    
    # Write with timestamp for Bounded Staleness
    timestamp = int(time.time() * 1000)
    data = json.dumps({"value": value, "timestamp": timestamp})
    
    g1.set(key, data)
    g2.set(key, data)
    
    # Store write timestamp in session for Read-Your-Writes
    session[f'write_ts_{key}'] = timestamp
    
    log_message("CP_COMMIT", {"key": key, "status": "Strong Consistency maintained", "timestamp": timestamp})
    return "CP Success: Strong Consistency maintained."

# --- Logic AP: Availability Priority ---
def ap_write(key, value):
    g1 = get_db_connection(DB_G1_HOST)
    
    if g1 is None:
        log_message("AP_CRITICAL_FAILURE", {"reason": "Primary G1 node is down", "key": key}, 'ERROR')
        raise Exception("Critical Failure: Primary G1 node is down.")

    # Write with timestamp
    timestamp = int(time.time() * 1000)
    data = json.dumps({"value": value, "timestamp": timestamp})
    g1.set(key, data)
    
    # Store write timestamp in session for Read-Your-Writes
    session[f'write_ts_{key}'] = timestamp
    
    g2_status = "Skipped"
    try:
        g2 = get_db_connection(DB_G2_HOST)
        if g2:
            g2.set(key, data)
            g2_status = "G2 Replicated"
        else:
            g2_status = "G2 Unreachable/Stale"
            log_message("AP_STALE_RISK", {"key": key, "target": "db_g2", "reason": "Partition/Unreachable"}, 'WARNING')
    except Exception as e:
        g2_status = f"G2 Replication Failed: {str(e)}"
        log_message("AP_ASYNC_FAIL", {"key": key, "target": "db_g2", "error": str(e)}, 'WARNING')

    return f"AP Success: High Availability maintained. G2 Status: {g2_status}"

# --- API Endpoints ---
@app.route('/write/<key>/<value>', methods=['POST'])
def write_data(key, value):
    start_time = time.time()
    try:
        if APP_MODE == 'CP':
            result = cp_write(key, value)
        else:
            result = ap_write(key, value)
            
        latency = time.time() - start_time
        request_latency.labels(mode=APP_MODE, operation='write').observe(latency)
        request_count.labels(mode=APP_MODE, operation='write', status='success').inc()
        
        log_message("REQUEST_COMPLETED", {"type": "write", "latency_ms": f"{latency*1000:.2f}", "result": "SUCCESS"})
        return jsonify({"status": "SUCCESS", "mode": APP_MODE, "message": result}), 200
    except Exception as e:
        latency = time.time() - start_time
        request_latency.labels(mode=APP_MODE, operation='write').observe(latency)
        request_count.labels(mode=APP_MODE, operation='write', status='failure').inc()
        
        log_message("REQUEST_FAILED", {"type": "write", "latency_ms": f"{latency*1000:.2f}", "error": str(e)}, 'ERROR')
        return jsonify({"status": "FAILURE", "mode": APP_MODE, "error": str(e)}), 503

@app.route('/read/<key>', methods=['GET'])
def read_data(key):
    start_time = time.time()
    g1 = get_db_connection(DB_G1_HOST)
    g2 = get_db_connection(DB_G2_HOST)
    
    # Parse data with timestamp
    def parse_value(conn, key):
        if not conn:
            return "N/A", 0
        raw = conn.get(key)
        if not raw:
            return "N/A", 0
        try:
            data = json.loads(raw.decode())
            return data.get('value', 'N/A'), data.get('timestamp', 0)
        except:
            return raw.decode(), 0
    
    g1_val, g1_ts = parse_value(g1, key)
    g2_val, g2_ts = parse_value(g2, key)
    
    # Check Read-Your-Writes consistency
    write_ts = session.get(f'write_ts_{key}', 0)
    ryw_consistent = g1_ts >= write_ts if write_ts > 0 else True
    
    # Check Bounded Staleness
    current_ts = int(time.time() * 1000)
    g1_staleness = current_ts - g1_ts if g1_ts > 0 else 0
    g2_staleness = current_ts - g2_ts if g2_ts > 0 else 0
    
    # Update Prometheus metrics
    staleness_gauge.labels(node='g1').set(g1_staleness)
    staleness_gauge.labels(node='g2').set(g2_staleness)
    
    is_consistent = (g1_val == g2_val and g1_val != "N/A")
    bounded_stale = g1_staleness <= MAX_STALENESS_MS and g2_staleness <= MAX_STALENESS_MS
    
    consistency_status = "CONSISTENT" if is_consistent else "INCONSISTENT/STALE"
    if not bounded_stale and g1_val != "N/A":
        consistency_status += " (EXCEEDS_STALENESS_BOUND)"
    if not ryw_consistent:
        consistency_status += " (RYW_VIOLATION)"
    
    latency = time.time() - start_time
    request_latency.labels(mode=APP_MODE, operation='read').observe(latency)
    request_count.labels(mode=APP_MODE, operation='read', status='success').inc()
    
    log_message("READ_CHECK", {
        "key": key, 
        "consistency": consistency_status, 
        "g1_staleness_ms": g1_staleness,
        "g2_staleness_ms": g2_staleness,
        "ryw_consistent": ryw_consistent
    })
    
    return jsonify({
        "key": key, 
        "mode": APP_MODE, 
        "G1_Value": g1_val, 
        "G2_Value": g2_val,
        "G1_Staleness_ms": g1_staleness,
        "G2_Staleness_ms": g2_staleness,
        "Consistency_Status": consistency_status,
        "RYW_Consistent": ryw_consistent
    }), 200

# --- Health Check Endpoint (Required for Docker Healthcheck) ---
@app.route('/health', methods=['GET'])
def health_check():
    g1 = get_db_connection(DB_G1_HOST)
    if g1:
        return jsonify({"status": "UP", "db_check": "G1 OK"}), 200
    return jsonify({"status": "DOWN", "db_check": "G1 FAILED"}), 500

@app.route('/circuit-breaker', methods=['GET'])
def circuit_breaker_status():
    """Endpoint to check Circuit Breaker status"""
    with cb_lock:
        status = {
            'db_g2': {
                'state': circuit_breaker['db_g2']['state'],
                'failures': circuit_breaker['db_g2']['failures'],
                'last_failure': circuit_breaker['db_g2']['last_failure_time']
            }
        }
    return jsonify(status), 200

@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == '__main__':
    log_message("SERVICE_STARTUP", {"mode": APP_MODE, "port": APP_PORT, "timeout": TIMEOUT})
    time.sleep(5) # Give time for DBs to initialize
    # Sử dụng Waitress WSGI server (Production)
    from waitress import serve 
    serve(app, host='0.0.0.0', port=APP_PORT)