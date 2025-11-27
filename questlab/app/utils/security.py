import os
from flask import current_app
from werkzeug.utils import secure_filename
import re
from typing import Iterable, List, Tuple
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

def sanitize_input(text, max_length: int = 5000):
    """Basic input sanitization with length limiting.

    Removes angle brackets to minimise HTML/script injection risks and trims
    surrounding whitespace.  ``None`` is normalised to an empty string to keep
    downstream code simple.
    """
    if text is None:
        return ''
    # Remove potentially dangerous characters but preserve most content
    text = re.sub(r'[<>]', '', str(text))
    cleaned = text.strip()
    if max_length and max_length > 0:
        return cleaned[:max_length]
    return cleaned


def validate_username(username: str, max_length: int = 80) -> Tuple[bool, str]:
    """Validate username against length and character policy."""
    if not username:
        return False, 'Username is required.'
    if len(username) < 3 or len(username) > max_length:
        return False, f'Username must be between 3 and {max_length} characters.'
    if not re.match(r'^[A-Za-z0-9_.-]+$', username):
        return False, 'Username may only contain letters, numbers, dots, dashes, and underscores.'
    return True, ''


def validate_password_strength(password: str, min_length: int = 8) -> Tuple[bool, str]:
    """Enforce a simple password policy."""
    if not password:
        return False, 'Password is required.'
    if len(password) < min_length:
        return False, f'Password must be at least {min_length} characters.'
    if not re.search(r'[A-Z]', password):
        return False, 'Password must include an uppercase letter.'
    if not re.search(r'[a-z]', password):
        return False, 'Password must include a lowercase letter.'
    if not re.search(r'[0-9]', password):
        return False, 'Password must include a number.'
    if not re.search(r'[!@#$%^&*(),.?\":{}|<>\\-_=+;]', password):
        return False, 'Password must include a special character.'
    return True, ''


def normalize_tags(raw_tags: Iterable, max_tags: int = 10, max_length: int = 30) -> List[str]:
    """Convert incoming tags to a deduplicated, sanitised list."""
    cleaned: List[str] = []
    if not raw_tags:
        return cleaned

    if isinstance(raw_tags, str):
        items = raw_tags.split(',')
    else:
        items = list(raw_tags)

    for tag in items:
        candidate = sanitize_input(tag)
        if not candidate:
            continue
        # Collapse internal whitespace and enforce a short max length
        candidate = re.sub(r'\\s+', ' ', candidate)[:max_length]
        if candidate not in cleaned:
            cleaned.append(candidate)
        if len(cleaned) >= max_tags:
            break
    return cleaned


def validate_email(email: str, max_length: int = 120) -> Tuple[bool, str]:
    """Basic email validation."""
    if not email:
        return False, 'Email is required.'
    if len(email) > max_length:
        return False, 'Email is too long.'
    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    if not re.match(pattern, email):
        return False, 'Invalid email format.'
    return True, ''

# Alternative validation without imghdr
def validate_file_type(file_stream, filename):
    """Validate file type using MIME type and extension with stricter checks."""
    try:
        if not allowed_file(filename):
            return False

        file_stream.seek(0)
        header = file_stream.read(2048)
        file_stream.seek(0)

        # If python-magic is available, prefer it for MIME detection, but fall back to signatures.
        if magic is not None:
            try:
                mime = magic.from_buffer(header, mime=True)
                if mime and (
                    mime.startswith('image/png')
                    or mime.startswith('image/jpeg')
                    or mime.startswith('image/gif')
                    or mime.startswith('video/mp4')
                    or mime.startswith('video/quicktime')
                ):
                    return True
            except Exception:
                pass

        # Basic signature checks
        name = filename.lower()
        if name.endswith('.png'):
            return header.startswith(b'\x89PNG\r\n\x1a\n')
        if name.endswith(('.jpg', '.jpeg')):
            return header.startswith(b'\xff\xd8\xff')
        if name.endswith('.gif'):
            return header.startswith(b'GIF8')
        if name.endswith('.mp4'):
            # MP4 signatures can vary; accept if 'ftyp' is present in first bytes
            return b'ftyp' in header[:256]
        if name.endswith('.mov'):
            return b'ftypqt' in header[:256] or b'qt  ' in header[:256]
        return False
    except Exception:
        return False
