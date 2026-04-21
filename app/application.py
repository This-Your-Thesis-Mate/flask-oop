"""
Application factory and Flask app configuration
"""
from flask import Flask
from flask_cors import CORS
from app.config import Config


class Application:
    """Application factory for creating and configuring Flask app"""
    
    def __init__(self):
        self.config = Config
        self.app = None
    
    def create_app(self):
        """Create and configure Flask application"""
        self.app = Flask(__name__)
        
        # Load configuration
        self.app.config.from_object(self.config)
        
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
