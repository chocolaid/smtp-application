import os
import platform
import getpass
import base64
import json
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from colorama import Fore, Style

class Security:
    _instance = None
    _initialized = False
    _key = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Security, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not Security._initialized:
            self._setup_secure_paths()
            self.password_verified = False
            self._load_or_create_key()
            self.cipher = Fernet(Security._key)
            Security._initialized = True

    def _setup_secure_paths(self):
        """Setup secure paths for key storage."""
        if platform.system() == "Windows":
            appdata = os.getenv('APPDATA')
            self.secure_dir = os.path.join(appdata, '.smtp_manager')
        else:
            home = os.path.expanduser('~')
            self.secure_dir = os.path.join(home, '.smtp_manager')
            
        self.key_file = os.path.join(self.secure_dir, '.key')
        self.salt_file = os.path.join(self.secure_dir, '.salt')
        os.makedirs(self.secure_dir, mode=0o700, exist_ok=True)

    def _load_or_create_key(self):
        """Load existing key or create a new one."""
        if Security._key is not None:
            return

        try:
            if os.path.exists(self.key_file) and os.path.exists(self.salt_file):
                with open(self.salt_file, 'rb') as f:
                    salt = f.read()
                
                password = self._get_password("Enter encryption password: ")
                key = self._derive_key(password, salt)
                
                # Verify the key
                if self._verify_key(key):
                    Security._key = key
                    self.password_verified = True
                else:
                    raise ValueError("Invalid password")
            else:
                Security._key = self._create_new_key()
                self.password_verified = True

        except Exception as e:
            print(f"{Fore.RED}Error loading encryption key: {str(e)}{Style.RESET_ALL}")
            raise

    def _create_new_key(self) -> bytes:
        """Create a new encryption key."""
        try:
            salt = os.urandom(16)
            with open(self.salt_file, 'wb') as f:
                f.write(salt)

            while True:
                password = self._get_password("Create encryption password: ")
                confirm = self._get_password("Confirm password: ")
                
                if password == confirm:
                    break
                print(f"{Fore.RED}Passwords do not match. Please try again.{Style.RESET_ALL}")

            key = self._derive_key(password, salt)
            
            # Save key verification data
            self._save_key_verification(key)
            
            return key

        except Exception as e:
            print(f"{Fore.RED}Error creating encryption key: {str(e)}{Style.RESET_ALL}")
            raise

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password and salt."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def _verify_key(self, key: bytes) -> bool:
        """Verify if the key is correct."""
        try:
            verification_file = os.path.join(self.secure_dir, '.verify')
            if not os.path.exists(verification_file):
                return True  # First time setup
                
            fernet = Fernet(key)
            with open(verification_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = fernet.decrypt(encrypted_data)
            return decrypted_data == b'VALID'
            
        except Exception:
            return False

    def _save_key_verification(self, key: bytes):
        """Save verification data for the key."""
        try:
            verification_file = os.path.join(self.secure_dir, '.verify')
            fernet = Fernet(key)
            encrypted_data = fernet.encrypt(b'VALID')
            
            with open(verification_file, 'wb') as f:
                f.write(encrypted_data)
                
        except Exception as e:
            print(f"{Fore.RED}Error saving key verification: {str(e)}{Style.RESET_ALL}")
            raise

    def _get_password(self, prompt: str) -> str:
        """Securely get password from user."""
        try:
            return getpass.getpass(prompt)
        except Exception as e:
            print(f"{Fore.RED}Error getting password: {str(e)}{Style.RESET_ALL}")
            raise

    def encrypt(self, data):
        """Encrypt data, handling both strings and dictionaries."""
        if not self._key:
            raise ValueError("Encryption key not initialized")
            
        try:
            if isinstance(data, (dict, list)):
                data = json.dumps(data)
            elif not isinstance(data, str):
                data = str(data)
                
            return self.cipher.encrypt(data.encode())
        except Exception as e:
            print(f"{Fore.RED}Encryption error: {str(e)}{Style.RESET_ALL}")
            raise

    def decrypt(self, encrypted_data: bytes) -> str:
        """Decrypt data using the encryption key."""
        if not self._key:
            raise ValueError("Encryption key not initialized")
            
        try:
            fernet = Fernet(self._key)
            decrypted_data = fernet.decrypt(encrypted_data)
            return decrypted_data.decode()
        except Exception as e:
            print(f"{Fore.RED}Decryption error: {str(e)}{Style.RESET_ALL}")
            raise

    def change_password(self) -> bool:
        """Change the encryption password."""
        try:
            current_password = self._get_password("Enter current password: ")
            with open(self.salt_file, 'rb') as f:
                current_salt = f.read()
            
            current_key = self._derive_key(current_password, current_salt)
            if not self._verify_key(current_key):
                print(f"{Fore.RED}Invalid current password{Style.RESET_ALL}")
                return False

            # Create new key
            new_salt = os.urandom(16)
            while True:
                new_password = self._get_password("Enter new password: ")
                confirm = self._get_password("Confirm new password: ")
                
                if new_password == confirm:
                    break
                print(f"{Fore.RED}Passwords do not match. Please try again.{Style.RESET_ALL}")

            new_key = self._derive_key(new_password, new_salt)

            # Save new salt and verification
            with open(self.salt_file, 'wb') as f:
                f.write(new_salt)
            self._save_key_verification(new_key)

            # Update instance key
            Security._key = new_key
            print(f"{Fore.GREEN}Password changed successfully{Style.RESET_ALL}")
            return True

        except Exception as e:
            print(f"{Fore.RED}Error changing password: {str(e)}{Style.RESET_ALL}")
            return False

    def verify_password(self, password: str) -> bool:
        """Verify if a password is correct."""
        try:
            with open(self.salt_file, 'rb') as f:
                salt = f.read()
            
            key = self._derive_key(password, salt)
            return self._verify_key(key)
            
        except Exception:
            return False