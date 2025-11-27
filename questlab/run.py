import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

try:
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
