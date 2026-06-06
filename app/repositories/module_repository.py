from datetime import datetime
from app.repositories.database import db_manager


class ModuleRepository:
    """Repository for module-related database operations"""
    
    @staticmethod
    def create_module(module_name, course_id, course_name, siteidentifier, ref_module_id=None):
        """Create a new module"""
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO modules (module_name, course_id, course_name, ref_module_id, siteidentifier)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (module_name, course_id, course_name, ref_module_id, siteidentifier)
            )
            module_id = cursor.fetchone()[0]
            conn.commit()
            return module_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            db_manager.return_connection(conn)
    
    @staticmethod
    def get_module(course_id, ref_module_id, siteidentifier):
        """Get module by course_id and ref_module_id (user's module ID) and siteidentifier"""
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, module_name, course_name 
                FROM modules 
                WHERE course_id = %s AND ref_module_id = %s AND siteidentifier = %s
                ORDER BY id DESC
                LIMIT 1
                """,
                (course_id, ref_module_id, siteidentifier)
            )
            result = cursor.fetchone()
            return result
        finally:
            cursor.close()
            db_manager.return_connection(conn)
    
    @staticmethod
    def delete_module(ref_module_id, course_id, siteidentifier):
        """Delete module and related data by ref_module_id and siteidentifier"""
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            # Get internal module id
            cursor.execute(
                "SELECT id FROM modules WHERE ref_module_id = %s AND course_id = %s AND siteidentifier = %s",
                (ref_module_id, course_id, siteidentifier)
            )
            module = cursor.fetchone()
            if not module:
                return False
            
            internal_module_id = module[0]
            
            # Delete related data
            cursor.execute("DELETE FROM chunks WHERE module_id = %s", (internal_module_id,))
            cursor.execute(
                "DELETE FROM tbl_vector WHERE chunk_id IN (SELECT id FROM chunks WHERE module_id = %s)",
                (internal_module_id,)
            )
            cursor.execute("DELETE FROM modules WHERE id = %s", (internal_module_id,))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            db_manager.return_connection(conn)
    
    @staticmethod
    def get_modules_by_course(course_id, siteidentifier):
        """Get all modules by course_id and siteidentifier"""
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, module_name, ref_module_id, course_id, course_name, siteidentifier 
                FROM modules 
                WHERE course_id = %s AND siteidentifier = %s
                ORDER BY id DESC
                """,
                (course_id, siteidentifier)
            )
            results = cursor.fetchall()
            return results
        finally:
            cursor.close()
            db_manager.return_connection(conn)
    
    @staticmethod
    def get_all_modules(siteidentifier):
        """Get all modules from all courses for a site"""
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, module_name, ref_module_id, course_id, course_name, siteidentifier 
                FROM modules 
                WHERE siteidentifier = %s
                ORDER BY course_id, id DESC
                """,
                (siteidentifier,)
            )
            results = cursor.fetchall()
            return results
        finally:
            cursor.close()
            db_manager.return_connection(conn)
    
    @staticmethod
    def get_module_by_ref_id(ref_module_id, siteidentifier, course_id=None):
        """
        Get module by ref_module_id and siteidentifier
        Optionally filter by course_id for more precise lookup
        """
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            if course_id:
                # If course_id is provided, use it for more precise lookup
                cursor.execute(
                    """
                    SELECT id, module_name, ref_module_id, course_id, course_name, siteidentifier 
                    FROM modules 
                    WHERE ref_module_id = %s AND course_id = %s AND siteidentifier = %s
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (ref_module_id, course_id, siteidentifier)
                )
            else:
                # Fall back to just ref_module_id and siteidentifier
                cursor.execute(
                    """
                    SELECT id, module_name, ref_module_id, course_id, course_name, siteidentifier 
                    FROM modules 
                    WHERE ref_module_id = %s AND siteidentifier = %s
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (ref_module_id, siteidentifier)
                )
            result = cursor.fetchone()
            return result
        finally:
            cursor.close()
            db_manager.return_connection(conn)
    
    @staticmethod
    def get_courses_by_site(siteidentifier):
        """Get all unique courses for a site"""
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT DISTINCT course_id, course_name, siteidentifier
                FROM modules 
                WHERE siteidentifier = %s
                ORDER BY course_id DESC
                """,
                (siteidentifier,)
            )
            results = cursor.fetchall()
            return results
        finally:
            cursor.close()
            db_manager.return_connection(conn)

module_repository = ModuleRepository()
