from app.repositories.database import db_manager


class AnnotationRepository:
    """Repository for annotation-related database operations"""
    
    @staticmethod
    def create_annotations(module_id, annotations, siteidentifier):
        """
        Create annotations for a module
        
        Args:
            module_id: Module ID
            annotations: List of Annotation objects
            siteidentifier: Site Identifier
        """
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            for annotation in annotations:
                cursor.execute(
                    """
                    INSERT INTO module_annotations (module_id, page_number, text, siteidentifier)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (module_id, annotation.page_number, annotation.text, siteidentifier)
                )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            db_manager.return_connection(conn)
    
    @staticmethod
    def get_annotations(module_id, siteidentifier):
        """Get all annotations for a module and site"""
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT page_number, text 
                FROM module_annotations 
                WHERE module_id = %s AND siteidentifier = %s
                ORDER BY page_number
                """,
                (module_id, siteidentifier)
            )
            result = cursor.fetchall()
            return result
        finally:
            cursor.close()
            db_manager.return_connection(conn)
    
    @staticmethod
    def delete_annotations(module_id, siteidentifier):
        """Delete all annotations for a module and site"""
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM module_annotations WHERE module_id = %s AND siteidentifier = %s", (module_id, siteidentifier))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            db_manager.return_connection(conn)

annotation_repository = AnnotationRepository()
