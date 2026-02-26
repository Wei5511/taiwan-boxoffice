import subprocess
import time
import os
import sys
import signal

def kill_port(port):
    print(f"--- Cleaning up port {port} ---")
    try:
        # Find PID occupying the port
        cmd = f"netstat -ano | findstr :{port}"
        # On Windows, findstr returns 1 if not found, which causes check_output to raise CalledProcessError
        try:
            output = subprocess.check_output(cmd, shell=True).decode()
            lines = output.strip().split('\n')
            for line in lines:
                parts = line.split()
                # Last element is usually PID
                pid = parts[-1]
                if pid.isdigit() and int(pid) > 0:
                    print(f"Killing PID {pid} on port {port}")
                    os.system(f"taskkill /F /PID {pid} >nul 2>&1")
        except subprocess.CalledProcessError:
            print(f"No process found on port {port}")
    except Exception as e:
        print(f"Error checking port {port}: {e}")

def main():
    print("--- STOPPING STARTUP ---")
    # 1. Kill old processes (Aggressive cleanup)
    kill_port(8001)
    kill_port(3000)
    os.system("taskkill /F /IM uvicorn.exe >nul 2>&1")
    os.system("taskkill /F /IM node.exe >nul 2>&1")
    os.system("taskkill /F /IM python.exe >nul 2>&1")

    print("\n--- STARTING NEW SERVERS ---")
    
    print("1. Starting Backend (Port 8001)...")
    # Use explicit python executable and run module
    # NOT using shell=True to avoid quoting issues with sys.executable
    backend_cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8001", "--reload"]
    print(f"Executing: {backend_cmd}")
    
    try:
        backend = subprocess.Popen(
            backend_cmd,
            cwd=os.getcwd(),
            shell=False # Change to False for list arg
        )
    except Exception as e:
        print(f"Failed to start backend: {e}")
        return

    print("--- Waiting for Backend to warm up... ---")
    time.sleep(5)
    
    print("--- Starting Frontend (Port 3000)...")
    frontend_dir = os.path.join(os.getcwd(), "frontend")
    npm_cmd = "npm.cmd" if os.name == 'nt' else "npm"
    
    print(f"Executing: {npm_cmd} run dev in {frontend_dir}")
    try:
        frontend = subprocess.Popen(
            [npm_cmd, "run", "dev"],
            cwd=frontend_dir,
            shell=True # Keep True for npm alias
        )
    except Exception as e:
        print(f"Failed to start frontend: {e}")
        backend.terminate()
        return
    
    print("\n>>> WINDOWS SERVERS STARTED <<<")
    print(">>> Please refresh http://localhost:3000 <<<")
    print(">>> Press Ctrl+C to stop servers <<<")
    
    # Keep script running
    try:
        backend.wait()
        frontend.wait()
    except KeyboardInterrupt:
        print("\n--- SHUTTING DOWN ---")
        backend.terminate()
        frontend.terminate()
        kill_port(8001)
        kill_port(3000)

if __name__ == "__main__":
    main()
