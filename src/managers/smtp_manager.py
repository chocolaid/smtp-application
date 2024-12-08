import os
import json
import smtplib
import ssl
from email.mime.text import MIMEText
from typing import Dict, List, Optional
from colorama import Fore, Style

from src.utils.security import Security
from src.utils.validators import Validators
from src.utils.logger import setup_logger
from src.config.settings import Settings

class SMTPManager:
    def __init__(self):
        self.logger = setup_logger()
        self.security = Security()
        self.data_file = os.path.join(Settings.SMTP_DIR, 'smtp_data.enc')
        self.accounts = self._load_smtp_accounts()

    def _load_smtp_accounts(self) -> dict:
        """Load SMTP accounts from encrypted file."""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'rb') as f:
                    encrypted_data = f.read()
                decrypted_data = self.security.decrypt(encrypted_data)
                if isinstance(decrypted_data, str):
                    return json.loads(decrypted_data)
                return decrypted_data
            return {}
        except Exception as e:
            self.logger.error(f"Error loading SMTP accounts: {str(e)}")
            return {}

    def _save_smtp_accounts(self, accounts: dict):
        """Save SMTP accounts to encrypted file."""
        try:
            encrypted_data = self.security.encrypt(json.dumps(accounts))
            with open(self.data_file, 'wb') as f:
                f.write(encrypted_data)
        except Exception as e:
            self.logger.error(f"Error saving SMTP accounts: {str(e)}")


    def view_accounts(self):
        """Display all SMTP accounts."""
        if not self.accounts:
            print(f"{Fore.YELLOW}No SMTP accounts found.{Style.RESET_ALL}")
            return

        print(f"\n{Fore.CYAN}SMTP Accounts:{Style.RESET_ALL}")
        for account_key, account in self.accounts.items():
            status = f"{Fore.GREEN}✓{Style.RESET_ALL}" if account.get('verified', False) else f"{Fore.RED}✗{Style.RESET_ALL}"
            print(f"\n{status} {account_key}:")
            print(f"  Host: {account['host']}")
            print(f"  Port: {account['port']}")
            print(f"  Username: {account['username']}")
            print(f"  Use TLS: {account.get('use_tls', True)}")

    def add_account(self):
        """Add a new SMTP account."""
        try:
            host = input("Enter SMTP host: ")
            port = input("Enter SMTP port [587]: ") or "587"
            username = input("Enter username/email: ")
            password = input("Enter password: ")
            use_tls = input("Use TLS? (y/n) [y]: ").lower() != 'n'

            if not all([host, port, username, password]):
                print(f"{Fore.RED}All fields are required!{Style.RESET_ALL}")
                return

            account_key = f"{username}@{host}"
            if account_key in self.accounts:
                print(f"{Fore.RED}Account already exists!{Style.RESET_ALL}")
                return

            account = {
                'host': host,
                'port': int(port),
                'username': username,
                'password': password,
                'use_tls': use_tls,
                'verified': False
            }

            # Test the connection
            if self._test_account(account_key, account):
                self.accounts[account_key] = account
                self._save_smtp_accounts(self.accounts)
                print(f"{Fore.GREEN}SMTP account added successfully!{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Failed to verify SMTP account!{Style.RESET_ALL}")

        except Exception as e:
            self.logger.error(f"Error adding SMTP account: {str(e)}")
            print(f"{Fore.RED}Error adding SMTP account: {str(e)}{Style.RESET_ALL}")

    def import_accounts(self):
        """Import SMTP accounts from a file."""
        try:
            file_path = input("Enter file path: ")
            if not os.path.exists(file_path):
                print(f"{Fore.RED}File not found!{Style.RESET_ALL}")
                return

            new_count = 0
            failed_count = 0
            print(f"\n{Fore.CYAN}Importing and testing SMTP accounts...{Style.RESET_ALL}")
            
            with open(file_path, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        parts = line.strip().split('|')
                        if len(parts) < 4:
                            print(f"{Fore.YELLOW}Line {line_num}: Invalid format, skipping...{Style.RESET_ALL}")
                            continue

                        host, port, username, password = parts[:4]
                        use_tls = True if len(parts) < 5 else parts[4].lower() == 'true'

                        account_key = f"{username}@{host}"
                        if account_key in self.accounts:
                            print(f"{Fore.YELLOW}Line {line_num}: Account {account_key} already exists, skipping...{Style.RESET_ALL}")
                            continue

                        account = {
                            'host': host,
                            'port': int(port),
                            'username': username,
                            'password': password,
                            'use_tls': use_tls,
                            'verified': False
                        }

                        # Test account before adding
                        print(f"Testing {account_key}...", end=' ', flush=True)
                        if self._test_account(account_key, account):
                            account['verified'] = True
                            self.accounts[account_key] = account
                            new_count += 1
                            print(f"{Fore.GREEN}Success{Style.RESET_ALL}")
                        else:
                            failed_count += 1
                            print(f"{Fore.RED}Failed{Style.RESET_ALL}")

                    except Exception as e:
                        failed_count += 1
                        self.logger.error(f"Error processing line {line_num}: {str(e)}")
                        print(f"{Fore.RED}Line {line_num}: Error - {str(e)}{Style.RESET_ALL}")
                        continue

                if new_count > 0:
                    self._save_smtp_accounts(self.accounts)
                    print(f"\n{Fore.GREEN}Successfully imported {new_count} SMTP accounts{Style.RESET_ALL}")
                if failed_count > 0:
                    print(f"{Fore.RED}Failed to import {failed_count} accounts{Style.RESET_ALL}")
                if new_count == 0 and failed_count == 0:
                    print(f"{Fore.YELLOW}No new SMTP accounts added{Style.RESET_ALL}")

        except Exception as e:
            self.logger.error(f"Error importing SMTP accounts: {str(e)}")
            print(f"{Fore.RED}Error importing accounts: {str(e)}{Style.RESET_ALL}")
            
    def _test_account(self, account_key: str, account: dict, verify_ssl: bool = True) -> bool:
        """Test a single SMTP account."""
        try:
            # First try with SSL verification
            context = ssl.create_default_context()
            with smtplib.SMTP(account['host'], account['port']) as server:
                server.starttls(context=context)
                server.login(account['username'], account['password'])
            return True
        except ssl.SSLCertVerificationError:
            try:
                # If SSL verification fails, try without it
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                
                with smtplib.SMTP(account['host'], account['port']) as server:
                    server.starttls(context=context)
                    server.login(account['username'], account['password'])
                print(f"{Fore.YELLOW}Warning: Connected with disabled SSL verification for {account_key}{Style.RESET_ALL}")
                return True
            except Exception as e:
                self.logger.error(f"SMTP test failed for {account_key}: {str(e)}")
                return False
        except Exception as e:
            self.logger.error(f"SMTP test failed for {account_key}: {str(e)}")
            return False

    def test_accounts(self):
        """Test all SMTP accounts."""
        if not self.accounts:
            print(f"{Fore.YELLOW}No SMTP accounts to test.{Style.RESET_ALL}")
            return

        print(f"\n{Fore.CYAN}Testing SMTP Accounts:{Style.RESET_ALL}")
        for account_key, account in self.accounts.items():
            try:
                if self._test_account(account_key, account):
                    account['verified'] = True
                    print(f"{Fore.GREEN}✓ {account_key}: Connection successful{Style.RESET_ALL}")
                else:
                    account['verified'] = False
                    print(f"{Fore.RED}✗ {account_key}: Connection failed{Style.RESET_ALL}")
            except Exception as e:
                account['verified'] = False
                print(f"{Fore.RED}✗ {account_key}: {str(e)}{Style.RESET_ALL}")

        self._save_smtp_accounts(self.accounts)

    def delete_account(self):
        """Delete an SMTP account."""
        if not self.accounts:
            print(f"{Fore.YELLOW}No SMTP accounts to delete.{Style.RESET_ALL}")
            return

        print("\nAvailable accounts:")
        for idx, account_key in enumerate(self.accounts.keys(), 1):
            print(f"{idx}. {account_key}")

        try:
            choice = input("\nEnter account number to delete (or 0 to cancel): ")
            if not choice.isdigit() or int(choice) < 0 or int(choice) > len(self.accounts):
                print(f"{Fore.RED}Invalid choice!{Style.RESET_ALL}")
                return

            if choice == '0':
                return

            account_key = list(self.accounts.keys())[int(choice) - 1]
            confirm = input(f"{Fore.RED}Are you sure you want to delete {account_key}? (yes/no): {Style.RESET_ALL}")
            
            if confirm.lower() == 'yes':
                del self.accounts[account_key]
                self._save_smtp_accounts(self.accounts)
                print(f"{Fore.GREEN}Account deleted successfully!{Style.RESET_ALL}")
            else:
                print("Deletion cancelled.")

        except Exception as e:
            self.logger.error(f"Error deleting SMTP account: {str(e)}")
            print(f"{Fore.RED}Error deleting account: {str(e)}{Style.RESET_ALL}")

    def get_verified_accounts(self) -> List[Dict]:
        """Return list of verified SMTP accounts."""
        return [
            {**account, 'key': key}
            for key, account in self.accounts.items()
            if account.get('verified', False)
        ]

    def send_test_email(self, account: Dict, to_email: str) -> bool:
        """Send a test email using specified SMTP account."""
        try:
            msg = MIMEText("This is a test email from SMTP Manager.")
            msg['Subject'] = "SMTP Test Email"
            msg['From'] = account['username']
            msg['To'] = to_email

            context = ssl.create_default_context()
            with smtplib.SMTP(account['host'], account['port']) as server:
                if account.get('use_tls', True):
                    server.starttls(context=context)
                server.login(account['username'], account['password'])
                server.send_message(msg)
            return True
        except Exception as e:
            self.logger.error(f"Error sending test email: {str(e)}")
            return False