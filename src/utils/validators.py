import re
import os
from email.utils import parseaddr
from src.config.constants import Status

class Validators:
    @staticmethod
    def validate_email(email):
        """Validate email format using regex."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False
        
        # Additional checks
        _, addr = parseaddr(email)
        if not addr or '@' not in addr:
            return False
            
        return True

    @staticmethod
    def validate_template_name(name):
        """Validate template name format."""
        pattern = r'^[a-zA-Z0-9_-]+$'
        return bool(re.match(pattern, name))

    @staticmethod
    def validate_file_path(path):
        """Validate file path."""
        try:
            # Check if path is absolute
            if not os.path.isabs(path):
                path = os.path.abspath(path)
            
            # Check if parent directory exists
            parent_dir = os.path.dirname(path)
            if not os.path.exists(parent_dir):
                return False
                
            return True
        except Exception:
            return False

    @staticmethod
    def validate_campaign_name(name):
        """Validate campaign name format."""
        pattern = r'^[a-zA-Z0-9_-]{3,50}$'
        return bool(re.match(pattern, name))

    @staticmethod
    def validate_smtp_config(host, port, username, password):
        """Validate SMTP configuration."""
        if not host or not isinstance(host, str):
            return False
        
        try:
            port = int(port)
            if port < 1 or port > 65535:
                return False
        except ValueError:
            return False
            
        if not username or not password:
            return False
            
        return True