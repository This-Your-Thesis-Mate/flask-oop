import logging
import sys
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
        
        # Configure logging
        self._configure_logging()
        
        # Load configuration
        self.app.config.from_object(self.config)
        
        # Enable CORS
        CORS(self.app)
        
        # Register blueprints
        self._register_blueprints()
        
        return self.app
    
    def _configure_logging(self):
        """Configure application-wide logging"""
        # Set root logger level
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        # Add handler to root logger (avoids duplicate handlers on reload)
        if not root_logger.handlers:
            root_logger.addHandler(console_handler)
        
        # Also set Flask app logger
        self.app.logger.setLevel(logging.INFO)
        if not self.app.logger.handlers:
            self.app.logger.addHandler(console_handler)
    
    def _register_blueprints(self):
        """Register all route blueprints"""
        from app.routes import (
            upload_bp,
            rag_bp,
            quiz_bp,
            annotation_bp,
            module_bp,
            healthcheck_bp,
        )
        
        self.app.register_blueprint(upload_bp)
        self.app.register_blueprint(rag_bp)
        self.app.register_blueprint(quiz_bp)
        self.app.register_blueprint(annotation_bp)
        self.app.register_blueprint(module_bp)
        self.app.register_blueprint(healthcheck_bp)
