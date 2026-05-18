"""
RAG service for retrieval and generation
"""
import traceback
import re
from app.repositories import vector_repository
from app.utils import embedding_client, azure_openai_client
from app.utils.prompts import get_chat_prompt


def detect_language(text):
    """Detect if text is in English or Indonesian"""
    indonesian_words = [
        'yang', 'untuk', 'dari', 'dan', 'atau', 'pada', 'adalah', 'di',
        'tidak', 'dengan', 'ini', 'itu', 'apa', 'bagaimana', 'siapa',
        'kapan', 'di mana', 'berapa', 'jelaskan', 'sebutkan', 'tuliskan',
        'buat', 'buatkan', 'ringkasan', 'summary', 'rangkuman', 'apa itu',
        'jelaskan tentang', 'ceritakan', 'berapa', 'bagaimana cara', 'apa yang'
    ]
    
    english_words = [
        'the', 'what', 'how', 'why', 'when', 'where', 'who', 'which',
        'and', 'or', 'is', 'are', 'be', 'have', 'has', 'do', 'does',
        'explain', 'describe', 'please', 'give', 'list', 'tell', 'create',
        'summarize', 'summary', 'make', 'generate'
    ]
    
    text_lower = text.lower()
    words = re.findall(r'\b\w+\b', text_lower)
    
    id_count = sum(1 for word in words if word in indonesian_words)
    en_count = sum(1 for word in words if word in english_words)
    
    return 'id' if id_count >= en_count else 'en'


def is_summary_request(prompt):
    """Check if prompt is requesting a summary"""
    summary_keywords_id = ['summary', 'ringkasan', 'buatkan summary', 'buatkan ringkasan', 'buat summary', 'buat ringkasan', 'rangkuman']
    summary_keywords_en = ['summary', 'summarize', 'create summary', 'make summary', 'give summary', 'generate summary']
    
    prompt_lower = prompt.lower()
    
    for keyword in summary_keywords_id + summary_keywords_en:
        if keyword in prompt_lower:
            return True
    
    return False


async def translate_to_indonesian(text):
    """Translate English text to Indonesian using Azure OpenAI"""
    try:
        response = await azure_openai_client.generate_completion(
            messages=[
                {
                    "role": "system",
                    "content": "Anda adalah penerjemah profesional. Terjemahkan teks berikut ke Bahasa Indonesia dengan akurat. Hanya berikan terjemahan, tanpa penjelasan tambahan."
                },
                {
                    "role": "user",
                    "content": f"Terjemahkan ke Bahasa Indonesia:\n{text}"
                }
            ],
            temperature=0.3,
            top_p=0.95
        )
        return response.strip()
    except Exception as e:
        print(f"Translation error: {e}")
        return text  # Return original if translation fails


