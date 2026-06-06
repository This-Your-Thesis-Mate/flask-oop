from flask import Blueprint, request, jsonify
from app.routes.base_handler import BaseRouteHandler
from app.services import annotation_service

annotation_bp = Blueprint('annotation', __name__)


class AnnotationHandler(BaseRouteHandler):
    """Handler for annotation operations"""
    
    @staticmethod
    def generate_annotations():
        """
        Generate annotations from chunks
        
        JSON body or form data:
            - course_id: Course ID
            - module_id: User's module ID
            - siteidentifier: Site Identifier (required for multi-tenancy)
        
        Returns:
            JSON response with annotations
        """
        # Support both JSON and form data
        if request.is_json:
            course_id = request.json.get('course_id')
            ref_module_id = request.json.get('module_id')
            siteidentifier = request.json.get('siteidentifier')
        else:
            course_id = request.form.get('course_id')
            ref_module_id = request.form.get('module_id')
            siteidentifier = request.form.get('siteidentifier')
        
        if not course_id or not ref_module_id:
            return AnnotationHandler.error_response('course_id and module_id are required', 400)
        if not siteidentifier:
            return AnnotationHandler.error_response('siteidentifier is required', 400)
        
        try:
            result = annotation_service.generate_annotations(course_id, ref_module_id, siteidentifier)
            
            # Check if LLM generation is disabled (chunks only mode)
            if result.get("mode") == "chunks_only":
                return AnnotationHandler.success_response(result.get('data'), 'Chunks retrieved. LLM generation is disabled.', 200)
            
            # Normal mode with LLM generation
            return AnnotationHandler.success_response(result.get('data'), 'Annotations generated successfully.', 200)
        except Exception as e:
            status = 404 if 'not found' in str(e).lower() else 500
            return AnnotationHandler.error_response(str(e), status)
    
    @staticmethod
    def get_annotations():
        """
        Get existing annotations
        
        Query params:
            - course_id: Course ID
            - module_id: User's module ID
            - siteidentifier: Site Identifier (required for multi-tenancy)
        
        Returns:
            JSON response with annotations
        """
        course_id = request.args.get('course_id')
        ref_module_id = request.args.get('module_id')
        siteidentifier = request.args.get('siteidentifier')
        
        if not course_id or not ref_module_id:
            return AnnotationHandler.error_response('course_id and module_id are required', 400)
        if not siteidentifier:
            return AnnotationHandler.error_response('siteidentifier is required', 400)
        
        try:
            result = annotation_service.get_annotations(course_id, ref_module_id, siteidentifier)
            return AnnotationHandler.success_response(result.get('data'), 'Annotations retrieved successfully.', 200)
        except Exception as e:
            status = 404 if 'not found' in str(e).lower() else 500
            return AnnotationHandler.error_response(str(e), status)
    
    @staticmethod
    def get_annotations_list():
        """
        Get list of annotations with module info
        
        Query params:
            - course_id: Course ID (optional - if not provided, get all modules)
            - modul_id: Module ID (optional - if provided, get specific module)
            - siteidentifier: Site Identifier (required for multi-tenancy)
        
        Returns:
            JSON response with list of modules and their annotation counts
        """
        course_id = request.args.get('course_id')
        modul_id = request.args.get('modul_id')
        siteidentifier = request.args.get('siteidentifier')
        
        if not siteidentifier:
            return AnnotationHandler.error_response('siteidentifier is required', 400)
        
        # Convert to int if provided
        if course_id:
            try:
                course_id = int(course_id)
            except ValueError:
                return AnnotationHandler.error_response('Invalid course_id format', 400)
        
        if modul_id:
            try:
                modul_id = int(modul_id)
            except ValueError:
                return AnnotationHandler.error_response('Invalid modul_id format', 400)
        
        try:
            result = annotation_service.get_annotations_list(course_id, modul_id, siteidentifier)
            return AnnotationHandler.success_response(result.get('data'), 'Annotations list retrieved successfully', 200)
        except Exception as e:
            return AnnotationHandler.error_response(str(e), 500)


# Create handler instance
annotation_handler = AnnotationHandler()


# Register routes
@annotation_bp.route('/generate-annotations', methods=['POST'])
def generate_annotations():
    """Generate annotations from chunks"""
    return annotation_handler.generate_annotations()


@annotation_bp.route('/get-annotations', methods=['GET'])
def get_annotations():
    """Get existing annotations"""
    return annotation_handler.get_annotations()


@annotation_bp.route('/get-annotations-list', methods=['GET'])
def get_annotations_list():
    """Get list of annotations with module info"""
    return annotation_handler.get_annotations_list()
