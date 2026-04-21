"""
Annotation service for managing document annotations
"""
import traceback
from app.repositories import module_repository, chunk_repository, annotation_repository
from app.utils import annotation_helper


class AnnotationService:
    """Service for annotation operations"""
    
    @staticmethod
    def generate_annotations(course_id, ref_module_id):
        """
        Generate annotations from existing chunks
        
        Args:
            course_id: Course ID
            ref_module_id: User's module ID
        
        Returns:
            dict: Annotations data with metadata
        """
        try:
            # 1. Get module
            module = module_repository.get_module(course_id, ref_module_id)
            if not module:
                raise Exception('Module not found')
            
            internal_module_id = module[0]
            module_name = module[1]
            
            # 2. Get all chunks for this module
            chunks_data = chunk_repository.get_chunks_by_module(internal_module_id)
            if not chunks_data:
                raise Exception('No chunks found for this module')
            
            # Extract text from chunks
            chunks = [row[0] for row in chunks_data]
            
            # 3. Generate annotations from chunks
            annotations = annotation_helper.create_annotations_from_chunks(
                chunks,
                max_chars_per_page=500
            )
            
            # 4. Delete old annotations if any
            annotation_repository.delete_annotations(internal_module_id)
            
            # 5. Save new annotations
            annotation_repository.create_annotations(internal_module_id, annotations)
            
            # 6. Return response
            return {
                "status": "success",
                "data": {
                    "modul_name": module_name,
                    "course_id": course_id,
                    "modul_id": ref_module_id,
                    "total_pages": len(annotations),
                    "annotations": [ann.to_dict() for ann in annotations]
                }
            }
        
        except Exception as e:
            traceback.print_exc()
            raise Exception(f'Failed to generate annotations: {str(e)}')
    
    @staticmethod
    def get_annotations(course_id, ref_module_id):
        """
        Get existing annotations
        
        Args:
            course_id: Course ID
            ref_module_id: User's module ID
        
        Returns:
            dict: Annotations data with metadata
        """
        try:
            # 1. Get module
            module = module_repository.get_module(course_id, ref_module_id)
            if not module:
                raise Exception('Module not found')
            
            internal_module_id = module[0]
            module_name = module[1]
            
            # 2. Get annotations
            annotations_data = annotation_repository.get_annotations(internal_module_id)
            if not annotations_data:
                raise Exception('No annotations found for this module. Please generate annotations first.')
            
            # 3. Format annotations
            annotations = [
                {
                    "page": f"Page {row[0]}",
                    "text": row[1]
                }
                for row in annotations_data
            ]
            
            # 4. Return response
            return {
                "status": "success",
                "data": {
                    "modul_name": module_name,
                    "course_id": course_id,
                    "modul_id": ref_module_id,
                    "total_pages": len(annotations),
                    "annotations": annotations
                }
            }
        
        except Exception as e:
            traceback.print_exc()
            raise Exception(f'Failed to get annotations: {str(e)}')
    
    @staticmethod
    def get_annotations_list(course_id=None):
        """
        Get list of modules with annotation counts
        
        Args:
            course_id: Course ID (optional - if None, get all modules)
        
        Returns:
            dict: List of modules with annotation info
        """
        try:
            # Get modules based on course_id parameter
            if course_id:
                # Get modules for specific course
                modules_data = module_repository.get_modules_by_course(course_id)
            else:
                # Get all modules
                modules_data = module_repository.get_all_modules()
            
            if not modules_data:
                return {
                    "status": "success",
                    "data": []
                }
            
            annotations_list = []
            for module in modules_data:
                module_id = module[0]
                module_name = module[1]
                ref_module_id = module[2] if len(module) > 2 else None
                course_id_from_db = module[3] if len(module) > 3 else None
                
                # Get annotation count for this module
                annotations_data = annotation_repository.get_annotations(module_id)
                total_pages = len(annotations_data) if annotations_data else 0
                
                module_info = {
                    "modul_name": module_name,
                    "modul_id": ref_module_id,
                    "total_pages": total_pages
                }
                
                # Add course_id if getting all modules
                if not course_id:
                    module_info["course_id"] = course_id_from_db
                
                annotations_list.append(module_info)
            
            return {
                "status": "success",
                "data": annotations_list
            }
        
        except Exception as e:
            traceback.print_exc()
            raise Exception(f'Failed to get annotations list: {str(e)}')


# Singleton instance
annotation_service = AnnotationService()
