"""
Module service for module management
"""
from app.repositories import module_repository


class ModuleService:
    """Service for module management"""
    
    @staticmethod
    def delete_module(module_id, course_id):
        """
        Delete a module and all related data
        
        Args:
            module_id: Module ID
            course_id: Course ID
        
        Returns:
            bool: True if deleted successfully
        """
        result = module_repository.delete_module(module_id, course_id)
        if not result:
            raise Exception('Module not found')
        return True


# Singleton instance
module_service = ModuleService()
