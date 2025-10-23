import os
from flask import current_app
from app.utils.security import allowed_file, secure_filename_with_id, validate_file_type

class FileService:
    """Secure file handling service"""
    
    @staticmethod
    def save_uploaded_file(file, file_id):
        if not file or file.filename == '':
            raise ValueError("No file selected")
        
        if not allowed_file(file.filename):
            raise ValueError("File type not allowed")
        
        # Validate file using the new method
        if not validate_file_type(file.stream, file.filename):
            raise ValueError("Invalid file type")
        
        filename = secure_filename_with_id(file.filename, file_id)
        
        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        return filename
    
    @staticmethod
    def validate_file_size(file):
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        return size <= current_app.config['MAX_CONTENT_LENGTH']