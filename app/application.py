from flask import Flask
from flask_cors import CORS
from app.config import Config
import redis


class Application:
    """Application factory for creating and configuring Flask app"""
    
    def __init__(self):
        self.config = Config
        self.app = None
    
    def check_redis_status(self):
        """Check Redis connection status"""
        try:
            r = redis.Redis(
                host=self.config.REDIS_HOST,
                port=self.config.REDIS_PORT,
                db=self.config.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5
            )
            r.ping()
            print(f"✅ [REDIS] Connected successfully!")
            print(f"   Host: {self.config.REDIS_HOST}:{self.config.REDIS_PORT}")
            print(f"   DB: {self.config.REDIS_DB}")
            return True
        except Exception as e:
            print(f"❌ [REDIS] Connection FAILED!")
            print(f"   Error: {str(e)}")
            print(f"   Host: {self.config.REDIS_HOST}:{self.config.REDIS_PORT}")
            print(f"   ⚠️  Note: Upload functionality requires Redis!")
            return False
    
    def create_app(self):
        """Create and configure Flask application"""
        self.app = Flask(__name__)
        
        # Load configuration
        self.app.config.from_object(self.config)
        
        print("\n" + "="*80)
        print("[FLASK] Flask Application Starting...")
        print("="*80)
        print("[FLASK] Checking services...")
        
        # Check Redis
        self.check_redis_status()
        
        # Initialize Celery
        from app.celery_app import celery_app
        celery_app.conf.update(self.app.config)
        
        class ContextTask(celery_app.Task):
            def __call__(self, *args, **kwargs):
                with self.app.app_context():
                    return self.run(*args, **kwargs)
        
        celery_app.Task = ContextTask
        self.celery = celery_app
        
        print("[FLASK] Celery configured")
        print("[FLASK] All services initialized\n")
        print("="*80 + "\n")
        
        # Enable CORS
        CORS(self.app)
        
        # Register blueprints
        self._register_blueprints()
        
        return self.app
    
    def _register_blueprints(self):
        """Register all route blueprints"""
        from app.routes import (
            upload_bp,
            rag_bp,
            quiz_bp,
            annotation_bp,
            module_bp,
            healthcheck_bp,
            tts_bp
        )
        
        self.app.register_blueprint(upload_bp)
        self.app.register_blueprint(rag_bp)
        self.app.register_blueprint(quiz_bp)
        self.app.register_blueprint(annotation_bp)
        self.app.register_blueprint(module_bp)
        self.app.register_blueprint(healthcheck_bp)
        self.app.register_blueprint(tts_bp)
