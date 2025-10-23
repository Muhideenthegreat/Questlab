from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
csrf = CSRFProtect()
login_manager = LoginManager()

def create_app(config_name=None):
    """Application factory pattern"""
    
    # Create app with instance folder
    app = Flask(__name__, instance_relative_config=True)
    
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass
    
    # Load configuration
    # Determine which configuration class to use.  The FLASK_CONFIG
    # environment variable can be set to "development", "testing" or
    # "production".  Default to development if nothing is provided.
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')

    from config import config
    app.config.from_object(config[config_name])

    # Database configuration is now handled entirely in the Config classes.
    # Do not override the SQLALCHEMY_DATABASE_URI here.  If you need to
    # point at a different database, set the DATABASE_URL environment
    # variable or adjust the value in config.py instead.
    
    # Create upload directory
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Provide user loader to Flask‑Login
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        """Return the user corresponding to the given user_id."""
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None
    
    # Register blueprints
    from app.routes.quest_routes import quest_bp
    from app.routes.submission_routes import submission_bp
    from app.routes.auth_routes import auth_bp
    
    app.register_blueprint(quest_bp)
    app.register_blueprint(submission_bp)
    app.register_blueprint(auth_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
