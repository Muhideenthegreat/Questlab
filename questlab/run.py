import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

try:
    # Provide a default database URI via environment variable if none was set.
    # Without this, some environments may struggle to open the SQLite database
    # file specified in the configuration.  By setting DATABASE_URL here we
    # ensure consistent behaviour across systems.
    if not os.environ.get('DATABASE_URL'):
        os.environ['DATABASE_URL'] = 'sqlite:///questlab.db'

    from app import create_app
    app = create_app()

    if __name__ == '__main__':
        debug_mode = os.environ.get('FLASK_ENV') != 'production'
        app.run(debug=debug_mode, host='0.0.0.0', port=5000)

except ImportError as e:
    print(f"Import Error: {e}")
    print("Current Python path:", sys.path)
    print("Current directory:", os.getcwd())
    print("Files in current directory:", os.listdir('.'))
    if os.path.exists('app'):
        print("Files in app directory:", os.listdir('app'))