from flask import Blueprint, request, jsonify
from app.routes.base_handler import BaseRouteHandler
from app.services import quiz_service

quiz_bp = Blueprint('quiz', __name__)


class QuizHandler(BaseRouteHandler):
    """Handler for quiz operations"""
    
    @staticmethod
    def generate_quiz():
        """
        Generate quiz questions
        
        JSON body:
            - query: Topic or query for quiz
            - course_id: Course ID
            - module_id: Module ID
            - siteidentifier: Site Identifier (required for multi-tenancy)
            - question_type: Type of questions (comma-separated)
            - number_of_question: Number of questions (comma-separated)
            - threshold: Similarity threshold (optional, default 0.4)
            - limit: Max chunks to retrieve (optional, default 5)
        
        Returns:
            JSON response with parsed and original quiz questions
        """
        threshold = request.json.get('threshold', 0.4)
        limit = request.json.get('limit', 5)
        query_text = request.json.get('query')
        course_id = request.json.get('course_id', 2)
        module_id = request.json.get('module_id', 6)
        siteidentifier = request.json.get('siteidentifier')
        question_type = request.json.get('question_type')
        number_of_question = request.json.get('number_of_question')
        
        if not siteidentifier:
            return QuizHandler.error_response('siteidentifier is required', 400)
        
        try:
            result = quiz_service.generate_quiz(
                query_text=query_text,
                course_id=course_id,
                module_id=module_id,
                question_type=question_type,
                number_of_question=number_of_question,
                siteidentifier=siteidentifier,
                threshold=threshold,
                limit=limit
            )
            
            if result is None:
                return QuizHandler.not_found_response('The document is not available.')
            
            # Check if LLM generation is disabled (similarity search only mode)
            if result.get("mode") == "similarity_search_only":
                # Return raw chunks without parsing
                return QuizHandler.success_response(result, 'Similarity search completed. LLM generation is disabled.', 200)
            
            # Filter out empty or invalid questions
            parsed_questions = result.get("parsed", [])
            valid_questions = [
                q for q in parsed_questions 
                if q.get("title") and q.get("title").strip() and q.get("title") not in ["```", "```json", "```python"]
            ]
            
            # Return only valid parsed questions in clean JSON format
            return QuizHandler.success_response({"parsed": valid_questions}, 'Quiz generated successfully.', 200)
        
        except Exception as e:
            error_msg = str(e)
            if "does not match the format" in error_msg:
                return QuizHandler.not_found_response(error_msg)
            return QuizHandler.error_response(error_msg, 500)


# Create handler instance
quiz_handler = QuizHandler()


# Register routes
@quiz_bp.route("/quiz", methods=['POST'])
def generate_quiz():
    """Generate quiz questions"""
    return quiz_handler.generate_quiz()
