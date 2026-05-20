from app.routes.base_handler import BaseRouteHandler
from app.routes.upload import upload_bp
from app.routes.rag import rag_bp
from app.routes.quiz import quiz_bp
from app.routes.annotation import annotation_bp
from app.routes.module import module_bp
from app.routes.healthcheck import healthcheck_bp
from app.routes.tts import tts_bp

__all__ = [
    'BaseRouteHandler',
    'upload_bp',
    'rag_bp',
    'quiz_bp',
    'annotation_bp',
    'module_bp',
    'healthcheck_bp',
    'tts_bp'
]
