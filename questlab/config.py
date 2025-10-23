import os
from datetime import timedelta

class Config:
    """Base configuration with security defaults"""
    
    # Security: Generate secret keys for production
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    
    # Database configuration
    #
    # When no external DATABASE_URL is provided, default to a SQLite file
    # inside the project's ``instance`` directory.  We intentionally use
    # a *relative* SQLite URI rather than an absolute path.  Relative
    # URIs avoid path resolution issues across different environments,
    # containers or operating systems.  The ``instance`` folder will be
    # created below if it does not already exist.
    basedir = os.path.abspath(os.path.dirname(__file__))

    # Ensure instance directory exists
    instance_dir = os.path.join(basedir, 'instance')
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir, exist_ok=True)

    # Select the database URI.  Prefer the DATABASE_URL environment
    # variable if present (this may point at a Postgres or other server).
    # Otherwise, store an SQLite file under the ``instance`` folder using
    # a relative URI.  A relative URI such as ``sqlite:///instance/questlab.db``
    # tells SQLAlchemy to create the database in a subdirectory of the
    # current working directory, which avoids problems with absolute
    # filenames when the project is run in different locations.
    if os.environ.get('DATABASE_URL'):
        SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    else:
        # Use a SQLite database file in the current working directory by default.
        # A simple relative URI like ``sqlite:///questlab.db`` avoids issues with
        # absolute paths when the application is run inside containers or
        # different host environments.  SQLAlchemy will create this file
        # automatically when the app first writes to the database.
        SQLALCHEMY_DATABASE_URI = 'sqlite:///questlab.db'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security: File upload restrictions
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov'}
    
    # Security: Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    
    # File upload security - FIXED PATH
    UPLOAD_FOLDER = os.path.join(instance_dir, 'uploads')


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
