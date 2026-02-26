import subprocess
import time
import os
import signal
import sys
import psutil

def kill_port(port):
    print(f"--- Cleaning up port {port} ---")
    current_pid = os.getpid()
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            # Skip the current process to avoid suicide
            if proc.pid == current_pid:
                continue
                
            for conn in proc.connections(kind='inet'):
                if conn.laddr.port == port:
                    print(f"Killing {proc.name()} (PID {proc.pid}) on port {port}")
                    proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def run():
    print("--- STOPPING OLD SERVERS ---")
    # 1. Kill old processes
    try:
        kill_port(8000)
        kill_port(3000)
    except Exception as e:
        print(f"Error killing ports: {e}")
        # Fallback for windows if psutil fails
        os.system(f"taskkill /F /IM python.exe /T")
        os.system(f"taskkill /F /IM node.exe /T")
        os.system(f"taskkill /F /IM uvicorn.exe /T")

    print("\n--- STARTING NEW SERVERS ---")
    
    print("1. Starting Backend (Port 8000)...")
    # Use python -m uvicorn to ensure it runs correctly on Windows
    # Using specific python executable to avoid path issues
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"],
        cwd=os.getcwd(), # Current directory is root where main.py is
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    print("   Waiting for Backend to initialize...")
    time.sleep(5)
    if backend.poll() is not None:
        print("!!! BACKEND FAILED TO START !!!")
        print(backend.stderr.read().decode())
        return

    print("2. Starting Frontend (Port 3000)...")
    frontend_dir = os.path.join(os.getcwd(), "frontend")
    npm_cmd = "npm.cmd" if os.name == 'nt' else "npm"
    
    frontend = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=frontend_dir,
        shell=True
    )

    print("\n>>> SYSTEM IS LIVE. BOTH SERVERS RUNNING. <<<")
    print(">>> PLEASE REFRESH BROWSER AT http://localhost:3000 <<<")
    print(">>> Press Ctrl+C to stop servers <<<")

    try:
        backend.wait()
        frontend.wait()
    except KeyboardInterrupt:
        print("\n--- SHUTTING DOWN ---")
        backend.terminate()
        frontend.terminate()
        kill_port(8000)
        kill_port(3000)

if __name__ == "__main__":
    run()
