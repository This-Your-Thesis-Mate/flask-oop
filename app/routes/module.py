from flask import Blueprint, request, jsonify
from app.routes.base_handler import BaseRouteHandler
from app.services import module_service

module_bp = Blueprint('module', __name__)


class ModuleHandler(BaseRouteHandler):
    """Handler for module operations"""
    
    @staticmethod
    def delete_module():
        """
        Delete a module and all related data
        
        JSON body:
            - module_id: Module ID
            - course_id: Course ID
            - tenant_id: Tenant ID (required for multi-tenancy)
        
        Returns:
            JSON response with success message
        """
        module_id = request.json.get('module_id')
        course_id = request.json.get('course_id')
        tenant_id = request.json.get('tenant_id')
        
        if not tenant_id:
            return ModuleHandler.error_response('tenant_id is required', 400)
        
        try:
            module_service.delete_module(module_id, course_id, tenant_id)
            return ModuleHandler.success_response(None, 'Module deleted successfully.', 200)
        except Exception as e:
            if 'not found' in str(e).lower():
                return ModuleHandler.not_found_response('Module not found.')
            return ModuleHandler.error_response(str(e), 500)


# Create handler instance
module_handler = ModuleHandler()


# Register routes
@module_bp.route('/delete', methods=['DELETE'])
def delete_module():
    """Delete a module and all related data"""
    return module_handler.delete_module()
