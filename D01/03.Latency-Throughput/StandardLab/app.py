from flask import Flask
import os
import time

app = Flask(__name__)

SERVICE_NAME = os.getenv("SERVICE_NAME", "UNKNOWN")
DELAY_MS = int(os.getenv("SIMULATED_DELAY_MS", "0"))

@app.route("/")
def index():
    time.sleep(DELAY_MS / 1000.0)
    return f"Response from {SERVICE_NAME} (delay: {DELAY_MS}ms)\n"

@app.route("/read")
def read():
    time.sleep(DELAY_MS / 1000.0)
    return f"READ from {SERVICE_NAME} (delay: {DELAY_MS}ms)\n"

@app.route("/write", methods=["POST"])
def write():
    time.sleep(DELAY_MS / 1000.0)
    return f"WRITE to {SERVICE_NAME} (delay: {DELAY_MS}ms)\n"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)