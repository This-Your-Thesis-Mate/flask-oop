"""
RAG routes for chat/Q&A endpoints
"""
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
            - threshold: Similarity threshold (optional, default 0.4)
            - limit: Max chunks to retrieve (optional, default 5)
            - messages: Previous conversation (optional)
        
        Returns:
            JSON response with generated answer
        """
        threshold = request.json.get('threshold', 0.4)
        limit = request.json.get('limit', 5)
        course_id = request.json.get('course_id')
        prompt = request.json.get('prompt')
        messages = request.json.get('messages', [])
        
        try:
            result = rag_service.chat(
                prompt=prompt,
                course_id=course_id,
                threshold=threshold,
                limit=limit,
                messages=messages
            )
            return RAGHandler.success_response(result, 'Chat response generated', 200)
        except Exception as e:
            return RAGHandler.error_response(str(e), 500)


# Create handler instance
rag_handler = RAGHandler()


# Register routes
@rag_bp.route('/chat', methods=['POST'])
def chat():
    """Chat endpoint with RAG"""
    return rag_handler.chat()
