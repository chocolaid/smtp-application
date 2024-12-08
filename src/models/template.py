from datetime import datetime

class Template:
    def __init__(self, name, subject, content, sender_name, is_html=True):
        self.name = name
        self.subject = subject
        self.content = content
        self.sender_name = sender_name  # Add sender name
        self.is_html = is_html
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.version = 1

    def update_content(self, subject, content, sender_name=None):
        self.subject = subject
        self.content = content
        if sender_name:
            self.sender_name = sender_name
        self.version += 1
        self.updated_at = datetime.now()