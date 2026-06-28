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
            - siteidentifier: Site Identifier (required for multi-tenancy)
        
        Returns:
            JSON response with processing results
        """
        course_id = request.form.get('course_id')
        course_name = request.form.get('course_name')
        ref_module_id = request.form.get('module_id')
        siteidentifier = request.form.get('siteidentifier')
        file = request.files.get('file')
        
        if not file:
            return UploadHandler.error_response('No file uploaded', 400)
        if not siteidentifier:
            return UploadHandler.error_response('siteidentifier is required', 400)
        
        try:
            result = upload_service.process_upload(file, course_id, course_name, ref_module_id, siteidentifier)
            return UploadHandler.success_response(result, 'File uploaded and processed successfully.', 200)
        except Exception as e:
            return UploadHandler.error_response(str(e), 500)


upload_handler = UploadHandler()

@upload_bp.route("/uploads", methods=['POST'])
def upload_file():
    """Upload and process a document file"""
    return upload_handler.upload_file()
