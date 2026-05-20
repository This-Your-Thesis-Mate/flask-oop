from flask import Blueprint, jsonify
from app.routes.base_handler import BaseRouteHandler

healthcheck_bp = Blueprint('healthcheck', __name__)


class HealthCheckHandler(BaseRouteHandler):
    """Handler for health check operations"""
    
    @staticmethod
    def health_check():
        """
        Health check endpoint
        
        Returns:
            JSON response with status
        """
        return jsonify({
            'status': 'healthy',
            'service': 'Splace Classroom API'
        })
    
    @staticmethod
    def index():
        """
        Index endpoint
        
        Returns:
            JSON response with API info
        """
        return jsonify({
            'service': 'Splace Classroom API',
            'version': '2.0',
            'status': 'running'
        })


# Create handler instance
health_handler = HealthCheckHandler()


# Register routes
@healthcheck_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return health_handler.health_check()


@healthcheck_bp.route('/', methods=['GET'])
def index():
    """Index endpoint"""
    return health_handler.index()
