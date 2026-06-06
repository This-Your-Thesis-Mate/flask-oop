from psycopg2.extras import execute_values
from app.repositories.database import db_manager


class ChunkRepository:
    """Repository for chunk-related database operations"""
    
    @staticmethod
    def create_chunk(module_id, chunk_text, siteidentifier):
        """Create a new chunk"""
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO chunks (module_id, chunk_text, siteidentifier) VALUES (%s, %s, %s) RETURNING id",
                (module_id, chunk_text, siteidentifier)
            )
            chunk_id = cursor.fetchone()[0]
            conn.commit()
            return chunk_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            db_manager.return_connection(conn)
    
    @staticmethod
    def get_chunks_by_module(module_id, siteidentifier):
        """Get all chunks for a module and site"""
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT chunk_text 
                FROM chunks 
                WHERE module_id = %s AND siteidentifier = %s
                ORDER BY id
                """,
                (module_id, siteidentifier)
            )
            result = cursor.fetchall()
            return result
        finally:
            cursor.close()
            db_manager.return_connection(conn)
    
    @staticmethod
    def get_chunks_by_ref_module_id(ref_module_id, siteidentifier):
        """Get all chunks for a module by ref_module_id and siteidentifier"""
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT c.chunk_text 
                FROM chunks c
                JOIN modules m ON c.module_id = m.id
                WHERE m.ref_module_id = %s AND c.siteidentifier = %s
                ORDER BY c.id
                """,
                (ref_module_id, siteidentifier)
            )
            result = cursor.fetchall()
            return result
        finally:
            cursor.close()
            db_manager.return_connection(conn)
    
    @staticmethod
    def save_chunks_and_embeddings(module_id, chunks_data, siteidentifier):
        """
        Save multiple chunks and their embeddings
        chunks_data: list of tuples (chunk_text, embedding_vector)
        siteidentifier: Site Identifier
        """
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            embedding_data = []
            
            for chunk_text, embedding_vec in chunks_data:
                # Save chunk
                cursor.execute(
                    "INSERT INTO chunks (module_id, chunk_text, siteidentifier) VALUES (%s, %s, %s) RETURNING id",
                    (module_id, chunk_text, siteidentifier)
                )
                chunk_id = cursor.fetchone()[0]
                
                embedding_data.append((embedding_vec, chunk_id, siteidentifier))
            # Save embeddings in bulk
            execute_values(
                cursor,
                "INSERT INTO tbl_vector (embedding, chunk_id, siteidentifier) VALUES %s",
                embedding_data
            )
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            db_manager.return_connection(conn)

chunk_repository = ChunkRepository()
