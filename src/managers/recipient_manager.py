import os
import json
import csv
from datetime import datetime
from typing import Dict, List, Tuple, Set
from collections import defaultdict
import pandas as pd
from colorama import Fore, Style

from src.utils.security import Security
from src.utils.logger import Logger
from src.utils.validators import Validators
from src.config.settings import Settings

class RecipientManager:
    def __init__(self):
        self.security = Security()
        self.logger = Logger()
        self.recipients_dir = Settings.RECIPIENTS_DIR
        self.recipients_file = os.path.join(self.recipients_dir, 'recipients.enc')
        self.tags = defaultdict(list)
        os.makedirs(self.recipients_dir, exist_ok=True)
        self._load_recipients()

    def _load_recipients(self):
        """Load recipients from encrypted storage."""
        try:
            if not os.path.exists(self.recipients_file):
                return
            
            with open(self.recipients_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.security.decrypt(encrypted_data)
            data = json.loads(decrypted_data)
            self.tags = defaultdict(list, data)
            
        except Exception as e:
            self.logger.error(f"Error loading recipients: {str(e)}")
            self.tags = defaultdict(list)

    def _validate_email(self, email: str) -> bool:
        """Validate email format."""
        try:
            # Basic email validation
            if not email or '@' not in email or '.' not in email:
                return False
                
            # Split email into local and domain parts
            local, domain = email.rsplit('@', 1)
            
            # Check local part
            if not local or len(local) > 64:
                return False
                
            # Check domain part
            if not domain or len(domain) > 255:
                return False
                
            # Check for valid characters
            allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.!#$%&'*+-/=?^_`{|}~@")
            if not all(c in allowed_chars for c in email):
                return False
                
            # Check for consecutive dots
            if '..' in local or '..' in domain:
                return False
                
            # Check if domain has at least one dot
            if '.' not in domain:
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating email {email}: {str(e)}")
            return False

    def add_recipients(self):
        """Add new recipients with tags."""
        try:
            print(f"\n{Fore.CYAN}Add Recipients{Style.RESET_ALL}")
            print("Enter recipient details (leave email empty to finish):")
            
            while True:
                # Get recipient email
                email = input("\nEmail: ").strip()
                if not email:
                    break
                    
                # Validate email format
                if not self._validate_email(email):
                    print(f"{Fore.RED}Invalid email format!{Style.RESET_ALL}")
                    continue
                    
                # Check if email already exists
                existing_tags = self._find_recipient_tags(email)
                if existing_tags:
                    print(f"{Fore.YELLOW}Email already exists with tags: {', '.join(existing_tags)}{Style.RESET_ALL}")
                    continue
                
                # Get tags for the recipient
                print("Enter tags (comma-separated, leave empty if none):")
                tags_input = input("Tags: ").strip()
                
                # Process tags
                if tags_input:
                    tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
                else:
                    tags = ['default']
                
                # Add recipient to each tag
                for tag in tags:
                    if email not in self.tags[tag]:
                        self.tags[tag].append(email)
                
                print(f"{Fore.GREEN}Recipient added successfully!{Style.RESET_ALL}")
            
            # Save changes
            if self._save_recipients():
                print(f"\n{Fore.GREEN}All recipients saved successfully!{Style.RESET_ALL}")
            
        except Exception as e:
            self.logger.error(f"Error adding recipients: {str(e)}")
            print(f"{Fore.RED}Error adding recipients: {str(e)}{Style.RESET_ALL}")

    def add_recipients(self):
        """Add new recipients with tags."""
        try:
            print(f"\n{Fore.CYAN}Add Recipients{Style.RESET_ALL}")
            print("Enter recipient details (leave email empty to finish):")
            
            while True:
                # Get recipient email
                email = input("\nEmail: ").strip()
                if not email:
                    break
                    
                # Validate email format
                if not self._validate_email(email):
                    print(f"{Fore.RED}Invalid email format!{Style.RESET_ALL}")
                    continue
                    
                # Check if email already exists
                existing_tags = self._find_recipient_tags(email)
                if existing_tags:
                    print(f"{Fore.YELLOW}Email already exists with tags: {', '.join(existing_tags)}{Style.RESET_ALL}")
                    continue
                
                # Get tags for the recipient
                print("Enter tags (comma-separated, leave empty if none):")
                tags_input = input("Tags: ").strip()
                
                # Process tags
                if tags_input:
                    tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
                else:
                    tags = ['default']
                
                # Add recipient to each tag
                for tag in tags:
                    if email not in self.tags[tag]:
                        self.tags[tag].append(email)
                
                print(f"{Fore.GREEN}Recipient added successfully!{Style.RESET_ALL}")
            
            # Save changes
            if self._save_recipients():
                print(f"\n{Fore.GREEN}All recipients saved successfully!{Style.RESET_ALL}")
            
        except Exception as e:
            self.logger.error(f"Error adding recipients: {str(e)}")
            print(f"{Fore.RED}Error adding recipients: {str(e)}{Style.RESET_ALL}")
    
    def _find_recipient_tags(self, email: str) -> List[str]:
        """Find all tags that contain the given email."""
        existing_tags = []
        for tag, emails in self.tags.items():
            if email in emails:
                existing_tags.append(tag)
        return existing_tags
    def _save_recipients(self):
        """Save recipients to encrypted storage."""
        try:
            encrypted_data = self.security.encrypt(json.dumps(dict(self.tags)))
            with open(self.recipients_file, 'wb') as f:
                f.write(encrypted_data)
            self.logger.info("Recipients saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving recipients: {str(e)}")
            raise
    def import_recipients(self):
        """Import recipients from a file."""
        print(f"\n{Fore.CYAN}Import Recipients{Style.RESET_ALL}")
        print("1. Import from CSV")
        print("2. Import from Excel")
        print("3. Import from Text file")
        
        choice = input("\nEnter your choice (0 to cancel): ")
        
        if choice == "0":
            return
            
        file_path = input("Enter file path: ")
        if not os.path.exists(file_path):
            print(f"{Fore.RED}File not found!{Style.RESET_ALL}")
            return

        tag = input("Enter tag for these recipients: ").strip()
        if not tag:
            print(f"{Fore.RED}Tag cannot be empty!{Style.RESET_ALL}")
            return

        try:
            if choice == "1":
                self._import_from_csv(file_path, tag)
            elif choice == "2":
                self._import_from_excel(file_path, tag)
            elif choice == "3":
                self._import_from_text(file_path, tag)
            else:
                print(f"{Fore.RED}Invalid choice!{Style.RESET_ALL}")
                return
                
        except Exception as e:
            self.logger.error(f"Error importing recipients: {str(e)}")
            print(f"{Fore.RED}Error importing recipients: {str(e)}{Style.RESET_ALL}")

    def _import_from_csv(self, file_path: str, tag: str):
        """Import recipients from CSV file."""
        total = 0
        valid = 0
        duplicates = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader)  # Skip header row
                email_col = self._find_email_column(headers)
                
                if email_col is None:
                    raise ValueError("No email column found in CSV file")
                
                for row in reader:
                    total += 1
                    if len(row) > email_col:
                        email = row[email_col].strip()
                        if self._add_recipient(email, tag):
                            valid += 1
                        else:
                            duplicates += 1
                            
            self._save_recipients()
            self._print_import_summary(total, valid, duplicates)
            
        except Exception as e:
            raise Exception(f"CSV import failed: {str(e)}")

    def _import_from_excel(self, file_path: str, tag: str):
        """Import recipients from Excel file."""
        total = 0
        valid = 0
        duplicates = 0
        
        try:
            df = pd.read_excel(file_path)
            email_col = self._find_email_column(df.columns)
            
            if email_col is None:
                raise ValueError("No email column found in Excel file")
                
            for email in df[email_col]:
                total += 1
                if isinstance(email, str) and self._add_recipient(email.strip(), tag):
                    valid += 1
                else:
                    duplicates += 1
                    
            self._save_recipients()
            self._print_import_summary(total, valid, duplicates)
            
        except Exception as e:
            raise Exception(f"Excel import failed: {str(e)}")

    def _import_from_text(self, file_path: str, tag: str):
        """Import recipients from text file."""
        total = 0
        valid = 0
        duplicates = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    total += 1
                    email = line.strip()
                    if self._add_recipient(email, tag):
                        valid += 1
                    else:
                        duplicates += 1
                        
            self._save_recipients()
            self._print_import_summary(total, valid, duplicates)
            
        except Exception as e:
            raise Exception(f"Text file import failed: {str(e)}")

    def _find_email_column(self, headers: List[str]) -> int:
        """Find the email column in the headers."""
        email_keywords = ['email', 'e-mail', 'mail', 'email address']
        for idx, header in enumerate(headers):
            if any(keyword in header.lower() for keyword in email_keywords):
                return idx
        return None

    def _add_recipient(self, email: str, tag: str) -> bool:
        """Add a single recipient to a tag."""
        if not email or not Validators.validate_email(email):
            return False
            
        # Check for duplicates across all tags
        for existing_tag, emails in self.tags.items():
            if email in emails and existing_tag != tag:
                self.logger.warning(f"Email {email} already exists in tag {existing_tag}")
                
        if email not in self.tags[tag]:
            self.tags[tag].append(email)
            return True
        return False

    def _print_import_summary(self, total: int, valid: int, duplicates: int):
        """Print import summary."""
        print(f"\n{Fore.CYAN}Import Summary:{Style.RESET_ALL}")
        print(f"Total processed: {total}")
        print(f"Valid emails: {valid}")
        print(f"Duplicates/Invalid: {duplicates}")

    def export_recipients(self):
        """Export recipients to a file."""
        if not self.tags:
            print(f"{Fore.YELLOW}No recipients to export.{Style.RESET_ALL}")
            return

        print(f"\n{Fore.CYAN}Export Recipients{Style.RESET_ALL}")
        print("1. Export all recipients")
        print("2. Export specific tag")
        
        choice = input("\nEnter your choice (0 to cancel): ")
        if choice == "0":
            return

        export_format = input("Export format (csv/excel/txt): ").lower()
        if export_format not in ['csv', 'excel', 'txt']:
            print(f"{Fore.RED}Invalid format!{Style.RESET_ALL}")
            return

        try:
            if choice == "1":
                self._export_all_recipients(export_format)
            elif choice == "2":
                tag = input("Enter tag to export: ")
                if tag in self.tags:
                    self._export_tag_recipients(tag, export_format)
                else:
                    print(f"{Fore.RED}Tag not found!{Style.RESET_ALL}")
        except Exception as e:
            self.logger.error(f"Error exporting recipients: {str(e)}")
            print(f"{Fore.RED}Error exporting recipients: {str(e)}{Style.RESET_ALL}")

    def _export_all_recipients(self, format: str):
        """Export all recipients."""
        filename = f"all_recipients_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        data = []
        
        for tag, emails in self.tags.items():
            for email in emails:
                data.append({'Email': email, 'Tag': tag})
                
        self._save_export(data, filename, format)

    def _export_tag_recipients(self, tag: str, format: str):
        """Export recipients from a specific tag."""
        filename = f"recipients_{tag}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        data = [{'Email': email, 'Tag': tag} for email in self.tags[tag]]
        self._save_export(data, filename, format)

    def _save_export(self, data: List[Dict], filename: str, format: str):
        """Save exported data to file."""
        export_dir = os.path.join(self.recipients_dir, 'exports')
        os.makedirs(export_dir, exist_ok=True)
        
        if format == 'csv':
            filepath = os.path.join(export_dir, f"{filename}.csv")
            pd.DataFrame(data).to_csv(filepath, index=False)
        elif format == 'excel':
            filepath = os.path.join(export_dir, f"{filename}.xlsx")
            pd.DataFrame(data).to_excel(filepath, index=False)
        else:  # txt
            filepath = os.path.join(export_dir, f"{filename}.txt")
            with open(filepath, 'w', encoding='utf-8') as f:
                for item in data:
                    f.write(f"{item['Email']}\n")
                    
        print(f"{Fore.GREEN}Exported to: {filepath}{Style.RESET_ALL}")

    def get_recipients(self, tag: str) -> List[str]:
        """Get recipients for a specific tag."""
        if tag.lower() == 'all':
            all_recipients = set()
            for recipients in self.tags.values():
                all_recipients.update(recipients)
            return list(all_recipients)
        return self.tags.get(tag, [])

    def get_recipients_by_tags(self, tags: List[str]) -> List[str]:
        """Get all unique recipients from specified tags."""
        try:
            all_recipients = set()  # Using set for automatic deduplication
            
            # Handle 'all' tag specially
            if 'all' in tags:
                for recipients in self.tags.values():
                    all_recipients.update(recipients)
                return list(all_recipients)
            
            # Get recipients from specified tags
            for tag in tags:
                if tag in self.tags:
                    all_recipients.update(self.tags[tag])
                else:
                    self.logger.warning(f"Tag '{tag}' not found")
                    
            return list(all_recipients)
            
        except Exception as e:
            self.logger.error(f"Error getting recipients by tags: {str(e)}")
            raise

    def get_tag_stats(self) -> Tuple[List[Dict], int]:
        """Get statistics about tags and recipients."""
        stats = []
        total_emails = set()
        
        for tag, emails in self.tags.items():
            unique_emails = list(dict.fromkeys(emails))
            stats.append({
                'tag': tag,
                'count': len(unique_emails)
            })
            total_emails.update(unique_emails)
        
        return stats, len(total_emails)

    def view_recipients(self):
        """View recipients and their tags."""
        if not self.tags:
            print(f"{Fore.YELLOW}No recipients found.{Style.RESET_ALL}")
            return

        stats, total = self.get_tag_stats()
        print(f"\n{Fore.CYAN}Recipient Statistics:{Style.RESET_ALL}")
        print(f"Total unique recipients: {total}")
        
        for stat in stats:
            print(f"\nTag: {stat['tag']}")
            print(f"Count: {stat['count']}")
            
            if input("View emails in this tag? (y/n) [n to skip to next tag if more tags available]: ").lower() == 'y':
                for email in self.tags[stat['tag']]:
                    print(f"- {email}")

    def manage_tags(self):
        """Manage recipient tags."""
        while True:
            print(f"\n{Fore.CYAN}Tag Management{Style.RESET_ALL}")
            print("1. Rename tag")
            print("2. Merge tags")
            print("3. Delete tag")
            print("4. Back")
            
            choice = input("\nEnter your choice: ")
            
            if choice == "1":
                self._rename_tag()
            elif choice == "2":
                self._merge_tags()
            elif choice == "3":
                self._delete_tag()
            elif choice == "4":
                break
            else:
                print(f"{Fore.RED}Invalid choice!{Style.RESET_ALL}")

    def _rename_tag(self):
        """Rename a tag."""
        if not self.tags:
            print(f"{Fore.YELLOW}No tags found.{Style.RESET_ALL}")
            return

        print("\nAvailable tags:")
        for tag in self.tags:
            print(f"- {tag}")

        old_tag = input("\nEnter tag to rename: ")
        if old_tag not in self.tags:
            print(f"{Fore.RED}Tag not found!{Style.RESET_ALL}")
            return

        new_tag = input("Enter new tag name: ")
        if new_tag in self.tags:
            print(f"{Fore.RED}Tag already exists!{Style.RESET_ALL}")
            return

        self.tags[new_tag] = self.tags.pop(old_tag)
        self._save_recipients()
        print(f"{Fore.GREEN}Tag renamed successfully!{Style.RESET_ALL}")

    def _merge_tags(self):
        """Merge two tags."""
        if len(self.tags) < 2:
            print(f"{Fore.YELLOW}Not enough tags to merge.{Style.RESET_ALL}")
            return

        print("\nAvailable tags:")
        for tag in self.tags:
            print(f"- {tag}")

        tag1 = input("\nEnter first tag: ")
        tag2 = input("Enter second tag: ")

        if tag1 not in self.tags or tag2 not in self.tags:
            print(f"{Fore.RED}One or both tags not found!{Style.RESET_ALL}")
            return

        new_tag = input("Enter name for merged tag: ")
        if new_tag in self.tags:
            print(f"{Fore.RED}Tag already exists!{Style.RESET_ALL}")
            return

        # Merge recipients and remove duplicates
        merged_recipients = list(set(self.tags[tag1] + self.tags[tag2]))
        self.tags[new_tag] = merged_recipients

        # Delete old tags
        del self.tags[tag1]
        del self.tags[tag2]

        self._save_recipients()
        print(f"{Fore.GREEN}Tags merged successfully!{Style.RESET_ALL}")

    def delete_recipients(self):
        """Delete recipients from a tag."""
        if not self.tags:
            print(f"{Fore.YELLOW}No recipients found.{Style.RESET_ALL}")
            return

        print("\nAvailable tags:")
        for tag in self.tags:
            print(f"- {tag}")

        tag = input("\nEnter tag to delete from (or 'all' for all tags): ")
        
        if tag.lower() == 'all':
            confirm = input(f"{Fore.RED}Are you sure you want to delete ALL recipients? (yes/no): {Style.RESET_ALL}")
            if confirm.lower() == 'yes':
                self.tags.clear()
                self._save_recipients()
                print(f"{Fore.GREEN}All recipients deleted successfully!{Style.RESET_ALL}")
        elif tag in self.tags:
            print(f"\nCurrent recipients in tag '{tag}':")
            for email in self.tags[tag]:
                print(f"- {email}")
                
            confirm = input(f"\n{Fore.RED}Are you sure you want to delete this tag? (yes/no): {Style.RESET_ALL}")
            if confirm.lower() == 'yes':
                del self.tags[tag]
                self._save_recipients()
                print(f"{Fore.GREEN}Tag deleted successfully!{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Tag not found!{Style.RESET_ALL}")