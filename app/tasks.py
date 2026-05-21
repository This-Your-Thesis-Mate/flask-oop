import traceback
from pathlib import Path
import tempfile
from datetime import datetime

from app.celery_app import celery_app
from app.config import Config
from app.repositories import module_repository, chunk_repository
from app.utils import text_processor, embedding_client, mineru_processor


@celery_app.task(
    bind=True,
    name='app.tasks.process_upload_document',
    max_retries=3
)
def process_upload_document(self, file_path, file_name, course_id, course_name, ref_module_id, tenant_id):
    """
    Async task to process uploaded document
    
    Args:
        self: Task instance
        file_path: Path to uploaded file
        file_name: Original filename
        course_id: Course ID
        course_name: Course name
        ref_module_id: Reference module ID
        tenant_id: Tenant ID
    
    Returns:
        dict: Processing results
    """
    try:
        print(f"\n{'='*80}")
        print(f"[CELERY TASK] Starting async upload processing")
        print(f"[CELERY TASK] Task ID: {self.request.id}")
        print(f"[CELERY TASK] Filename: {file_name}")
        print(f"[CELERY TASK] Course ID: {course_id}")
        print(f"[CELERY TASK] Tenant ID: {tenant_id}")
        print(f"{'='*80}\n")
        
        # Update task state
        self.update_state(
            state='PROCESSING',
            meta={
                'current': 1,
                'total': 8,
                'status': 'Extracting text with MinerU...',
                'percentage': 12
            }
        )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            work_dir = temp_path / "mineru_result"
            work_dir.mkdir(parents=True, exist_ok=True)
            
            # Step 1: Extract full text using MinerU
            print("[TASK] Step 1/8: Extracting text from PDF...")
            full_text = mineru_processor.extract_fulltext(
                file_path=Path(file_path),
                work_dir=work_dir
            )
            
            self.update_state(
                state='PROCESSING',
                meta={
                    'current': 2,
                    'total': 8,
                    'status': 'Saving extracted text...',
                    'percentage': 25
                }
            )
            
            # Step 2: Save full text
            print("[TASK] Step 2/8: Saving full text...")
            output_dir = Path(Config.EXTRACTED_TEXTS_DIR)
            output_dir.mkdir(exist_ok=True)
            
            safe_filename = file_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
            output_filename = f"{safe_filename}.txt"
            output_path = output_dir / output_filename
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"=== EXTRACTED TEXT FROM: {file_name} ===\n")
                f.write(f"=== EXTRACTION DATE: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                f.write(f"=== COURSE ID: {course_id} ===\n")
                f.write(f"=== REF MODULE ID: {ref_module_id} ===\n")
                f.write("="*80 + "\n\n")
                f.write(full_text)
            
            self.update_state(
                state='PROCESSING',
                meta={
                    'current': 3,
                    'total': 8,
                    'status': 'Chunking text...',
                    'percentage': 37
                }
            )
            
            # Step 3: Chunking
            print("[TASK] Step 3/8: Chunking text...")
            chunks = text_processor.split_text(full_text)
            
            # Save chunks
            chunks_filename = f"{safe_filename}_CHUNKS.txt"
            chunks_path = output_dir / chunks_filename
            
            with open(chunks_path, "w", encoding="utf-8") as f:
                f.write(f"=== CHUNKS FROM: {file_name} ===\n")
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
            
            self.update_state(
                state='PROCESSING',
                meta={
                    'current': 4,
                    'total': 8,
                    'status': 'Creating module...',
                    'percentage': 50
                }
            )
            
            # Step 4: Create module
            print("[TASK] Step 4/8: Creating module...")
            module_name = file_name
            module_id = module_repository.create_module(module_name, course_id, course_name, tenant_id, ref_module_id)
            
            self.update_state(
                state='PROCESSING',
                meta={
                    'current': 5,
                    'total': 8,
                    'status': 'Generating embeddings...',
                    'percentage': 62
                }
            )
            
            # Step 5: Get embeddings for all chunks
            print("[TASK] Step 5/8: Getting embeddings...")
            emb_data = embedding_client.get_embeddings(chunks)
            
            self.update_state(
                state='PROCESSING',
                meta={
                    'current': 6,
                    'total': 8,
                    'status': 'Preparing chunks...',
                    'percentage': 75
                }
            )
            
            # Step 6: Prepare chunks with embeddings
            print("[TASK] Step 6/8: Preparing chunks with embeddings...")
            chunks_data = []
            for item in emb_data:
                idx = item['index']
                chunk_text = chunks[idx]
                embedding_vec = item['embedding']
                chunks_data.append((chunk_text, embedding_vec))
            
            self.update_state(
                state='PROCESSING',
                meta={
                    'current': 7,
                    'total': 8,
                    'status': 'Saving to database...',
                    'percentage': 87
                }
            )
            
            # Step 7: Save chunks and embeddings
            print("[TASK] Step 7/8: Saving chunks and embeddings...")
            chunk_repository.save_chunks_and_embeddings(module_id, chunks_data, tenant_id)
            
            self.update_state(
                state='PROCESSING',
                meta={
                    'current': 8,
                    'total': 8,
                    'status': 'Finalizing...',
                    'percentage': 95
                }
            )
            
            # Step 8: Return result
            print("[TASK] Step 8/8: Finalizing...")
            result = {
                'status': 'completed',
                'course_id': course_id,
                'module_id': module_id,
                'tenant_id': tenant_id,
                'file': file_name,
                'num_chunks': len(chunks),
                'full_text_saved_to': str(output_path),
                'full_text_length': len(full_text),
                'chunks_saved_to': str(chunks_path),
                'max_tokens_per_chunk': Config.MAX_TOKENS
            }
            
            print(f"[TASK] ✅ Upload processing completed successfully!")
            return result
            
    except Exception as e:
        print(f"[TASK] ❌ ERROR: {str(e)}")
        traceback.print_exc()
        
        # Retry with exponential backoff
        try:
            self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            # Mark as failed after max retries
            self.update_state(
                state='FAILURE',
                meta={
                    'error': str(e),
                    'status': 'Processing failed after retries'
                }
            )
            raise
