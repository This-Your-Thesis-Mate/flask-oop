from app.repositories import module_repository


class ModuleService:
    """Service for module management"""
    
    @staticmethod
    def delete_module(module_id, course_id, siteidentifier):
        """
        Delete a module and all related data
        
        Args:
            module_id: Module ID
            course_id: Course ID
            siteidentifier: Site Identifier
        
        Returns:
            bool: True if deleted successfully
        """
        result = module_repository.delete_module(module_id, course_id, siteidentifier)
        if not result:
            raise Exception('Module not found.')
        return True

module_service = ModuleService()
