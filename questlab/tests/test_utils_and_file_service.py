"""
Tests for utility functions and the file handling service.

These tests exercise the pure utility helpers defined in
``app.utils.security`` as well as the higher level file saving
functionality provided by ``FileService``.  The tests intentionally
avoid any external dependencies beyond what is already required by
the application (e.g. Werkzeug for FileStorage) and use temporary
directories to ensure isolation.

To run these tests use::

    pytest -q questlab/tests/test_utils_and_file_service.py
"""

import io
import os
import json
import tempfile

import pytest

from werkzeug.datastructures import FileStorage

from app.utils.security import (
    allowed_file,
    secure_filename_with_id,
    sanitize_input,
    validate_file_type,
    validate_username,
    validate_password_strength,
    normalize_tags,
)
from app.utils.rate_limit import check_rate_limit, remaining
from app.services.file_service import FileService


class TestSecurityUtils:
    """Unit tests for simple utility helpers in ``app.utils.security``."""

    def test_allowed_file(self, app):
        """Only files with allowed extensions should return True."""
        with app.app_context():
            app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
            assert allowed_file('image.png') is True
            assert allowed_file('picture.JPG') is True  # case insensitive
            assert allowed_file('video.mp4') is False
            assert allowed_file('noextension') is False

    def test_secure_filename_with_id(self):
        """The generated filename should consist of the id and original extension."""
        filename = secure_filename_with_id('  my dangerous file.Mp4  ', 'abcd1234')
        # ``secure_filename`` preserves the original case of the file extension; ``secure_filename_with_id``
        # simply prefixes the given id and does not coerce the extension to lowercase.
        assert filename == 'abcd1234.Mp4'

    def test_sanitize_input(self):
        """Sanitise input should strip angle brackets and whitespace."""
        assert sanitize_input(' <script>alert(1)</script> ') == 'scriptalert(1)/script'
        assert sanitize_input('Hello World') == 'Hello World'
        assert sanitize_input('') == ''

    def test_validate_username_and_password(self):
        """Username and password validators should enforce policy."""
        assert validate_username('learner_01')[0] is True
        assert validate_username('x')[0] is False
        assert validate_password_strength('weakpass')[0] is False
        assert validate_password_strength('Str0ng!Pass')[0] is True

    def test_normalize_tags(self):
        """Normalize_tags should sanitise and deduplicate tag input."""
        tags = normalize_tags(' science, physics ,science,<script>')
        assert tags == ['science', 'physics', 'script']

    def test_rate_limit_helper(self):
        """check_rate_limit should enforce limits within the window."""
        key = "test:rate"
        # Allow first 2 attempts
        assert check_rate_limit(key, 2, 60) is True
        assert check_rate_limit(key, 2, 60) is True
        # Third should be blocked
        assert check_rate_limit(key, 2, 60) is False
        assert remaining(key, 2, 60) == 0

    def test_validate_file_type(self, app):
        """Basic MIME signature checks should accept common image types and reject others."""
        with app.app_context():
            app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
            # A minimal PNG file (PNG header + some data)
            png_header = b'\x89PNG\r\n\x1a\n\x00\x00\x00\x00'
            stream = io.BytesIO(png_header + b'ABCDEFG')
            assert validate_file_type(stream, 'test.png') is True
            # A JPEG file header
            jpeg_header = b'\xff\xd8\xff\xe0' + b'0' * 10
            stream2 = io.BytesIO(jpeg_header)
            assert validate_file_type(stream2, 'image.jpg') is True
            # Invalid content disguised as image
            bad_stream = io.BytesIO(b'This is not an image')
            assert validate_file_type(bad_stream, 'photo.png') is False


class TestFileService:
    """Integration tests for the file saving service."""

    def test_save_uploaded_file(self, app):
        """A valid file should be saved to the configured upload folder with a secure name."""
        with app.app_context():
            # Override upload configuration to use a temporary directory
            tmpdir = tempfile.mkdtemp()
            app.config['UPLOAD_FOLDER'] = tmpdir
            app.config['ALLOWED_EXTENSIONS'] = {'png'}
            # Build a fake PNG file using Werkzeug's FileStorage
            data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 10
            file_storage = FileStorage(
                stream=io.BytesIO(data),
                filename='test image.PNG',
                content_type='image/png'
            )
            # Save the file
            file_id = '1234-5678'
            saved_name = FileService.save_uploaded_file(file_storage, file_id)
            # The returned filename should be id plus the original extension as provided by ``secure_filename``.
            # ``secure_filename`` preserves the case of the extension, so here we expect ``.PNG``.
            assert saved_name == f"{file_id}.PNG"
            saved_path = os.path.join(tmpdir, saved_name)
            # The file should exist on disk
            assert os.path.isfile(saved_path)
            # Clean up
            os.remove(saved_path)

    def test_save_uploaded_file_invalid(self, app):
        """Attempting to save a file with a disallowed extension should raise a ValueError."""
        with app.app_context():
            app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
            app.config['ALLOWED_EXTENSIONS'] = {'png'}
            # Prepare a text file disguised as image
            file_storage = FileStorage(
                stream=io.BytesIO(b'Not an image'),
                filename='malware.exe',
                content_type='application/octet-stream'
            )
            with pytest.raises(ValueError):
                FileService.save_uploaded_file(file_storage, 'bad-id')
