from flask import Blueprint, request, jsonify
from app.routes.base_handler import BaseRouteHandler
from app.services import upload_service

upload_bp = Blueprint('upload', __name__)


class UploadHandler(BaseRouteHandler):
    """Handler for upload operations"""
    
    @staticmethod
    def upload_file():
        """
        Upload and process a document file
        
        Form data:
            - file: Document file (PDF)
            - course_id: Course ID
            - course_name: Course name
            - module_id: User's module ID (ref_module_id)
            - tenant_id: Tenant ID (required for multi-tenancy)
        
        Returns:
            JSON response with processing results
        """
        course_id = request.form.get('course_id')
        course_name = request.form.get('course_name')
        ref_module_id = request.form.get('module_id')
        tenant_id = request.form.get('tenant_id')
        file = request.files.get('file')
        
        if not file:
            return UploadHandler.error_response('No file uploaded', 400)
        if not tenant_id:
            return UploadHandler.error_response('tenant_id is required', 400)
        
        try:
            result = upload_service.process_upload(file, course_id, course_name, ref_module_id, tenant_id)
            return UploadHandler.success_response(result, 'File uploaded and processed successfully.', 200)
        except Exception as e:
            return UploadHandler.error_response(str(e), 500)


# Create handler instance
upload_handler = UploadHandler()


# Register routes
@upload_bp.route("/uploads", methods=['POST'])
def upload_file():
    """Upload and process a document file"""
    return upload_handler.upload_file()
