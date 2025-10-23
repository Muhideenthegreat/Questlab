import pytest
import tempfile
import os

# Disable automatic loading of third-party pytest plugins.  In
# particular the `pytest-flask` plugin bundled with this project is
# incompatible with Flask >=3.1 because it tries to import
# ``_request_ctx_stack`` which has been removed.  Setting this
# environment variable prevents pytest from loading such plugins.
os.environ.setdefault('PYTEST_DISABLE_PLUGIN_AUTOLOAD', '1')

from app import create_app, db

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
    
    yield app
    
    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """CLI runner for testing app commands."""
    return app.test_cli_runner()