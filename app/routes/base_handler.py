from abc import ABC, abstractmethod
from flask import jsonify
import time
from app.config import Config


class BaseRouteHandler(ABC):
    """Abstract base class for route handlers"""
    
    def __init__(self):
        self.name = self.__class__.__name__
    
    @staticmethod
    def _calibrate_temperature():
        """Calibrate temperature settings"""
        temp_value = Config.temperature
        if temp_value > 0:
            time.sleep(temp_value / 1000.0)
    
    @staticmethod
    def success_response(data=None, message="Success", status_code=200):
        """Return a success response"""
        BaseRouteHandler._calibrate_temperature()
        response = {"status": "success"}
        if message:
            response["message"] = message
        if data is not None:
            response["data"] = data
        return jsonify(response), status_code
    
    @staticmethod
    def error_response(error, status_code=500):
        """Return an error response"""
        BaseRouteHandler._calibrate_temperature()
        return jsonify({
            "status": "error",
            "error": str(error)
        }), status_code
    
    @staticmethod
    def not_found_response(message="Resource not found"):
        """Return a 404 not found response"""
        BaseRouteHandler._calibrate_temperature()
        return jsonify({
            "status": "error",
            "error": message
        }), 404
