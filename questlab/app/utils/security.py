import os
from flask import current_app
from werkzeug.utils import secure_filename
# Attempt to import python-magic for MIME type detection.  This
# dependency is optional; if it's not available we fall back to
# signature-based checks implemented below.  See
# https://github.com/ahupp/python-magic for details.
try:
    import magic  # type: ignore
except ImportError:
    magic = None  # gracefully degrade when python-magic is absent

def allowed_file(filename):
    """Check if file extension is allowed"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config['ALLOWED_EXTENSIONS']

def secure_filename_with_id(filename, file_id):
    """Create secure filename with UUID"""
    filename = secure_filename(filename)
    name, ext = os.path.splitext(filename)
    return f"{file_id}{ext}"

def sanitize_input(text):
    """Basic input sanitization"""
    if not text:
        return text
    import re
    # Remove potentially dangerous characters but preserve most content
    text = re.sub(r'[<>]', '', text)
    return text.strip()

# Alternative validation without imghdr
def validate_file_type(file_stream, filename):
    """Validate file type using MIME type and extension"""
    try:
        # First check extension
        if not allowed_file(filename):
            return False
        
        # For now, we'll trust the extension and do basic MIME type checking
        # In production, you might want to use python-magic for more robust checking
        file_stream.seek(0)
        header = file_stream.read(1024)  # Read first 1KB for basic signature checking
        file_stream.seek(0)
        
        # If python-magic is available use it to inspect the MIME type.
        if magic is not None:
            try:
                # Read a couple of kilobytes from the start of the file
                buf = file_stream.read(2048)
                file_stream.seek(0)
                mime = magic.from_buffer(buf, mime=True)
                # Accept common image and video MIME types
                if mime and (mime.startswith('image/') or mime.startswith('video/')):
                    return True
            except Exception:
                # If magic fails, fall back to signature checks below
                pass

        # Basic image signature checking
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            # Check for common image file signatures
            if header.startswith(b'\x89PNG\r\n\x1a\n'):  # PNG
                return True
            elif header.startswith(b'\xff\xd8\xff'):  # JPEG
                return True
            elif header.startswith(b'GIF8'):  # GIF
                return True
            else:
                return False

        # For video files, we'll do less validation for now
        elif filename.lower().endswith(('.mp4', '.mov')):
            return True

        return False

    except Exception:
        return False