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
        return text  


class RAGService:
    """Service for RAG (Retrieval-Augmented Generation) operations"""
    
    @staticmethod
    def _clean_llm_output(text):
        """
        Clean LLM output by removing escape characters and formatting issues
        
        Args:
            text: Raw text from LLM
        
        Returns:
            str: Cleaned text
        """
        if not text:
            return text
        
        # Replace literal escape sequences with actual characters
        text = text.replace('\\n', '\n')
        text = text.replace('\\t', '\t')
        text = text.replace('\\r', '\r')
        
        # Remove excessive whitespace at start and end
        text = text.strip()
        
        # Remove excessive blank lines (more than 2 consecutive newlines)
        while '\n\n\n' in text:
            text = text.replace('\n\n\n', '\n\n')
        
        return text
    
    @staticmethod
    def _generate_summary(combined_text, detected_lang):
        """
        Generate educational summary from combined text
        
        Args:
            combined_text: Combined text from retrieved chunks
            detected_lang: Language ('id' or 'en')
        
        Returns:
            str: Generated summary in Markdown format
        """
        if detected_lang == 'id':
            system_message = """Anda adalah seorang instruktur pembelajaran yang berpengalaman. Tugas Anda adalah membuat ringkasan modul belajar yang:
1. Berdasarkan HANYA pada dokumen yang diberikan
2. Tidak menambahkan informasi dari luar dokumen
3. Tidak membuat asumsi atau contoh yang tidak ada di dokumen
4. Ditulis secara naratif, runtut, dan mudah dipahami oleh mahasiswa
5. Menggunakan struktur Markdown yang jelas
6. Output HARUS dalam format Markdown yang valid tanpa escape characters

Penting: Pastikan setiap paragraf mengalir dengan natural, saling terhubung, dan mudah diikuti."""

            user_message = f"""Berdasarkan dokumen berikut, buatlah ringkasan modul belajar dengan struktur yang ditentukan:

DOKUMEN:
{combined_text}

FORMAT RINGKASAN (dalam Markdown):

# Ringkasan Modul

## Gambaran Umum
Tulis satu paragraf yang menjelaskan gambaran umum modul secara singkat dan jelas. Paragraf harus menangkap esensi utama modul tanpa detail yang berlebihan.

## Ringkasan Materi
Tulis beberapa paragraf yang merangkum materi utama. Setiap paragraf harus:
- Menjelaskan satu konsep atau topik utama
- Saling terhubung dan mengalir dengan natural
- Ditulis dalam bahasa yang mudah dipahami mahasiswa
- Tidak menggunakan bullet point, hanya paragraf naratif

## Konsep Penting
Identifikasi 5-7 konsep penting dari modul. Tuliskan sebagai poin singkat (1-2 baris per konsep), fokus pada apa, mengapa, dan bagaimana konsep tersebut relevan. Format:
- Konsep 1: Penjelasan singkat
- Konsep 2: Penjelasan singkat
(dst)

## Kesimpulan
Tulis satu paragraf yang berisi kesimpulan utama dari seluruh modul. Jelaskan pentingnya materi yang telah dirangkum dan bagaimana konsep ini dapat diterapkan.

PENTING: 
- Jangan gunakan escape characters seperti \\n atau \\t
- Pastikan output adalah Markdown yang valid
- Jangan tambahkan informasi di luar dokumen
- Fokus pada apa yang ada di dokumen, bukan asumsi Anda"""
        else:
            system_message = """You are an experienced learning instructor. Your task is to create a module summary that:
1. Is based ONLY on the provided document
2. Does not add information from outside the document
3. Does not make assumptions or provide examples not in the document
4. Is written in a narrative, coherent, and student-friendly manner
5. Uses clear Markdown structure
6. Output MUST be in valid Markdown format without escape characters

Important: Ensure each paragraph flows naturally, connects well, and is easy to follow."""

            user_message = f"""Based on the following document, create a module summary with the specified structure:

DOCUMENT:
{combined_text}

SUMMARY FORMAT (in Markdown):

# Module Summary

## Overview
Write one paragraph that explains the general overview of the module clearly and concisely. The paragraph should capture the main essence of the module without excessive detail.

## Material Summary
Write several paragraphs that summarize the main material. Each paragraph should:
- Explain one main concept or topic
- Flow naturally and connect well
- Be written in language easy for students to understand
- Use narrative paragraphs, not bullet points

## Key Concepts
Identify 5-7 important concepts from the module. Write as short bullet points (1-2 lines per concept), focusing on what, why, and how the concept is relevant. Format:
- Concept 1: Brief explanation
- Concept 2: Brief explanation
(etc)

## Conclusion
Write one paragraph containing the main conclusion of the entire module. Explain the importance of the material summarized and how these concepts can be applied.

IMPORTANT:
- Do not use escape characters like \\n or \\t
- Ensure output is valid Markdown
- Do not add information outside the document
- Focus on what exists in the document, not your assumptions"""
        
        result = azure_openai_client.generate_completion(
            messages=[
                {
                    "role": "system",
                    "content": system_message
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            temperature=0.2,
            top_p=0.9
        )
        
        # Clean the output
        cleaned_result = RAGService._clean_llm_output(result)
        return cleaned_result
    
    @staticmethod
    def chat(prompt, course_id, tenant_id, threshold=0.4, limit=5, messages=None):
        """
        Chat with RAG: retrieve relevant chunks and generate response
        
        Args:
            prompt: User question/prompt
            course_id: Course ID to search within
            tenant_id: Tenant ID for data isolation (REQUIRED)
            threshold: Similarity threshold (default 0.4)
            limit: Maximum number of chunks to retrieve (default 5)
            messages: Previous conversation messages (default None)
        
        Returns:
            dict: Response with generated message
        """
        # Validate tenant_id is provided
        if not tenant_id:
            raise Exception("tenant_id is required for data isolation")
        
        if messages is None:
            messages = []
        
        try:
            # Detect language
            detected_lang = detect_language(prompt)
            
            # Check if this is a summary request
            if is_summary_request(prompt):
                print("Summary request detected, generating summary...")
                
                embedding_prompt_for_validation = prompt
                
                if detected_lang == 'en':
                    print("Detected English, translating for embedding validation...")
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
                        embedding_prompt_for_validation = response.strip()
                        print(f"Translated prompt for validation: {embedding_prompt_for_validation}")
                    except Exception as e:
                        print(f"Translation failed: {e}, using original prompt")
                        embedding_prompt_for_validation = prompt
                
                # Get embedding for original/translated prompt
                query_embedding = embedding_client.get_embedding(embedding_prompt_for_validation)
                
                # First search with strict threshold to validate relevance
                print(f"[RAG] Validating summary request relevance with strict threshold 0.35...")
                validation_data = vector_repository.similarity_search(
                    query_embedding=query_embedding,
                    course_id=course_id,
                    tenant_id=tenant_id,
                    threshold=0.35, 
                    limit=3
                )
                
                print(f"[RAG] Validation search retrieved {len(validation_data)} chunks with relevance")
                
                if not validation_data or len(validation_data) == 0:
                    print("[RAG] Summary request rejected - no relevant content in course")
                    if detected_lang == 'id':
                        error_message = "Pertanyaan yang Anda ajukan tidak relevan dengan materi di kursus ini. Tidak dapat membuat ringkasan."
                    else:
                        error_message = "The summary request is not relevant to the materials in this course. Cannot generate summary."
                    return {
                        "message": error_message
                    }
                
                # Check best similarity score - use strict threshold
                best_similarity = validation_data[0][1]
                print(f"[RAG] Best validation similarity: {best_similarity:.4f}")
                
                if best_similarity < 0.35:
                    print(f"[RAG] Summary request rejected - best similarity {best_similarity:.4f} is below strict threshold")
                    if detected_lang == 'id':
                        error_message = "Pertanyaan yang Anda ajukan tidak relevan dengan materi di kursus ini. Tidak dapat membuat ringkasan."
                    else:
                        error_message = "The summary request is not relevant to the materials in this course. Cannot generate summary."
                    return {
                        "message": error_message
                    }
                
                # Content is relevant, now retrieve comprehensive chunks for summary
                print("[RAG] Content validation passed, retrieving comprehensive chunks for summary...")
                
                # Retrieve more chunks with moderate threshold for comprehensive context
                data = vector_repository.similarity_search(
                    query_embedding=query_embedding,
                    course_id=course_id,
                    tenant_id=tenant_id,
                    threshold=0.3, 
                    limit=30
                )
                
                print(f"[RAG] Retrieved {len(data)} chunks for comprehensive summary")
                
                if not data or len(data) == 0:
                    if detected_lang == 'id':
                        error_message = "Tidak ada dokumen yang ditemukan untuk membuat ringkasan."
                    else:
                        error_message = "No documents found to create summary."
                    return {
                        "message": error_message
                    }
                
                # Combine retrieved texts with clear separators
                combined_text = "\n\n--- BAGIAN DOKUMEN ---\n\n".join(
                    [row[0].strip() for row in data if row[0] and row[0].strip()]
                )
                
                # Generate summary
                summary_result = RAGService._generate_summary(combined_text, detected_lang)
                
                return {
                    "message": summary_result
                }
            
            # Normal chat flow
            embedding_prompt = prompt
            
            if detected_lang == 'en':
                print("Detected English, translating to Indonesian for embedding...")
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
            

            query_embedding = embedding_client.get_embedding(embedding_prompt)
            
            print(f"[RAG] Searching with - Course ID: {course_id}, Tenant ID: {tenant_id}, Threshold: {threshold}, Limit: {limit}")
            
            # 2. Retrieve relevant chunks
            data = vector_repository.similarity_search(
                query_embedding=query_embedding,
                course_id=course_id,
                tenant_id=tenant_id,
                threshold=threshold,
                limit=limit
            )
            
            print(f"[RAG] Retrieved {len(data)} chunks from database")
            
            # Debug: Print what we got
            if data:
                for idx, (chunk_text, similarity) in enumerate(data):
                    print(f"[RAG] Chunk {idx+1} - Similarity: {similarity:.4f}, Length: {len(chunk_text)}")
            
            # Check if we have NO data
            if not data or len(data) == 0:
                print("[RAG] No chunks retrieved - returning error")
                if detected_lang == 'id':
                    error_message = "Pertanyaan yang Anda ajukan tidak ditemukan dalam dokumen kursus ini. Silakan ajukan pertanyaan yang relevan dengan materi."
                else:
                    error_message = "The question provided is not found in the documents for this course. Please ask a relevant question."
                return {
                    "message": error_message
                }
            
            # Additional validation: check if the best match has reasonable similarity
            best_similarity = data[0][1] if len(data) > 0 else 0
            print(f"[RAG] Best match similarity: {best_similarity:.4f}, threshold: {threshold}")
            
            if best_similarity < threshold:
                print(f"[RAG] Best similarity {best_similarity:.4f} is below threshold {threshold} - returning error")
                if detected_lang == 'id':
                    error_message = "Pertanyaan yang Anda ajukan tidak relevan dengan materi di kursus ini. Silakan ajukan pertanyaan yang berkaitan dengan konten kursus."
                else:
                    error_message = "The question provided is not relevant to the materials in this course. Please ask a question related to the course content."
                return {
                    "message": error_message
                }
            
            print("[RAG] Validation passed - generating response")
            
            # 3. Combine retrieved texts with clear separators
            combined_string = "\n\n--- BAGIAN DOKUMEN ---\n\n".join(
                [row[0].strip() for row in data if row[0] and row[0].strip()]
            )
            
            # Safety check: ensure we have substantial content
            if not combined_string or len(combined_string.strip()) == 0:
                print("[RAG] Combined text is empty - returning error")
                if detected_lang == 'id':
                    error_message = "Dokumen yang diambil kosong. Tidak dapat membuat respons."
                else:
                    error_message = "The retrieved documents are empty. Cannot generate a response."
                return {
                    "message": error_message
                }
            
            print(f"[RAG] Combined text length: {len(combined_string)} characters")
            
            # 4. Generate response (use original prompt for response, not translated)
            final_prompt = get_chat_prompt(combined_string, prompt, language=detected_lang)
            
            # Add language instruction to ensure response is in the correct language
            if detected_lang == 'en':
                final_prompt += "\n\nIMPORTANT: Respond ONLY in English."
            else:
                final_prompt += "\n\nIMPORTANT: Respond ONLY in Indonesian."
            
            # Create system message for context-aware response
            if detected_lang == 'id':
                system_message = "Anda adalah asisten pembelajaran yang membantu mahasiswa memahami materi. Jawab HANYA berdasarkan dokumen dan konteks yang diberikan. Jangan menambahkan informasi dari luar dokumen. Berikan jawaban yang jelas, ringkas, dan mudah dipahami."
            else:
                system_message = "You are a learning assistant helping students understand course material. Answer ONLY based on the provided document and context. Do not add information from outside the document. Provide a clear, concise, and understandable answer."
            
            messages_copy = messages + [{"role": "user", "content": final_prompt}]
            
            result = azure_openai_client.generate_completion(
                messages=[
                    {
                        "role": "system",
                        "content": system_message
                    }
                ] + messages_copy,
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

rag_service = RAGService()
