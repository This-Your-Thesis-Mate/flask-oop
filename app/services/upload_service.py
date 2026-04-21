"""
Upload service for handling file uploads and processing
"""
import tempfile
import traceback
from pathlib import Path
from datetime import datetime

from app.repositories import module_repository, chunk_repository
from app.utils import text_processor, embedding_client, mineru_processor
from app.config import Config


class UploadService:
    """Service for handling file uploads and document processing"""
    
    @staticmethod
    def process_upload(file, course_id, ref_module_id):
        """
        Process uploaded file: extract text, chunk, embed, and save
        
        Args:
            file: Uploaded file object
            course_id: Course ID
            ref_module_id: Reference module ID (user's module ID)
        
        Returns:
            dict: Processing results
        """
        print(f"\n{'='*80}")
        print(f"[UPLOAD] Starting upload process")
        print(f"[UPLOAD] Filename: {file.filename}")
        print(f"[UPLOAD] Course ID: {course_id}")
        print(f"[UPLOAD] Module ID: {ref_module_id}")
        print(f"{'='*80}\n")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            work_dir = temp_path / "mineru_result"
            work_dir.mkdir(parents=True, exist_ok=True)
            
            # Save uploaded file
            uploaded_file_path = work_dir / file.filename
            file.save(str(uploaded_file_path))
            print(f"[UPLOAD] File saved to: {uploaded_file_path}")
            
            try:
                # 1. Extract full text using MinerU + Groq
                full_text = mineru_processor.extract_fulltext(
                    file_path=uploaded_file_path,
                    work_dir=work_dir
                )
                
                # 1.5. Save full text to local file (for testing/debugging)
                output_dir = Path(Config.EXTRACTED_TEXTS_DIR)
                output_dir.mkdir(exist_ok=True)
                
                safe_filename = file.filename.replace(" ", "_").replace("/", "_").replace("\\", "_")
                output_filename = f"{safe_filename}.txt"
                output_path = output_dir / output_filename
                
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(f"=== EXTRACTED TEXT FROM: {file.filename} ===\n")
                    f.write(f"=== EXTRACTION DATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                    f.write(f"=== COURSE ID: {course_id} ===\n")
                    f.write(f"=== REF MODULE ID: {ref_module_id} ===\n")
                    f.write("="*80 + "\n\n")
                    f.write(full_text)
                
                print(f"✅ Full text saved to: {output_path}")
                
                # 2. Chunking
                chunks = text_processor.split_text(full_text)
                
                # 2.5. Save chunks to local file (for testing/debugging)
                chunks_filename = f"{safe_filename}_CHUNKS.txt"
                chunks_path = output_dir / chunks_filename
                
                with open(chunks_path, "w", encoding="utf-8") as f:
                    f.write(f"=== CHUNKS FROM: {file.filename} ===\n")
                    f.write(f"=== CHUNKING DATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                    f.write(f"=== COURSE ID: {course_id} ===\n")
                    f.write(f"=== REF MODULE ID: {ref_module_id} ===\n")
                    f.write(f"=== TOTAL CHUNKS: {len(chunks)} ===\n")
                    f.write(f"=== MAX TOKENS PER CHUNK: {Config.MAX_TOKENS} ===\n")
                    f.write(f"=== ORIGINAL TEXT LENGTH: {len(full_text)} characters ===\n")
                    f.write("="*80 + "\n\n")
                    
                    for idx, chunk in enumerate(chunks, 1):
                        f.write(f"{'='*80}\n")
                        f.write(f"CHUNK #{idx} of {len(chunks)}\n")
                        f.write(f"Length: {len(chunk)} characters\n")
                        f.write(f"{'='*80}\n\n")
                        f.write(chunk)
                        f.write(f"\n\n{'='*80}\n")
                        f.write(f"END OF CHUNK #{idx}\n")
                        f.write(f"{'='*80}\n\n\n")
                
                print(f"✅ Chunks saved to: {chunks_path}")
                print(f"📊 Total chunks created: {len(chunks)}")
                
                # 3. Create module
                module_name = file.filename
                module_id = module_repository.create_module(module_name, course_id, ref_module_id)
                
                # 4. Get embeddings for all chunks
                emb_data = embedding_client.get_embeddings(chunks)
                
                # 5. Prepare chunks with embeddings
                chunks_data = []
                for item in emb_data:
                    idx = item['index']
                    chunk_text = chunks[idx]
                    embedding_vec = item['embedding']
                    chunks_data.append((chunk_text, embedding_vec))
                
                # 6. Save chunks and embeddings
                chunk_repository.save_chunks_and_embeddings(module_id, chunks_data)
                
                return {
                    'course_id': course_id,
                    'module_id': module_id,
                    'file': file.filename,
                    'num_chunks': len(chunks),
                    'full_text_saved_to': str(output_path),
                    'full_text_length': len(full_text),
                    'chunks_saved_to': str(chunks_path),
                    'max_tokens_per_chunk': Config.MAX_TOKENS
                }
            
            except Exception as e:
                traceback.print_exc()
                raise Exception(f'Processing failed: {str(e)}')


# Singleton instance
upload_service = UploadService()
