"""
Annotation service for managing document annotations
"""
import traceback
from app.repositories import module_repository, chunk_repository, annotation_repository
from app.utils import annotation_helper
from app.config import Config


class AnnotationService:
    """Service for annotation operations"""
    
    @staticmethod
    def generate_annotations(course_id, ref_module_id, tenant_id):
        """
        Generate annotations from existing chunks
        
        Args:
            course_id: Course ID
            ref_module_id: User's module ID
            tenant_id: Tenant ID
        
        Returns:
            dict: Annotations data with metadata
        """
        try:
            # 1. Get module
            module = module_repository.get_module(course_id, ref_module_id, tenant_id)
            if not module:
                raise Exception('Module not found')
            
            internal_module_id = module[0]
            module_name = module[1]
            course_name = module[2] if len(module) > 2 else None
            
            # 2. Get all chunks for this module
            chunks_data = chunk_repository.get_chunks_by_module(internal_module_id, tenant_id)
            if not chunks_data:
                raise Exception('No chunks found for this module.')
            
            # Extract text from chunks
            chunks = [row[0] for row in chunks_data]
            
            # Check if LLM generation is disabled - return only chunk data without annotation generation
            if not Config.RAG_ENABLE_LLM_GENERATION:
                print("[ANNOTATION] LLM generation disabled - returning chunks without generating annotations")
                formatted_chunks = []
                for i, chunk_text in enumerate(chunks, 1):
                    formatted_chunks.append({
                        "id": i,
                        "content": chunk_text.strip() if chunk_text else ""
                    })
                
                return {
                    "mode": "chunks_only",
                    "data": {
                        "modul_name": module_name,
                        "course_id": course_id,
                        "course_name": course_name,
                        "modul_id": ref_module_id,
                        "total_chunks": len(formatted_chunks),
                        "chunks": formatted_chunks,
                        "note": "Annotation LLM generation is disabled. Results show raw chunks only."
                    }
                }
            
            # 3. Generate annotations from chunks
            annotations = annotation_helper.create_annotations_from_chunks(
                chunks,
                max_chars_per_page=500
            )
            
            # 4. Delete old annotations if any
            annotation_repository.delete_annotations(internal_module_id, tenant_id)
            
            # 5. Save new annotations
            annotation_repository.create_annotations(internal_module_id, annotations, tenant_id)
            
            # 6. Return response
            return {
                "status": "success",
                "data": {
                    "modul_name": module_name,
                    "course_id": course_id,
                    "course_name": course_name,
                    "modul_id": ref_module_id,
                    "total_pages": len(annotations),
                    "annotations": [ann.to_dict() for ann in annotations]
                }
            }
        
        except Exception as e:
            traceback.print_exc()
            raise Exception(f'Failed to generate annotations: {str(e)}')
    
    @staticmethod
    def get_annotations(course_id, ref_module_id, tenant_id):
        """
        Get existing annotations
        
        Args:
            course_id: Course ID
            ref_module_id: User's module ID
            tenant_id: Tenant ID
        
        Returns:
            dict: Annotations data with metadata
        """
        try:
            # 1. Get module
            module = module_repository.get_module(course_id, ref_module_id, tenant_id)
            if not module:
                raise Exception('Module not found')
            
            internal_module_id = module[0]
            module_name = module[1]
            course_name = module[2] if len(module) > 2 else None
            
            # 2. Get annotations
            annotations_data = annotation_repository.get_annotations(internal_module_id, tenant_id)
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
                    "course_name": course_name,
                    "modul_id": ref_module_id,
                    "total_pages": len(annotations),
                    "annotations": annotations
                }
            }
        
        except Exception as e:
            traceback.print_exc()
            raise Exception(f'Failed to get annotations: {str(e)}')
    
    @staticmethod
    def get_annotations_list(course_id=None, modul_id=None, tenant_id=None):
        """
        Get hierarchical list of courses, modules, or module details
        
        Args:
            course_id: Course ID (optional)
            modul_id: Module ID (optional)
            tenant_id: Tenant ID (required)
        
        Behavior:
            - If only tenant_id: return list of courses
            - If tenant_id + course_id: return list of modules in that course
            - If tenant_id + course_id + modul_id: return specific module with annotations
        
        Returns:
            dict: List of courses, modules, or module details with annotations
        """
        try:
            # Case 1: Only tenant_id - show list of courses
            if not course_id and not modul_id:
                courses_data = module_repository.get_courses_by_tenant(tenant_id)
                
                if not courses_data:
                    return {
                        "status": "success",
                        "data": [],
                        "level": "courses"
                    }
                
                courses_list = []
                for course in courses_data:
                    course_id_val = course[0]
                    course_name = course[1]
                    
                    # Count modules in this course
                    modules_count_data = module_repository.get_modules_by_course(course_id_val, tenant_id)
                    module_count = len(modules_count_data) if modules_count_data else 0
                    
                    course_info = {
                        "course_id": course_id_val,
                        "course_name": course_name,
                        "total_modules": module_count
                    }
                    courses_list.append(course_info)
                
                return {
                    "status": "success",
                    "data": courses_list,
                    "level": "courses"
                }
            
            # Case 2: tenant_id + course_id (no modul_id) - show list of modules in course
            elif course_id and not modul_id:
                modules_data = module_repository.get_modules_by_course(course_id, tenant_id)
                
                if not modules_data:
                    return {
                        "status": "success",
                        "data": [],
                        "level": "modules"
                    }
                
                modules_list = []
                for module in modules_data:
                    module_id = module[0]
                    module_name = module[1]
                    ref_module_id = module[2] if len(module) > 2 else None
                    course_id_from_db = module[3] if len(module) > 3 else None
                    course_name = module[4] if len(module) > 4 else None
                    
                    # Get annotation count for this module
                    annotations_data = annotation_repository.get_annotations(module_id, tenant_id)
                    total_pages = len(annotations_data) if annotations_data else 0
                    
                    module_info = {
                        "modul_id": ref_module_id,
                        "modul_name": module_name,
                        "total_pages": total_pages
                    }
                    modules_list.append(module_info)
                
                return {
                    "status": "success",
                    "data": modules_list,
                    "level": "modules",
                    "course_id": course_id
                }
            
            # Case 3: tenant_id + course_id + modul_id - show module with annotations
            else:
                module = module_repository.get_module_by_ref_id(modul_id, tenant_id, course_id)
                if not module:
                    return {
                        "status": "success",
                        "data": [],
                        "level": "module_details"
                    }
                
                module_id = module[0]
                module_name = module[1]
                ref_module_id = module[2] if len(module) > 2 else None
                course_id_from_db = module[3] if len(module) > 3 else None
                course_name = module[4] if len(module) > 4 else None
                
                # Get annotation data for this module
                annotations_data = annotation_repository.get_annotations(module_id, tenant_id)
                total_pages = len(annotations_data) if annotations_data else 0
                
                # Format annotations
                annotations = []
                if annotations_data:
                    annotations = [
                        {
                            "page": f"Page {row[0]}",
                            "text": row[1]
                        }
                        for row in annotations_data
                    ]
                
                module_info = {
                    "modul_id": ref_module_id,
                    "modul_name": module_name,
                    "course_id": course_id_from_db,
                    "course_name": course_name,
                    "total_pages": total_pages,
                    "annotations": annotations
                }
                
                return {
                    "status": "success",
                    "data": [module_info],
                    "level": "module_details"
                }
        
        except Exception as e:
            traceback.print_exc()
            raise Exception(f'Failed to get annotations list: {str(e)}')


# Singleton instance
annotation_service = AnnotationService()
