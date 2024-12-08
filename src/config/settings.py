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

     # Update Settings
    GITHUB_TOKEN = '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' # Set this in environment variables
    GITHUB_REPO = 'https://github.com/chocolaid/smtp-application'
    CHECK_UPDATES_ON_START = True
    APP_NAME = "SMTP Manager"
    APP_AUTHOR = "OECAPPS"
    APP_BUNDLE_ID = "oec.apps.smtpmanager"
    APP_ICON_PATH = "assets/icon.ico"  # or .icns for macOS