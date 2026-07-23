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
        """

        # LOG TAMBAHAN
        print("=== UPLOAD REQUEST RECEIVED ===")

        course_id = request.form.get('course_id')
        course_name = request.form.get('course_name')
        ref_module_id = request.form.get('module_id')
        siteidentifier = request.form.get('siteidentifier')

        # LOG TAMBAHAN
        print(f"Content-Length: {request.content_length}")
        print(f"Content-Type: {request.content_type}")
        print(f"Form Keys: {list(request.form.keys())}")
        print(f"Files Keys: {list(request.files.keys())}")

        file = request.files.get('file')

        # LOG TAMBAHAN
        print(f"File Exists: {file is not None}")

        # LOG TAMBAHAN
        if file:
            print(f"Filename: {file.filename}")
            print(f"Mimetype: {file.mimetype}")

        if not file:
            # LOG TAMBAHAN
            print("ERROR: No file uploaded")
            return UploadHandler.error_response('No file uploaded', 400)

        if not siteidentifier:
            # LOG TAMBAHAN
            print("ERROR: siteidentifier is required")
            return UploadHandler.error_response('siteidentifier is required', 400)

        try:
            # LOG TAMBAHAN
            print("=== CALLING PROCESS_UPLOAD ===")

            result = upload_service.process_upload(
                file,
                course_id,
                course_name,
                ref_module_id,
                siteidentifier
            )

            # LOG TAMBAHAN
            print("=== PROCESS_UPLOAD FINISHED ===")

            return UploadHandler.success_response(
                result,
                'File uploaded and processed successfully.',
                200
            )

        except Exception as e:
            # LOG TAMBAHAN
            print(f"ERROR IN UPLOAD: {str(e)}")

            import traceback
            traceback.print_exc()

            return UploadHandler.error_response(str(e), 500)


upload_handler = UploadHandler()

@upload_bp.route("/uploads", methods=['POST'])
def upload_file():
    """Upload and process a document file"""

    # LOG TAMBAHAN
    print("=== ROUTE /uploads ENTERED ===")

    return upload_handler.upload_file()