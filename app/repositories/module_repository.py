"""
Module repository for database operations
"""
from datetime import datetime
from app.repositories.database import db_manager


class ModuleRepository:
    """Repository for module-related database operations"""
    
    @staticmethod
    def create_module(module_name, course_id, ref_module_id=None):
        """Create a new module"""
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO modules (module_name, course_id, ref_module_id)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (module_name, course_id, ref_module_id)
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
    def get_module(course_id, ref_module_id):
        """Get module by course_id and ref_module_id (user's module ID)"""
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, module_name 
                FROM modules 
                WHERE course_id = %s AND ref_module_id = %s
                ORDER BY id DESC
                LIMIT 1
                """,
                (course_id, ref_module_id)
            )
            result = cursor.fetchone()
            return result
        finally:
            cursor.close()
            db_manager.return_connection(conn)
    
    @staticmethod
    def delete_module(ref_module_id, course_id):
        """Delete module and related data by ref_module_id"""
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            # Get internal module id
            cursor.execute(
                "SELECT id FROM modules WHERE ref_module_id = %s AND course_id = %s",
                (ref_module_id, course_id)
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
    def get_modules_by_course(course_id):
        """Get all modules by course_id"""
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, module_name, ref_module_id, course_id 
                FROM modules 
                WHERE course_id = %s
                ORDER BY id DESC
                """,
                (course_id,)
            )
            results = cursor.fetchall()
            return results
        finally:
            cursor.close()
            db_manager.return_connection(conn)
    
    @staticmethod
    def get_all_modules():
        """Get all modules from all courses"""
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, module_name, ref_module_id, course_id 
                FROM modules 
                ORDER BY course_id, id DESC
                """
            )
            results = cursor.fetchall()
            return results
        finally:
            cursor.close()
            db_manager.return_connection(conn)


# Singleton instance
module_repository = ModuleRepository()
