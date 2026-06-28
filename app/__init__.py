from app.application import Application

def create_app():
    """Create and configure Flask application"""
    app_instance = Application()
    return app_instance.create_app()


__all__ = ['create_app', 'Application']
