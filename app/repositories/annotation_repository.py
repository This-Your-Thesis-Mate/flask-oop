"""
Annotation repository for database operations
"""
from app.repositories.database import db_manager


class AnnotationRepository:
    """Repository for annotation-related database operations"""
    
    @staticmethod
    def create_annotations(module_id, annotations):
        """
        Create annotations for a module
        
        Args:
            module_id: Module ID
            annotations: List of Annotation objects
        """
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            for annotation in annotations:
                cursor.execute(
                    """
                    INSERT INTO module_annotations (module_id, page_number, text)
                    VALUES (%s, %s, %s)
                    """,
                    (module_id, annotation.page_number, annotation.text)
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            db_manager.return_connection(conn)
    
    @staticmethod
    def get_annotations(module_id):
        """Get all annotations for a module"""
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT page_number, text 
                FROM module_annotations 
                WHERE module_id = %s
                ORDER BY page_number
                """,
                (module_id,)
            )
            result = cursor.fetchall()
            return result
        finally:
            cursor.close()
            db_manager.return_connection(conn)
    
    @staticmethod
    def delete_annotations(module_id):
        """Delete all annotations for a module"""
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM module_annotations WHERE module_id = %s", (module_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            db_manager.return_connection(conn)


# Singleton instance
annotation_repository = AnnotationRepository()
