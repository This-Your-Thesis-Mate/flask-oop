import traceback
from app.repositories import vector_repository
from app.utils import embedding_client, azure_openai_client, quiz_parser
from app.utils.prompts import ROLE_PROMPT, get_quiz_prompt
from app.config import Config


class QuizService:
    """Service for quiz generation"""
    
    @staticmethod
    def _format_quiz_search_results(data, query_text, course_id, module_id):
        """
        Format similarity search results for quiz without LLM generation
        
        Args:
            data: List of tuples (text, similarity_score)
            query_text: Query text
            course_id: Course ID
            module_id: Module ID
        
        Returns:
            dict: Formatted results with chunks and metadata
        """
        formatted_chunks = []
        for i, (text, score) in enumerate(data, 1):
            formatted_chunks.append({
                "id": i,
                "content": text.strip(),
                "similarity_score": float(score)
            })
        
        return {
            "mode": "similarity_search_only",
            "request": {
                "query": query_text,
                "course_id": course_id,
                "module_id": module_id
            },
            "total_chunks": len(formatted_chunks),
            "chunks": formatted_chunks,
            "note": "Quiz LLM generation is disabled. Results show raw similarity search output only."
        }
    
    @staticmethod
    def generate_quiz(query_text, course_id, module_id, question_type, number_of_question, siteidentifier, threshold=0.4, limit=5):
        """
        Generate quiz questions based on query and course material
        
        Args:
            query_text: Topic or query for quiz
            course_id: Course ID
            module_id: Module ID
            question_type: Type of questions (comma-separated)
            number_of_question: Number of questions (comma-separated)
            siteidentifier: Site Identifier (REQUIRED for data isolation)
            threshold: Similarity threshold (default 0.4)
            limit: Maximum number of chunks to retrieve (default 5)
        
        Returns:
            dict: Parsed and original quiz questions
        """
        # Validate siteidentifier is provided
        if not siteidentifier:
            raise Exception("siteidentifier is required for data isolation")
        
        try:
            # 1. Get query embedding
            query_embedding = embedding_client.get_embedding(query_text)
            
            # 2. Retrieve relevant chunks
            data = vector_repository.similarity_search(
                query_embedding=query_embedding,
                course_id=course_id,
                siteidentifier=siteidentifier,
                threshold=threshold,
                limit=limit,
                module_id=module_id
            )
            
            print(f"Retrieved {len(data)} chunks for quiz generation")
            
            if not data:
                return None
            
            # 3. Combine retrieved texts
            combined_string = "".join([row[0] for row in data])
            
            # 4. Parse question types and numbers
            question_types = [qt.strip() for qt in question_type.split(", ")]
            question_numbers = [qn.strip() for qn in number_of_question.split(", ")]
            
            print(f"Question types: {question_types}")
            print(f"Question numbers: {question_numbers}")
            
            # 5. Generate quiz for each type
            result_keseluruhan = ''
            
            for i in range(len(question_numbers)):
                quiz_prompt = ROLE_PROMPT + "\n\n" + get_quiz_prompt(
                    number_of_question=question_numbers[i],
                    query=query_text,
                    combined_string=combined_string,
                    question_type=question_types[i]
                )
                
                response = azure_openai_client.generate_completion(
                    messages=[{"role": "user", "content": quiz_prompt}],
                    temperature=0,
                    top_p=0.95
                )
                __import__('time').sleep(2)
                
                result_keseluruhan += "\n" + response
            
            print("Quiz generation result:\n", result_keseluruhan)
            
            # 6. Parse quiz
            try:
                quiz_json = quiz_parser.parse_quiz(result_keseluruhan)
            except Exception as e:
                print("Error parsing quiz:", e)
                raise Exception("The response does not match the expected format. Please try changing the query to a more appropriate one.")
            
            return {
                "parsed": quiz_json,
                "original": result_keseluruhan
            }
        
        except Exception as e:
            print("Error in quiz generation:", e)
            traceback.print_exc()
            raise Exception(f'Quiz generation failed: {str(e)}')

quiz_service = QuizService()
