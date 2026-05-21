from celery import Celery
from app.config import Config
import redis

# Test Redis connection
def test_redis_connection():
    """Test if Redis is accessible"""
    try:
        r = redis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=Config.REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=5
        )
        r.ping()
        print(f"\n✅ [REDIS] Connected successfully!")
        print(f"   Host: {Config.REDIS_HOST}:{Config.REDIS_PORT}")
        print(f"   DB: {Config.REDIS_DB}\n")
        return True
    except Exception as e:
        print(f"\n❌ [REDIS] Connection FAILED!")
        print(f"   Error: {str(e)}")
        print(f"   Host: {Config.REDIS_HOST}:{Config.REDIS_PORT}")
        print(f"   Solution: Make sure Redis is running:")
        print(f"     - Windows: docker run -d -p 6379:6379 redis:alpine")
        print(f"     - Linux/Mac: redis-server")
        print(f"     - Check: redis-cli ping\n")
        return False

# Create Celery app
broker_url = f"redis://{Config.REDIS_HOST}:{Config.REDIS_PORT}/{Config.REDIS_DB}"
backend_url = f"redis://{Config.REDIS_HOST}:{Config.REDIS_PORT}/{Config.REDIS_DB}"

print("\n" + "="*80)
print("[CELERY] Initializing Celery app...")
print(f"   Broker: {broker_url}")
print(f"   Backend: {backend_url}")
print("="*80)

celery_app = Celery(
    'flask_app',
    broker=broker_url,
    backend=backend_url
)

# Test connection
redis_connected = test_redis_connection()

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60, 
    task_soft_time_limit=28 * 60,  
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  
)

if redis_connected:
    print("[CELERY] Configuration loaded successfully")
    print("[CELERY] Ready to accept tasks\n")
else:
    print("[CELERY] ⚠️  WARNING: Celery configured but Redis not accessible!")
    print("[CELERY] Tasks will be queued but NOT processed until Redis is available\n")

# Auto-discover tasks
celery_app.autodiscover_tasks(['app.tasks'])
