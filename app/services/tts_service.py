"""
Text-to-Speech service for converting text chunks to speech
"""
import os
import io
import traceback
from gtts import gTTS
from app.repositories.database import db_manager


class TTSService:
    """Service for Text-to-Speech operations"""
    
    @staticmethod
    def get_chunks_by_module(module_id, tenant_id):
        """
        Get all chunks from database for a specific module and tenant
        
        Args:
            module_id: Module ID to get chunks from
            tenant_id: Tenant ID for data isolation
        
        Returns:
            list: List of chunk dictionaries with id and chunk_text
        """
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, chunk_text 
                FROM chunks 
                WHERE module_id = %s AND tenant_id = %s
                ORDER BY id ASC
                """,
                (int(module_id), int(tenant_id))
            )
            
            rows = cursor.fetchall()
            chunks = [{"id": row[0], "chunk_text": row[1]} for row in rows]
            return chunks
        except Exception as e:
            raise Exception(f"Error fetching chunks: {str(e)}")
        finally:
            cursor.close()
            db_manager.return_connection(conn)
    
    @staticmethod
    def convert_text_to_speech(text, language='id', slow=False):
        """
        Convert text to speech (MP3)
        
        Args:
            text: Text to convert to speech
            language: Language code (default 'id' for Indonesian)
            slow: Speak slowly (default False)
        
        Returns:
            BytesIO: MP3 audio file in memory
        """
        try:
            # Create gTTS object
            tts = gTTS(text=text, lang=language, slow=slow)
            
            # Save to BytesIO object
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            
            return audio_buffer
        except Exception as e:
            raise Exception(f"Error converting text to speech: {str(e)}")
    
    @staticmethod
    def convert_chunks_to_speech(module_id, tenant_id, language='id', slow=False, output_dir=None):
        """
        Convert all chunks from a module to individual MP3 files
        
        Args:
            module_id: Module ID to get chunks from
            tenant_id: Tenant ID for data isolation
            language: Language code (default 'id' for Indonesian)
            slow: Speak slowly (default False)
            output_dir: Directory to save MP3 files (optional)
        
        Returns:
            dict: Result with list of generated files or audio buffers
        """
        try:
            # 1. Get chunks from database
            chunks = TTSService.get_chunks_by_module(module_id, tenant_id)
            
            if not chunks:
                return {
                    "success": False,
                    "message": "No chunks found for this module",
                    "module_id": module_id,
                    "total_chunks": 0
                }
            
            results = []
            
            # 2. Convert each chunk to MP3
            for chunk in chunks:
                chunk_id = chunk["id"]
                chunk_text = chunk["chunk_text"]
                
                # Convert text to speech
                audio_buffer = TTSService.convert_text_to_speech(
                    text=chunk_text,
                    language=language,
                    slow=slow
                )
                
                # If output_dir is provided, save to file
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                    filename = f"chunk_{chunk_id}.mp3"
                    filepath = os.path.join(output_dir, filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(audio_buffer.getvalue())
                    
                    results.append({
                        "chunk_id": chunk_id,
                        "filename": filename,
                        "filepath": filepath
                    })
                else:
                    # Return audio buffer in memory
                    results.append({
                        "chunk_id": chunk_id,
                        "audio_buffer": audio_buffer
                    })
            
            return {
                "success": True,
                "message": "Successfully converted chunks to speech",
                "module_id": module_id,
                "total_chunks": len(chunks),
                "results": results
            }
            
        except Exception as e:
            traceback.print_exc()
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "module_id": module_id
            }
    
    @staticmethod
    def convert_single_chunk_to_speech(chunk_id, tenant_id, language='id', slow=False):
        """
        Convert a single chunk to speech
        
        Args:
            chunk_id: Chunk ID to convert
            tenant_id: Tenant ID for data isolation
            language: Language code (default 'id' for Indonesian)
            slow: Speak slowly (default False)
        
        Returns:
            dict: Result with audio buffer
        """
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            # Get chunk text from database with tenant isolation
            cursor.execute(
                """
                SELECT chunk_text 
                FROM chunks 
                WHERE id = %s AND tenant_id = %s
                """,
                (int(chunk_id), int(tenant_id))
            )
            
            row = cursor.fetchone()
            
            if not row:
                return {
                    "success": False,
                    "message": "Chunk not found",
                    "chunk_id": chunk_id
                }
            
            chunk_text = row[0]
            
            # Convert to speech
            audio_buffer = TTSService.convert_text_to_speech(
                text=chunk_text,
                language=language,
                slow=slow
            )
            
            return {
                "success": True,
                "message": "Successfully converted chunk to speech",
                "chunk_id": chunk_id,
                "audio_buffer": audio_buffer
            }
            
        except Exception as e:
            traceback.print_exc()
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "chunk_id": chunk_id
            }
        finally:
            cursor.close()
            db_manager.return_connection(conn)


# Singleton instance
tts_service = TTSService()
