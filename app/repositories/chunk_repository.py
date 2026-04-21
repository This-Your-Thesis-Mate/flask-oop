"""
Chunk repository for database operations
"""
from psycopg2.extras import execute_values
from app.repositories.database import db_manager


class ChunkRepository:
    """Repository for chunk-related database operations"""
    
    @staticmethod
    def create_chunk(module_id, chunk_text):
        """Create a new chunk"""
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO chunks (module_id, chunk_text) VALUES (%s, %s) RETURNING id",
                (module_id, chunk_text)
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
    def get_chunks_by_module(module_id):
        """Get all chunks for a module"""
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT chunk_text 
                FROM chunks 
                WHERE module_id = %s
                ORDER BY id
                """,
                (module_id,)
            )
            result = cursor.fetchall()
            return result
        finally:
            cursor.close()
            db_manager.return_connection(conn)
    
    @staticmethod
    def save_chunks_and_embeddings(module_id, chunks_data):
        """
        Save multiple chunks and their embeddings
        chunks_data: list of tuples (chunk_text, embedding_vector)
        """
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            embedding_data = []
            
            for chunk_text, embedding_vec in chunks_data:
                # Save chunk
                cursor.execute(
                    "INSERT INTO chunks (module_id, chunk_text) VALUES (%s, %s) RETURNING id",
                    (module_id, chunk_text)
                )
                chunk_id = cursor.fetchone()[0]
                
                # Prepare embedding data
                embedding_data.append((embedding_vec, chunk_id))
            
            # Bulk insert embeddings
            execute_values(
                cursor,
                "INSERT INTO tbl_vector (embedding, chunk_id) VALUES %s",
                embedding_data
            )
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            db_manager.return_connection(conn)


# Singleton instance
chunk_repository = ChunkRepository()
