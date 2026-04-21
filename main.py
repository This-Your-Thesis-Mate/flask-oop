"""
Main entry point for Flask application
"""
from app.application import Application
from app.config import Config


class Main:
    """Main application entry point"""
    
    @staticmethod
    def run():
        """Run the application"""
        app_instance = Application()
        flask_app = app_instance.create_app()
        
        flask_app.run(
            debug=Config.DEBUG,
            port=Config.PORT,
            host=Config.HOST
        )


if __name__ == "__main__":
    main = Main()
    main.run()
