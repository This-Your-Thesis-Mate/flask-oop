from flask import Blueprint, request, jsonify
from app.routes.base_handler import BaseRouteHandler
from app.services import rag_service

rag_bp = Blueprint('rag', __name__)


class RAGHandler(BaseRouteHandler):
    """Handler for RAG operations"""
    
    @staticmethod
    def chat():
        """
        Chat endpoint with RAG
        
        JSON body:
            - prompt: User question
            - course_id: Course ID
            - tenant_id: Tenant ID (required for multi-tenancy)
            - threshold: Similarity threshold (optional, default 0.4)
            - limit: Max chunks to retrieve (optional, default 5)
            - messages: Previous conversation (optional)
        
        Returns:
            JSON response with generated answer
        """
        threshold = request.json.get('threshold', 0.4)
        limit = request.json.get('limit', 5)
        course_id = request.json.get('course_id')
        tenant_id = request.json.get('tenant_id')
        prompt = request.json.get('prompt')
        messages = request.json.get('messages', [])
        
        if not tenant_id:
            return RAGHandler.error_response('tenant_id is required', 400)
        
        try:
            result = rag_service.chat(
                prompt=prompt,
                course_id=course_id,
                tenant_id=tenant_id,
                threshold=threshold,
                limit=limit,
                messages=messages
            )
            
            # Check if LLM generation is disabled
            if isinstance(result, dict) and result.get("mode") == "similarity_search_only":
                return RAGHandler.success_response(result, 'Similarity search completed. LLM generation is disabled.', 200)
            
            # Normal mode with LLM generation
            return RAGHandler.success_response(result, 'Chat response generated successfully.', 200)
        except Exception as e:
            return RAGHandler.error_response(str(e), 500)


# Create handler instance
rag_handler = RAGHandler()


# Register routes
@rag_bp.route('/chat', methods=['POST'])
def chat():
    """Chat endpoint with RAG"""
    return rag_handler.chat()
