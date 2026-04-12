from flask import Flask
from app.config import Config
from app.routes.views import bp as main_bp
from app.models.database import init_db

def create_app():
    """Application factory function"""
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    # Initialize application database tables
    init_db()

    # Register blueprints
    app.register_blueprint(main_bp)
    
    return app 
