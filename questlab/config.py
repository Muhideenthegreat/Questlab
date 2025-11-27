import os
from datetime import timedelta

class Config:
    """Base configuration with security defaults"""
    
    # Security: Generate secret keys for production
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # Only enable ``SESSION_COOKIE_SECURE`` when explicitly requested so local
    # HTTP development remains convenient.
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    
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
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        # If a relative SQLite URL was provided (e.g. sqlite:///questlab.db),
        # resolve it against the project base directory to avoid double
        # "instance/instance" issues. Absolute URLs are left untouched.
        if db_url.startswith('sqlite:///') and not db_url.startswith('sqlite:////'):
            rel_path = db_url.replace('sqlite:///', '', 1)
            abs_path = os.path.abspath(os.path.join(basedir, rel_path))
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{abs_path}"
        else:
            SQLALCHEMY_DATABASE_URI = db_url
    else:
        # Default: absolute path inside the instance directory for portability.
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(instance_dir, 'questlab.db')}"
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security: File upload restrictions
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov'}
    
    # Security: Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    
    # File upload security - FIXED PATH
    UPLOAD_FOLDER = os.path.join(instance_dir, 'uploads')
    LOG_FOLDER = os.path.join(instance_dir, 'logs')
    SECURITY_LOG_FILE = os.environ.get('SECURITY_LOG_FILE') or os.path.join(LOG_FOLDER, 'questlab.log')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    # Security headers
    CONTENT_SECURITY_POLICY = os.environ.get(
        'CONTENT_SECURITY_POLICY',
        "default-src 'self'; "
        "style-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "script-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "img-src 'self' data:; "
        "font-src 'self' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net"
    )
    REFERRER_POLICY = 'no-referrer'
    X_FRAME_OPTIONS = 'DENY'
    X_CONTENT_TYPE_OPTIONS = 'nosniff'
    STRICT_TRANSPORT_SECURITY = os.environ.get('STRICT_TRANSPORT_SECURITY', 'max-age=31536000; includeSubDomains')

    # Rate limiting defaults
    LOGIN_RATE_LIMIT = (5, 900)  # 5 attempts per 15 minutes
    REGISTER_RATE_LIMIT = (10, 900)
    UPLOAD_RATE_LIMIT = (30, 900)


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
    SESSION_COOKIE_SECURE = True
    # Require a non-default secret key in production
    def __init__(self):
        super().__init__()
        if self.SECRET_KEY == 'dev-key-change-in-production':
            raise RuntimeError("SECRET_KEY must be set to a strong value in production.")


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
