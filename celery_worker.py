#!/usr/bin/env python
"""
Celery worker script for running background tasks
Run this in a separate terminal/process
"""
import os
import sys
import redis
from app.celery_app import celery_app
from app.config import Config

def check_redis_connection():
    """Check if Redis is running and accessible"""
    print("\n" + "="*80)
    print("[WORKER] Checking Redis connection...")
    print("="*80)
    
    try:
        r = redis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=Config.REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=5
        )
        r.ping()
        print(f"✅ [REDIS] Connected successfully!")
        print(f"   Host: {Config.REDIS_HOST}:{Config.REDIS_PORT}")
        print(f"   DB: {Config.REDIS_DB}")
        print(f"   Status: READY\n")
        return True
    except redis.ConnectionError as e:
        print(f"❌ [REDIS] Connection FAILED!")
        print(f"   Error: {str(e)}")
        print(f"   Host: {Config.REDIS_HOST}:{Config.REDIS_PORT}")
        print(f"\n📌 Solution: Start Redis in another terminal:")
        print(f"   Windows (Docker): docker run -d -p 6379:6379 redis:alpine")
        print(f"   Windows (WSL): wsl -u root && redis-server")
        print(f"   Linux: sudo redis-server")
        print(f"   macOS: brew install redis && redis-server")
        print(f"\n   Then verify: redis-cli ping\n")
        return False
    except Exception as e:
        print(f"❌ [REDIS] Unexpected error: {str(e)}\n")
        return False

if __name__ == '__main__':
    print("\n" + "="*80)
    print("[WORKER] Starting Celery Worker...")
    print("="*80)
    
    # Set environment
    os.environ.setdefault('ENVIRONMENT', 'development')
    
    # Check Redis connection before starting
    if not check_redis_connection():
        print("\n⚠️  WARNING: Redis is not available!")
        print("The worker will fail to process tasks.\n")
        sys.exit(1)
    
    print("[WORKER] Starting worker process...")
    print("="*80 + "\n")
    
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=2',  # Number of worker processes
        '--time-limit=1800',  # 30 minutes hard limit per task
        '--soft-time-limit=1700',  # 28 minutes soft limit per task
        '--queues=celery',
        '--pool=solo'  # Use solo pool for Windows compatibility
    ])
