import requests
import threading
import time
import argparse
from colorama import Fore, init
import logging
from datetime import datetime
import psutil

# Inisialisasi colorama
init()

# Setup logging
logging.basicConfig(
    filename=f'load_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class LoadTester:
    def __init__(self, target, threads, test_duration):
        self.target = target
        self.threads = threads
        self.test_duration = test_duration
        self.success = 0
        self.failed = 0
        self.lock = threading.Lock()
        self.start_time = time.time()
        self.is_running = True

    def print_status(self, message, color=Fore.WHITE):
        """Print berwarna ke console dan log"""
        with self.lock:
            print(f"{color}{message}{Fore.RESET}")
            logging.info(message)

    def make_request(self):
        """Melakukan single request ke target"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }

        try:
            response = requests.get(self.target, headers=headers, timeout=5)
            with self.lock:
                self.success += 1
            return response.status_code
        except requests.RequestException as e:
            with self.lock:
                self.failed += 1
            return str(e)

    def worker(self):
        """Worker thread untuk melakukan requests"""
        while self.is_running and (time.time() - self.start_time) < self.test_duration:
            status = self.make_request()
            self.print_status(f"Request status: {status}", 
                            Fore.GREEN if isinstance(status, int) and 200 <= status < 300 
                            else Fore.RED)
            time.sleep(0.1)  # Delay untuk menghindari overload

    def monitor(self):
        """Monitor dan tampilkan statistik"""
        while self.is_running and (time.time() - self.start_time) < self.test_duration:
            time.sleep(1)
            elapsed = time.time() - self.start_time
            total = self.success + self.failed
            rps = total / elapsed if elapsed > 0 else 0
            
            stats = f"""
{'='*50}
Waktu berjalan: {elapsed:.2f} detik
Request sukses: {self.success}
Request gagal: {self.failed}
Requests per detik: {rps:.2f}
{'='*50}
"""
            self.print_status(stats, Fore.CYAN)

    def run(self):
        """Mulai load testing"""
        self.print_status(f"""
Load Testing dimulai dengan konfigurasi:
Target: {self.target}
Threads: {self.threads}
Durasi: {self.test_duration} detik
        """, Fore.YELLOW)

        # Buat threads
        threads = []
        for _ in range(self.threads):
            t = threading.Thread(target=self.worker)
            threads.append(t)
            t.start()

        # Thread monitor
        monitor_thread = threading.Thread(target=self.monitor)
        monitor_thread.start()

        # Tunggu sampai selesai
        for t in threads:
            t.join()

        self.is_running = False
        monitor_thread.join()

        # Tampilkan hasil akhir
        final_stats = f"""
{'='*50}
TEST SELESAI
Total waktu: {time.time() - self.start_time:.2f} detik
Total request sukses: {self.success}
Total request gagal: {self.failed}
{'='*50}
"""
        self.print_status(final_stats, Fore.MAGENTA)

def monitor_server_resources():
    """Monitor resource server (tambahkan sesuai kebutuhan)"""
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    
    print(f"""
    CPU Usage: {cpu_percent}%
    Memory Usage: {memory.percent}%
    """)

def main():
    parser = argparse.ArgumentParser(description='Website Load Tester')
    parser.add_argument('-t', '--target', required=True, help='Target URL')
    parser.add_argument('-n', '--threads', type=int, default=10, help='Jumlah threads')
    parser.add_argument('-d', '--duration', type=int, default=30, help='Durasi test (detik)')
    
    args = parser.parse_args()

    try:
        tester = LoadTester(args.target, args.threads, args.duration)
        tester.run()
    except KeyboardInterrupt:
        print("\nTest dihentikan oleh user")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 