from datetime import datetime

class Recipient:
    def __init__(self, email, tags=None):
        self.email = email
        self.tags = tags or []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def add_tag(self, tag):
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()

    def remove_tag(self, tag):
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now()