from abc import ABC, abstractmethod
from flask import jsonify


class BaseRouteHandler(ABC):
    """Abstract base class for route handlers"""
    
    def __init__(self):
        self.name = self.__class__.__name__
    
    @staticmethod
    def success_response(data=None, message="Success", status_code=200):
        """Return a success response"""
        response = {"status": "success"}
        if message:
            response["message"] = message
        if data is not None:
            response["data"] = data
        return jsonify(response), status_code
    
    @staticmethod
    def error_response(error, status_code=500):
        """Return an error response"""
        return jsonify({
            "status": "error",
            "error": str(error)
        }), status_code
    
    @staticmethod
    def not_found_response(message="Resource not found"):
        """Return a 404 not found response"""
        return jsonify({
            "status": "error",
            "error": message
        }), 404
