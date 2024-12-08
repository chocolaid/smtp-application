import os
import json
from colorama import Fore, Style

from src.utils.security import Security
from src.utils.logger import Logger
from src.config.settings import Settings

class SettingsManager:
    def __init__(self):
        self.security = Security()
        self.logger = Logger()
        self.settings_file = os.path.join(Settings.DATA_DIR, 'settings.enc')
        self.settings = self._load_settings()

    def _load_settings(self) -> dict:
        """Load settings from encrypted storage."""
        try:
            if not os.path.exists(self.settings_file):
                return self._default_settings()
            
            with open(self.settings_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.security.decrypt(encrypted_data)
            return json.loads(decrypted_data)
        except Exception as e:
            self.logger.error(f"Error loading settings: {str(e)}")
            return self._default_settings()

    def _save_settings(self):
        """Save settings to encrypted storage."""
        try:
            encrypted_data = self.security.encrypt(json.dumps(self.settings))
            with open(self.settings_file, 'wb') as f:
                f.write(encrypted_data)
            self.logger.info("Settings saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving settings: {str(e)}")
            raise

    def _default_settings(self) -> dict:
        """Return default settings."""
        return {
            'smtp_default_port': Settings.SMTP_DEFAULT_PORT,
            'smtp_use_tls': Settings.SMTP_USE_TLS,
            'log_level': Settings.LOG_LEVEL,
            'max_emails_per_campaign': Settings.MAX_EMAILS_PER_CAMPAIGN,
            'email_rate_limit': Settings.EMAIL_RATE_LIMIT
        }

    def view_settings(self):
        """View current settings."""
        print(f"\n{Fore.CYAN}Current Settings:{Style.RESET_ALL}")
        for key, value in self.settings.items():
            print(f"{key}: {value}")

    def update_setting(self, key: str, value):
        """Update a specific setting."""
        if key not in self.settings:
            print(f"{Fore.RED}Setting not found!{Style.RESET_ALL}")
            return

        self.settings[key] = value
        self._save_settings()
        print(f"{Fore.GREEN}Setting '{key}' updated successfully!{Style.RESET_ALL}")

    def configure_settings(self):
        """Interactively configure settings."""
        while True:
            self.view_settings()
            print("\nOptions:")
            print("1. Update setting")
            print("2. Reset to default")
            print("3. Back")
            
            choice = input("\nEnter your choice: ")
            
            if choice == "1":
                key = input("Enter setting key to update: ")
                value = input("Enter new value: ")
                try:
                    # Convert value to appropriate type
                    if isinstance(self.settings[key], bool):
                        value = value.lower() in ['true', '1', 'yes']
                    elif isinstance(self.settings[key], int):
                        value = int(value)
                    self.update_setting(key, value)
                except ValueError:
                    print(f"{Fore.RED}Invalid value type!{Style.RESET_ALL}")
            elif choice == "2":
                self.settings = self._default_settings()
                self._save_settings()
                print(f"{Fore.GREEN}Settings reset to default!{Style.RESET_ALL}")
            elif choice == "3":
                break
            else:
                print(f"{Fore.RED}Invalid choice!{Style.RESET_ALL}")