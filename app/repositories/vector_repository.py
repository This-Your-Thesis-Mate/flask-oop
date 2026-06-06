from app.repositories.database import db_manager


class VectorRepository:
    """Repository for vector similarity search operations"""
    
    @staticmethod
    def similarity_search(query_embedding, course_id, siteidentifier, threshold=0.4, limit=5, module_id=None):
        """
        Perform similarity search with site isolation
        
        Args:
            query_embedding: Query embedding vector
            course_id: Course ID to search within
            siteidentifier: Site Identifier for data isolation (REQUIRED)
            threshold: Similarity threshold (default 0.4)
            limit: Maximum number of results (default 5)
            module_id: Optional module_id to filter by specific module
        
        Returns:
            List of tuples (chunk_text, similarity)
        """
        if not siteidentifier:
            raise ValueError("siteidentifier is required for security and data isolation")
        
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        try:
            if module_id:
                # Search within specific module by ref_module_id with site isolation on all tables
                cursor.execute(
                    """
                    SELECT c.chunk_text, (1 - (v.embedding <=> %s::vector)) as similarity 
                    FROM chunks c
                    JOIN tbl_vector v ON c.id = v.chunk_id  
                    JOIN modules m ON c.module_id = m.id
                    WHERE m.course_id = %s AND m.ref_module_id = %s 
                    AND m.siteidentifier = %s AND c.siteidentifier = %s AND v.siteidentifier = %s
                    AND (1 - (v.embedding <=> %s::vector)) > %s
                    ORDER BY similarity DESC
                    LIMIT %s
                    """,
                    (query_embedding, int(course_id), int(module_id), str(siteidentifier), str(siteidentifier), str(siteidentifier), query_embedding, float(threshold), int(limit))
                )
            else:
                # Search across all modules in course with site isolation on all tables
                cursor.execute(
                    """
                    SELECT c.chunk_text, (1 - (v.embedding <=> %s::vector)) as similarity 
                    FROM chunks c
                    JOIN tbl_vector v ON c.id = v.chunk_id  
                    JOIN modules m ON c.module_id = m.id
                    WHERE m.course_id = %s AND m.siteidentifier = %s AND c.siteidentifier = %s AND v.siteidentifier = %s
                    AND (1 - (v.embedding <=> %s::vector)) > %s
                    ORDER BY similarity DESC
                    LIMIT %s
                    """,
                    (query_embedding, int(course_id), str(siteidentifier), str(siteidentifier), str(siteidentifier), query_embedding, float(threshold), int(limit))
                )
            
            result = cursor.fetchall()
            return result
        finally:
            cursor.close()
            db_manager.return_connection(conn)

vector_repository = VectorRepository()
