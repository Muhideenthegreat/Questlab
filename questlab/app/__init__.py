from flask import Flask, g, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
import uuid

# Load environment variables from project root .env
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
load_dotenv(os.path.join(BASE_DIR, '.env'))

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
    
    # Create upload and logging directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    log_folder = app.config.get('LOG_FOLDER')
    if log_folder:
        os.makedirs(log_folder, exist_ok=True)
    _configure_logging(app)

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

    @app.before_request
    def inject_request_id():
        g.request_id = str(uuid.uuid4())


    @app.after_request
    def set_security_headers(response):
        """Apply baseline security headers."""
        csp = app.config.get('CONTENT_SECURITY_POLICY')
        if csp:
            response.headers.setdefault('Content-Security-Policy', csp)
        response.headers.setdefault('X-Frame-Options', app.config.get('X_FRAME_OPTIONS', 'DENY'))
        response.headers.setdefault('X-Content-Type-Options', app.config.get('X_CONTENT_TYPE_OPTIONS', 'nosniff'))
        response.headers.setdefault('Referrer-Policy', app.config.get('REFERRER_POLICY', 'no-referrer'))
        # Only set HSTS when running over HTTPS to avoid local dev issues.
        if request.scheme == 'https':
            hsts = app.config.get('STRICT_TRANSPORT_SECURITY')
            if hsts:
                response.headers.setdefault('Strict-Transport-Security', hsts)
        return response
    
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


def _configure_logging(app: Flask) -> None:
    """Configure rotating file logging for security/audit events."""
    from app.utils.logging import JSONLogFormatter, RequestContextFilter

    log_path = app.config.get('SECURITY_LOG_FILE')
    if not log_path:
        return

    log_level_name = str(app.config.get('LOG_LEVEL', 'INFO')).upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    try:
        handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=5)
    except OSError:
        # If the log file can't be opened, skip configuration to avoid crashing startup.
        return

    handler.setFormatter(JSONLogFormatter())
    handler.setLevel(log_level)
    handler.addFilter(RequestContextFilter())
    if not any(isinstance(h, RotatingFileHandler) and getattr(h, 'baseFilename', None) == getattr(handler, 'baseFilename', None)
               for h in app.logger.handlers):
        app.logger.addHandler(handler)
    app.logger.setLevel(log_level)
