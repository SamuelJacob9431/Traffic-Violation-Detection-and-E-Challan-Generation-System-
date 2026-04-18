import subprocess
import time
import sys
import os
import socket

def free_port(port):
    """Force kill any process using the given port on Windows."""
    try:
        if os.name == 'nt':
            # Find PID using netstat
            output = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True).decode()
            if output:
                lines = output.strip().split('\n')
                for line in lines:
                    if f':{port}' in line and 'LISTENING' in line:
                        pid = line.strip().split()[-1]
                        subprocess.call(f'taskkill /F /PID {pid}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        print(f"Cleaned up orphaned process {pid} on port {port}")
    except Exception:
        pass

def run_backend():
    free_port(8000)
    print("Starting Backend (FastAPI)...")
    return subprocess.Popen([sys.executable, "-m", "backend.main"], cwd=os.getcwd())

def run_frontend():
    print("Starting Frontend (Vite)...")
    # Using shell=True for npm on Windows
    return subprocess.Popen("npm run dev", shell=True, cwd=os.path.join(os.getcwd(), "frontend"))

def run_ai_engine():
    print("Starting AI Engine (YOLOv8)...")
    return subprocess.Popen([sys.executable, "-m", "ai_engine.detector"], cwd=os.getcwd())

if __name__ == "__main__":
    p_backend = run_backend()
    time.sleep(3) # Wait for backend to start
    p_frontend = run_frontend()
    p_ai = run_ai_engine()
    
    print("\n--- System Running ---")
    print("Dashboard: http://localhost:3000")
    print("API Docs: http://localhost:8000/docs")
    print("Press Ctrl+C to stop all services.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        p_backend.terminate()
        p_frontend.terminate()
        p_ai.terminate()
