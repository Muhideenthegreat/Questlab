import os
import sys

print("🔍 Debugging QuestLab Setup...")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

# Check if app directory exists
app_exists = os.path.exists('app')
print(f"App directory exists: {app_exists}")

if app_exists:
    print("Files in app directory:")
    for file in os.listdir('app'):
        print(f"  - {file}")
    
    # Check if __init__.py exists
    init_exists = os.path.exists('app/__init__.py')
    print(f"app/__init__.py exists: {init_exists}")
    
    if init_exists:
        print("Contents of app/__init__.py:")
        with open('app/__init__.py', 'r') as f:
            content = f.read()
            print(content[:500] + "..." if len(content) > 500 else content)

# Try to import
print("\nAttempting to import...")
try:
    from app import create_app
    print("✅ SUCCESS: Imported create_app from app")
except ImportError as e:
    print(f"❌ FAILED: {e}")
    
    # Try alternative import
    try:
        import app
        print("✅ Can import app module")
        print("Available attributes in app:", dir(app))
    except ImportError as e2:
        print(f"❌ Cannot import app at all: {e2}")