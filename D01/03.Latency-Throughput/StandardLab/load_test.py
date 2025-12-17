import requests
import time
import concurrent.futures

BASE_URL = "http://localhost:8080"
NUM_REQUESTS = 1000 # Tổng số request để đo throughput

def run_test(path, description):
    print(f"\n--- Testing {description} ({NUM_REQUESTS} requests) ---")
    
    start_time = time.time()
    
    def fetch_url(url):
        try:
            # Gửi POST cho /write, GET cho /read
            if path == "/write":
                response = requests.post(url, timeout=5)
            else:
                response = requests.get(url, timeout=5)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            # print(f"Error: {e}")
            return False

    urls = [BASE_URL + path] * NUM_REQUESTS
    
    # Sử dụng ThreadPoolExecutor để tạo tải song song (simulating high Throughput)
    # Tăng max_workers để đẩy Throughput lên cao nhất
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        results = list(executor.map(fetch_url, urls))

    end_time = time.time()
    total_time = end_time - start_time
    
    successful_requests = sum(results)
    
    # Tính toán Throughput (RPS) [2]
    throughput = successful_requests / total_time
    
    # Latency trung bình (Approx. Latency)
    avg_latency_ms = (total_time / successful_requests) * 1000 if successful_requests > 0 else 0

    print(f"Total time elapsed: {total_time:.2f} seconds")
    print(f"Successful Requests: {successful_requests}")
    print(f"Achieved THROUGHPUT: {throughput:.2f} RPS")
    print(f"Observed AVG LATENCY: {avg_latency_ms:.2f} ms")
    
    return avg_latency_ms, throughput

if __name__ == "__main__":
    # Test 1: Tuyến Latency Thấp (Read)
    read_latency, read_throughput = run_test("/read", "LOW LATENCY (REPLICA) PATH")
    
    # Test 2: Tuyến Latency Cao (Write)
    write_latency, write_throughput = run_test("/write", "HIGH LATENCY (PRIMARY) PATH")

    print("\n--- Summary of Latency vs Throughput Trade-off ---")
    print(f"Read Path (5ms Sim Delay): Avg Latency={read_latency:.2f} ms, Throughput={read_throughput:.2f} RPS")
    print(f"Write Path (50ms Sim Delay): Avg Latency={write_latency:.2f} ms, Throughput={write_throughput:.2f} RPS")