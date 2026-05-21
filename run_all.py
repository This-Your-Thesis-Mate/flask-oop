import subprocess
import sys
import time
import os
from pathlib import Path

# Get project root
PROJECT_ROOT = Path(__file__).parent.absolute()
VENV_SCRIPTS = PROJECT_ROOT / "venv" / "Scripts"

def run_command(cmd, name):
    """Run command and print output"""
    print(f"\n{'='*60}")
    print(f"▶️  Starting: {name}")
    print(f"{'='*60}\n")
    
    try:
        subprocess.run(cmd, cwd=PROJECT_ROOT)
    except KeyboardInterrupt:
        print(f"\n⏹️  Stopped: {name}")
    except Exception as e:
        print(f"❌ Error in {name}: {e}")

def main():
    """Start Flask and Celery in parallel using subprocess"""
    import subprocess
    import threading
    
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║         🚀 ASYNC UPLOAD SYSTEM - FULL STARTUP             ║
    ║    Flask API + Celery Worker + Redis (parallel)           ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    # Check if Redis is running
    print("📋 Checking Redis connection...")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis is running on localhost:6379\n")
    except Exception as e:
        print(f"❌ Redis not running! Error: {e}")
        print("   Start Redis first: redis-server\n")
        return
    
    # Prepare commands
    flask_cmd = [sys.executable, "main.py"]
    celery_cmd = [sys.executable, "celery_worker.py"]
    
    # Run Flask and Celery in separate threads
    flask_thread = threading.Thread(
        target=run_command,
        args=(flask_cmd, "Flask API (Terminal 1)"),
        daemon=False
    )
    celery_thread = threading.Thread(
        target=run_command,
        args=(celery_cmd, "Celery Worker (Terminal 2)"),
        daemon=False
    )
    
    try:
        # Start both
        flask_thread.start()
        time.sleep(2)  # Give Flask time to start
        celery_thread.start()
        
        print("""
        ╔════════════════════════════════════════════════════════════╗
        ║                    ✅ SYSTEM RUNNING                       ║
        ║  Flask API:     http://localhost:5000                     ║
        ║  Upload:        POST /uploads                             ║
        ║  Status:        GET /upload-status/<task_id>              ║
        ║  Flower (opt):  http://localhost:5555                     ║
        ║                                                            ║
        ║  Press Ctrl+C to stop both services                       ║
        ╚════════════════════════════════════════════════════════════╝
        """)
        
        # Wait for both threads
        flask_thread.join()
        celery_thread.join()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Stopping system...")
        time.sleep(1)
        sys.exit(0)

if __name__ == "__main__":
    main()
