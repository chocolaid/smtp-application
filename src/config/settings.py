import os

class Settings:
    # Directories
    DATA_DIR = os.path.join(os.getcwd(), 'data')
    SMTP_DIR = os.path.join(DATA_DIR, 'smtp')
    TEMPLATES_DIR = os.path.join(DATA_DIR, 'templates')
    RECIPIENTS_DIR = os.path.join(DATA_DIR, 'recipients')
    LOGS_DIR = os.path.join(DATA_DIR, 'logs')
    BACKUPS_DIR = os.path.join(DATA_DIR, 'backups')

    # SMTP Settings
    SMTP_DEFAULT_PORT = 587
    SMTP_USE_TLS = True

    # Logging Settings
    LOG_LEVEL = 'INFO'
    LOG_FILE = os.path.join(LOGS_DIR, 'application.log')

    # Security Settings
    ENCRYPTION_KEY_PATH = os.path.join(DATA_DIR, 'encryption.key')

    # Other Settings
    MAX_EMAILS_PER_CAMPAIGN = 1000
    EMAIL_RATE_LIMIT = 10  # emails per minute