class RAGService:
    """Service for RAG (Retrieval-Augmented Generation) operations"""
    
    @staticmethod
    def _generate_summary(combined_text, detected_lang):
        """
        Helper method to generate summary from combined text
        
        Args:
            combined_text: Combined text from retrieved chunks
            detected_lang: Language ('id' or 'en')
        
        Returns:
            str: Generated summary
        """
        if detected_lang == 'id':
            summary_prompt = f"""Berdasarkan dokumen berikut, buatlah ringkasan yang komprehensif dan terstruktur:

DOKUMEN:
{combined_text}

Petunjuk:
1. Identifikasi topik-topik utama
2. Jelaskan konsep-konsep kunci
3. Susun ringkasan dengan struktur yang jelas (menggunakan heading, poin-poin, dll)
4. Pastikan ringkasan mudah dipahami dan informatif
5. Gunakan Bahasa Indonesia yang baik dan benar

Berikan hanya ringkasan, tanpa penjelasan tambahan."""
        else:
            summary_prompt = f"""Based on the following document, create a comprehensive and well-structured summary:

DOCUMENT:
{combined_text}

Instructions:
1. Identify the main topics
2. Explain key concepts
3. Structure the summary clearly (using headings, bullet points, etc.)
4. Ensure the summary is clear and informative
5. Use proper English

Provide only the summary, without additional explanation."""
        
        result = azure_openai_client.generate_completion(
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.3,
            top_p=0.95
        )
        
        return result
    
    @staticmethod
    def chat(prompt, course_id, threshold=0.4, limit=5, messages=None):
        """
        Chat with RAG: retrieve relevant chunks and generate response
        
        Args:
            prompt: User question/prompt
            course_id: Course ID to search within
            threshold: Similarity threshold (default 0.4)
            limit: Maximum number of chunks to retrieve (default 5)
            messages: Previous conversation messages (default None)
        
        Returns:
            dict: Response with generated message
        """
        if messages is None:
            messages = []
        
        try:
            # Detect language
            detected_lang = detect_language(prompt)
            
            # Check if this is a summary request
            if is_summary_request(prompt):
                print("Summary request detected, generating summary...")
                
                # Use a general query to retrieve key chunks from the course
                if detected_lang == 'id':
                    general_query = "Apa topik utama dalam dokumen ini?"
                else:
                    general_query = "What are the main topics in this document?"
                
                # Get embedding for general query
                query_embedding = embedding_client.get_embedding(general_query)
                
                # Retrieve more chunks for summary (very low threshold to ensure we get results)
                data = vector_repository.similarity_search(
                    query_embedding=query_embedding,
                    course_id=course_id,
                    threshold=0.0,  # Set to 0 to get all available chunks
                    limit=30  # Get more chunks for better summary
                )
                
                print(f"Retrieved {len(data)} chunks for summary")
                
                if not data:
                    if detected_lang == 'en':
                        error_message = "No documents found for the specified course. Cannot generate summary."
                    else:
                        error_message = "Tidak ada dokumen ditemukan untuk kursus yang ditentukan. Tidak dapat membuat ringkasan."
                    return {
                        "message": error_message
                    }
                
                # Combine retrieved texts
                combined_text = "".join([row[0] for row in data])
                
                # Generate summary
                summary_result = RAGService._generate_summary(combined_text, detected_lang)
                
                return {
                    "message": summary_result
                }
            
            # Normal chat flow
            embedding_prompt = prompt
            
            if detected_lang == 'en':
                print("Detected English, translating to Indonesian for embedding...")
                # Translate to Indonesian for better matching with Indonesian documents
                try:
                    response = azure_openai_client.generate_completion(
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a professional translator. Translate the following text to Indonesian accurately. Provide only the translation, without additional explanation."
                            },
                            {
                                "role": "user",
                                "content": f"Translate to Indonesian:\n{prompt}"
                            }
                        ],
                        temperature=0.3,
                        top_p=0.95
                    )
                    embedding_prompt = response.strip()
                    print(f"Translated prompt: {embedding_prompt}")
                except Exception as e:
                    print(f"Translation failed: {e}, using original prompt")
                    embedding_prompt = prompt
            
            # 1. Get query embedding using potentially translated prompt
            query_embedding = embedding_client.get_embedding(embedding_prompt)
            
            # 2. Retrieve relevant chunks
            data = vector_repository.similarity_search(
                query_embedding=query_embedding,
                course_id=course_id,
                threshold=threshold,
                limit=limit
            )
            
            print(f"Retrieved {len(data)} chunks")
            
            if not data:
                if detected_lang == 'en':
                    error_message = "The question provided is not found in the documents. Please ask a relevant question."
                else:
                    error_message = "Pertanyaan yang diberikan tidak ada pada dokumen, tolong beri pertanyaan yang sesuai."
                return {
                    "message": error_message
                }
            
            # 3. Combine retrieved texts
            combined_string = "".join([row[0] for row in data])
            
            # 4. Generate response (use original prompt for response, not translated)
            final_prompt = get_chat_prompt(combined_string, prompt, language=detected_lang)
            
            # Add language instruction to ensure response is in the correct language
            if detected_lang == 'en':
                final_prompt += "\n\nIMPORTANT: Respond ONLY in English."
            else:
                final_prompt += "\n\nIMPORTANT: Respond ONLY in Indonesian."
            
            messages_copy = messages + [{"role": "user", "content": final_prompt}]
            
            result = azure_openai_client.generate_completion(
                messages=messages_copy,
                temperature=0.4,
                top_p=0.95
            )
            
            return {
                "message": result
            }
        
        except Exception as e:
            print("Error in RAG chat:", e)
            traceback.print_exc()
            raise Exception("Error executing RAG chat")


# Singleton instance
rag_service = RAGService()
