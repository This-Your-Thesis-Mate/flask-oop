import os
from dotenv import load_dotenv

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
if ENVIRONMENT == "development":
    load_dotenv()

class Config:
    """Configuration class for Flask application"""
    
    # Flask Config
    DEBUG = os.getenv("DEBUG", "True") == "True"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "5000"))
    
    # MinerU Config
    MINERU_TOKEN = os.getenv("MINERU_TOKEN")
    MINERU_API_BASE = os.getenv("MINERU_API_BASE", "https://mineru.net/api/v4")
    MINERU_LANGUAGE = os.getenv("MINERU_LANGUAGE", "id")
    MINERU_ENABLE_TABLE = os.getenv("MINERU_ENABLE_TABLE", "True") == "True"
    MINERU_ENABLE_FORMULA = os.getenv("MINERU_ENABLE_FORMULA", "True") == "True"
    MINERU_IS_OCR = os.getenv("MINERU_IS_OCR", "True") == "True"
    
    # Azure OpenAI Config
    AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    
    # Sumopod Config (legacy, kept for reference)
    # SUMOPOD_API_KEY = os.getenv("SUMOPOD_API_KEY")
    # SUMOPOD_BASE_URL = os.getenv("SUMOPOD_BASE_URL", "https://ai.sumopod.com/v1")
    # SUMOPOD_MODEL = os.getenv("SUMOPOD_MODEL", "gpt-4o-mini")
    
    # Azure Embedding Config
    AZURE_EMBEDDING_URL = os.getenv("AZURE_EMBEDDING_URL")
    AZURE_EMBEDDING_API_KEY = os.getenv("AZURE_EMBEDDING_API_KEY")
    
    # Database Config
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "vectors")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "123123")
    DB_SSLMODE = os.getenv("DB_SSLMODE", "require")
    
    # Text Splitting Config
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1500"))
    TOKENIZER_MODEL = os.getenv("TOKENIZER_MODEL", "bert-base-uncased")
    
    # Annotation Config
    MAX_CHARS_PER_PAGE = int(os.getenv("MAX_CHARS_PER_PAGE", "500"))
    
    # Output Directory Config
    EXTRACTED_TEXTS_DIR = os.getenv("EXTRACTED_TEXTS_DIR", "extracted_texts")
    
    # RAG Config
    RAG_ENABLE_LLM_GENERATION = os.getenv("RAG_ENABLE_LLM_GENERATION", "True") == "True"
    
    # Temperature calibration value (model-specific parameter)
    temperature = int(os.getenv("temperature", "0"))
    
    @staticmethod
    def get_db_connection_string():
        """Get database connection string"""
        return "host={0} port={1} user={2} dbname={3} password={4}".format(
            Config.DB_HOST,
            Config.DB_PORT,
            Config.DB_USER,
            Config.DB_NAME,
            Config.DB_PASSWORD
        )
