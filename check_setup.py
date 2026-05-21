#!/usr/bin/env python
"""
Diagnostic script to check if all services are properly configured
Run this before starting the application
"""
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80)

def print_success(text):
    """Print success message"""
    print(f"✅ {text}")

def print_error(text):
    """Print error message"""
    print(f"❌ {text}")

def print_warning(text):
    """Print warning message"""
    print(f"⚠️  {text}")

def check_environment():
    """Check Python environment"""
    print_header("1. PYTHON ENVIRONMENT")
    
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print_success("Python environment OK")

def check_imports():
    """Check if all required packages are installed"""
    print_header("2. REQUIRED PACKAGES")
    
    required_packages = {
        'flask': 'Flask',
        'flask_cors': 'Flask-Cors',
        'celery': 'Celery',
        'redis': 'Redis',
        'psycopg2': 'PostgreSQL',
        'groq': 'Groq',
        'requests': 'Requests',
        'dotenv': 'python-dotenv',
    }
    
    all_ok = True
    for import_name, display_name in required_packages.items():
        try:
            __import__(import_name)
            print_success(f"{display_name} installed")
        except ImportError:
            print_error(f"{display_name} NOT installed - Run: pip install -r requirements.txt")
            all_ok = False
    
    return all_ok

def check_config():
    """Check configuration"""
    print_header("3. CONFIGURATION")
    
    try:
        from app.config import Config
        
        print(f"Flask DEBUG: {Config.DEBUG}")
        print(f"Flask HOST: {Config.HOST}")
        print(f"Flask PORT: {Config.PORT}")
        print(f"Redis HOST: {Config.REDIS_HOST}")
        print(f"Redis PORT: {Config.REDIS_PORT}")
        print(f"Redis DB: {Config.REDIS_DB}")
        print(f"Database: {Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}")
        
        print_success("Configuration loaded successfully")
        return True
    except Exception as e:
        print_error(f"Configuration error: {str(e)}")
        return False

def check_redis():
    """Check Redis connection"""
    print_header("4. REDIS CONNECTION")
    
    try:
        import redis
        from app.config import Config
        
        print(f"Connecting to Redis at {Config.REDIS_HOST}:{Config.REDIS_PORT} (DB {Config.REDIS_DB})...")
        
        r = redis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=Config.REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=5
        )
        
        r.ping()
        print_success("Redis connected successfully!")
        
        # Get Redis info
        info = r.info()
        print(f"Redis version: {info.get('redis_version', 'unknown')}")
        print(f"Used memory: {info.get('used_memory_human', 'unknown')}")
        
        return True
    except redis.ConnectionError as e:
        print_error(f"Redis connection failed: {str(e)}")
        print_warning("Solutions:")
        print("  - Windows (Docker): docker run -d -p 6379:6379 redis:alpine")
        print("  - Windows (WSL): wsl -u root && redis-server")
        print("  - Linux: sudo redis-server")
        print("  - macOS: brew install redis && redis-server")
        print("  - Verify: redis-cli ping")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return False

def check_database():
    """Check database connection"""
    print_header("5. DATABASE CONNECTION")
    
    try:
        import psycopg2
        from app.config import Config
        
        print(f"Connecting to {Config.DB_USER}@{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}...")
        
        conn = psycopg2.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            sslmode=Config.DB_SSLMODE,
            connect_timeout=5
        )
        
        conn.close()
        print_success("Database connected successfully!")
        return True
    except psycopg2.OperationalError as e:
        print_error(f"Database connection failed: {str(e)}")
        print_warning("Make sure PostgreSQL is running and credentials are correct")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return False

def check_celery():
    """Check Celery configuration"""
    print_header("6. CELERY CONFIGURATION")
    
    try:
        from app.celery_app import celery_app
        
        print(f"Broker: {celery_app.conf['broker_url']}")
        print(f"Backend: {celery_app.conf['result_backend']}")
        print(f"Task serializer: {celery_app.conf.get('task_serializer', 'default')}")
        print(f"Timezone: {celery_app.conf.get('timezone', 'UTC')}")
        
        print_success("Celery configured successfully!")
        return True
    except Exception as e:
        print_error(f"Celery configuration error: {str(e)}")
        return False

def check_api_keys():
    """Check API keys"""
    print_header("7. API KEYS")
    
    try:
        from app.config import Config
        
        keys_to_check = {
            'GROQ_API_KEY': Config.GROQ_API_KEY,
            'MINERU_TOKEN': Config.MINERU_TOKEN,
            'AZURE_EMBEDDING_API_KEY': Config.AZURE_EMBEDDING_API_KEY,
            'SUMOPOD_API_KEY': Config.SUMOPOD_API_KEY,
        }
        
        for key_name, key_value in keys_to_check.items():
            if key_value:
                masked = f"{key_value[:10]}...{key_value[-4:]}"
                print_success(f"{key_name} configured ({masked})")
            else:
                print_warning(f"{key_name} not set - check .env file")
        
        return True
    except Exception as e:
        print_error(f"API key check error: {str(e)}")
        return False

def print_summary(results):
    """Print summary of all checks"""
    print_header("SUMMARY")
    
    all_passed = all(results.values())
    
    for check_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check_name}")
    
    if all_passed:
        print_success("\nAll checks passed! Ready to start the application.\n")
        print("Next steps:")
        print("1. Make sure Redis is running in a terminal")
        print("2. Run: python main.py (Flask API)")
        print("3. Run: python celery_worker.py (Celery Worker in another terminal)")
        return True
    else:
        print_error("\nSome checks failed. See above for details.\n")
        return False

def main():
    """Run all checks"""
    print("\n" + "█"*80)
    print("  ASYNC UPLOAD SYSTEM - DIAGNOSTIC CHECK")
    print("█"*80)
    
    results = {}
    
    # Run all checks
    check_environment()
    results['Imports'] = check_imports()
    results['Configuration'] = check_config()
    results['Redis'] = check_redis()
    results['Database'] = check_database()
    results['Celery'] = check_celery()
    results['API Keys'] = check_api_keys()
    
    # Print summary
    success = print_summary(results)
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
