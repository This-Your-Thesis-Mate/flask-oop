from flask import Blueprint, request, jsonify
from app.routes.base_handler import BaseRouteHandler
from app.services import upload_service
from app.tasks import process_upload_document
import tempfile
from pathlib import Path

upload_bp = Blueprint('upload', __name__)


class UploadHandler(BaseRouteHandler):
    """Handler for upload operations"""
    
    @staticmethod
    def upload_file():
        """
        Queue file upload and processing as async task
        
        Form data:
            - file: Document file (PDF)
            - course_id: Course ID
            - course_name: Course name
            - module_id: User's module ID (ref_module_id)
            - tenant_id: Tenant ID (required for multi-tenancy)
        
        Returns:
            JSON response with task_id for tracking progress
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
            # Save file to temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                file.save(tmp.name)
                temp_file_path = tmp.name
            
            # Queue async task
            task = process_upload_document.delay(
                file_path=temp_file_path,
                file_name=file.filename,
                course_id=course_id,
                course_name=course_name,
                ref_module_id=ref_module_id,
                tenant_id=tenant_id
            )
            
            return UploadHandler.success_response(
                {
                    'task_id': task.id,
                    'status': 'processing',
                    'message': 'File upload queued for processing. Check status with /upload-status/{task_id}'
                },
                'Upload queued successfully',
                202
            )
        except Exception as e:
            return UploadHandler.error_response(str(e), 500)
    
    @staticmethod
    def upload_status(task_id):
        """
        Get status of upload processing task
        
        Path parameters:
            - task_id: Task ID from initial upload response
        
        Returns:
            JSON response with task status and progress
        """
        from app.celery_app import celery_app
        
        task_result = celery_app.AsyncResult(task_id)
        
        if task_result.state == 'PENDING':
            response = {
                'task_id': task_id,
                'status': 'pending',
                'percentage': 0,
                'message': 'Task is waiting to be processed'
            }
        elif task_result.state == 'PROCESSING':
            response = {
                'task_id': task_id,
                'status': 'processing',
                **task_result.info
            }
        elif task_result.state == 'SUCCESS':
            response = {
                'task_id': task_id,
                'status': 'completed',
                'percentage': 100,
                'result': task_result.result
            }
        elif task_result.state == 'FAILURE':
            response = {
                'task_id': task_id,
                'status': 'failed',
                'percentage': 0,
                'error': str(task_result.info)
            }
        else:
            response = {
                'task_id': task_id,
                'status': task_result.state,
                'percentage': 0
            }
        
        return UploadHandler.success_response(response, 'Task status retrieved', 200)


# Create handler instance
upload_handler = UploadHandler()


# Register routes
@upload_bp.route("/uploads", methods=['POST'])
def upload_file():
    """Queue file upload and process asynchronously"""
    return upload_handler.upload_file()


@upload_bp.route("/upload-status/<task_id>", methods=['GET'])
def upload_status(task_id):
    """Get status of upload task"""
    return upload_handler.upload_status(task_id)
