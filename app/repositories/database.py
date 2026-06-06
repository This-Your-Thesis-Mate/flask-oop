import psycopg2
from psycopg2 import pool
from app.config import Config


class DatabaseManager:
    """Singleton database connection pool manager"""
    
    _instance = None
    _pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._initialize_pool()
        return cls._instance
    
    @classmethod
    def _initialize_pool(cls):
        """Initialize connection pool from environment variables"""
        if cls._pool is None:
            try:
                # Use connection parameters from Config (loaded from environment variables)
                cls._pool = psycopg2.pool.SimpleConnectionPool(
                    1, 20,
                    host=Config.DB_HOST,
                    port=Config.DB_PORT,
                    user=Config.DB_USER,
                    database=Config.DB_NAME,
                    password=Config.DB_PASSWORD
                )
                print(f"✓ Connection pool created: {Config.DB_USER}@{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}")
            except Exception as e:
                print(f"✗ Failed to create connection pool: {str(e)}")
                raise
    
    def get_connection(self):
        """Get connection from pool"""
        return self._pool.getconn()
    
    def return_connection(self, conn):
        """Return connection to pool"""
        self._pool.putconn(conn)
    
    def execute_query(self, query, params=None, fetch=True):
        """Execute a query and return results"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            if fetch:
                result = cursor.fetchall()
            else:
                result = None
            conn.commit()
            return result
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            self.return_connection(conn)

db_manager = DatabaseManager()
