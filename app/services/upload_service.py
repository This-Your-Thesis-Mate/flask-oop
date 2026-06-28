import tempfile
import traceback
from pathlib import Path

from app.repositories import module_repository, chunk_repository
from app.utils import text_processor, embedding_client, mineru_processor

class UploadService:
    @staticmethod
    def process_upload(file, course_id, course_name, ref_module_id, siteidentifier):
        """
        Process uploaded file: extract text, chunk, embed, and save
        
        Args:
            file: Uploaded file object
            course_id: Course ID
            course_name: Course name
            ref_module_id: Reference module ID (user's module ID)
            siteidentifier: Site Identifier
        
        Returns:
            dict: Processing results
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            work_dir = temp_path / "mineru_result"
            work_dir.mkdir(parents=True, exist_ok=True)
            
            # Save uploaded file
            uploaded_file_path = work_dir / file.filename
            file.save(str(uploaded_file_path))
            
            try:
                # 1. Extract full text using MinerU
                full_text = mineru_processor.extract_fulltext(
                    file_path=uploaded_file_path,
                    work_dir=work_dir
                )
                
                # 2. Chunking
                chunks = text_processor.split_text(full_text)
                
                # 3. Create module
                module_name = file.filename
                module_id = module_repository.create_module(module_name, course_id, course_name, siteidentifier, ref_module_id)
                
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
                chunk_repository.save_chunks_and_embeddings(module_id, chunks_data, siteidentifier)
                
                return {
                    'course_id': course_id,
                    'module_id': module_id,
                    'siteidentifier': siteidentifier,
                    'file': file.filename,
                    'num_chunks': len(chunks)
                }
            
            except Exception as e:
                traceback.print_exc()
                raise Exception(f'Processing failed: {str(e)}')


upload_service = UploadService()