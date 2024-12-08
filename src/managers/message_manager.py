import os
import json
from datetime import datetime
from typing import Dict, Optional
from bs4 import BeautifulSoup
import re
from colorama import Fore, Style

from src.utils.security import Security
from src.utils.logger import Logger
from src.utils.validators import Validators
from src.config.settings import Settings
from src.config.constants import Defaults

class MessageManager:
    def __init__(self):
        self.security = Security()
        self.logger = Logger()
        self.templates_dir = Settings.TEMPLATES_DIR
        self.templates_file = os.path.join(self.templates_dir, 'templates.enc')
        os.makedirs(self.templates_dir, exist_ok=True)

    def _load_templates(self) -> Dict:
        """Load templates from encrypted storage."""
        try:
            if not os.path.exists(self.templates_file):
                return {}
            
            with open(self.templates_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self.security.decrypt(encrypted_data)
            return json.loads(decrypted_data)
        except Exception as e:
            self.logger.error(f"Error loading templates: {str(e)}")
            return {}

    def _save_templates(self, templates: Dict):
        """Save templates to encrypted storage."""
        try:
            encrypted_data = self.security.encrypt(json.dumps(templates))
            with open(self.templates_file, 'wb') as f:
                f.write(encrypted_data)
            self.logger.info("Templates saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving templates: {str(e)}")
            raise
    def view_templates(self):
        """Display all email templates."""
        try:
            templates = self._load_templates()
            
            if not templates:
                print(f"{Fore.YELLOW}No templates found.{Style.RESET_ALL}")
                return

            print(f"\n{Fore.CYAN}Email Templates:{Style.RESET_ALL}")
            for name, template in templates.items():
                print(f"\n{Fore.GREEN}Template: {name}{Style.RESET_ALL}")
                print(f"  Subject: {template.get('subject', 'No subject')}")
                print(f"  Content Preview: {template.get('content', 'No content')[:100]}...")

        except Exception as e:
            self.logger.error(f"Error viewing templates: {str(e)}")
            print(f"{Fore.RED}Error viewing templates: {str(e)}{Style.RESET_ALL}")
    def import_template(self, name: str, subject: str, file_path: str):
        """Import a new email template."""
        try:
            if not Validators.validate_template_name(name):
                raise ValueError("Invalid template name. Use only letters, numbers, underscore, and hyphen.")

            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Template file not found: {file_path}")

            # Read template content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        
            # Determine if content is HTML
            sender_name = input("Enter sender name for this template: ")
            if not sender_name:
                print(f"{Fore.RED}Sender name is required!{Style.RESET_ALL}")
                return

            is_html = self._is_html_content(content)

            if is_html:
                # Validate and sanitize HTML
                content = self._sanitize_html(content)

            # Create backup of the template file
            backup_path = os.path.join(
                self.templates_dir,
                f"{os.path.basename(file_path)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.enc"
            )
            encrypted_backup = self.security.encrypt(content)
            with open(backup_path, 'wb') as f:
                f.write(encrypted_backup)

            # Load existing templates
            templates = self._load_templates()

            # Add new template
            templates[name] = {
                'subject': subject,
                'content': content,
                'sender_name': sender_name,  # Add sender name
                'is_html': is_html,
                'variables': self._extract_variables(content),
                'created_at': datetime.now().isoformat(),
                'last_modified': datetime.now().isoformat(),
                'version': 1,
                'backup_path': backup_path
            }

            self._save_templates(templates)
            print(f"{Fore.GREEN}Template '{name}' imported successfully!{Style.RESET_ALL}")
            
        except Exception as e:
            self.logger.error(f"Error importing template: {str(e)}")
            raise

    def _is_html_content(self, content: str) -> bool:
        """Check if content is HTML."""
        return bool(re.search(r'<[^>]+>', content))

    def _sanitize_html(self, html: str) -> str:
        """Sanitize HTML content."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove potentially dangerous tags and attributes
            for tag in soup.find_all(True):
                if tag.name in ['script', 'style', 'iframe', 'object', 'embed']:
                    tag.decompose()
                    continue
                
                # Remove dangerous attributes
                dangerous_attrs = ['onclick', 'onload', 'onerror', 'onmouseover']
                for attr in dangerous_attrs:
                    if attr in tag.attrs:
                        del tag.attrs[attr]

            return str(soup)
        except Exception as e:
            self.logger.error(f"Error sanitizing HTML: {str(e)}")
            raise

    def _extract_variables(self, content: str) -> list:
        """Extract template variables from content."""
        # Handle both {VARIABLE} and %variable% patterns
        pattern1 = r'\{([A-Z_]+)\}'
        pattern2 = r'%(\w+)%'
        
        variables = set(re.findall(pattern1, content))
        variables.update(re.findall(pattern2, content))
        return list(variables)

    def edit_template(self, name: str = None):
        """Edit an existing template."""
        templates = self._load_templates()
        
        if not templates:
            print(f"{Fore.YELLOW}No templates found.{Style.RESET_ALL}")
            return

        if name is None:
            print(f"\n{Fore.CYAN}Available Templates:{Style.RESET_ALL}")
            for idx, template_name in enumerate(templates.keys(), 1):
                print(f"{idx}. {template_name}")
            
            try:
                choice = int(input("\nEnter template number to edit (0 to cancel): "))
                if choice == 0:
                    return
                if 1 <= choice <= len(templates):
                    name = list(templates.keys())[choice - 1]
                else:
                    print(f"{Fore.RED}Invalid choice!{Style.RESET_ALL}")
                    return
            except ValueError:
                print(f"{Fore.RED}Invalid input!{Style.RESET_ALL}")
                return

        if name not in templates:
            print(f"{Fore.RED}Template not found!{Style.RESET_ALL}")
            return

        template = templates[name]
        print(f"\n{Fore.CYAN}Current Template:{Style.RESET_ALL}")
        print(f"Subject: {template['subject']}")
        print(f"Content Type: {'HTML' if template['is_html'] else 'Text'}")
        print(f"Variables: {', '.join(template['variables'])}")
        print("\nContent:")
        print(template['content'])

        if input("\nEdit subject? (y/n): ").lower() == 'y':
            template['subject'] = input("New subject: ")

        if input("Edit content? (y/n): ").lower() == 'y':
            print("\nEnter new content (press Ctrl+D or Ctrl+Z when finished):")
            content_lines = []
            try:
                while True:
                    line = input()
                    content_lines.append(line)
            except EOFError:
                content = '\n'.join(content_lines)
                if template['is_html']:
                    content = self._sanitize_html(content)
                template['content'] = content
                template['variables'] = self._extract_variables(content)

        template['version'] += 1
        template['last_modified'] = datetime.now().isoformat()
        templates[name] = template
        
        self._save_templates(templates)
        print(f"{Fore.GREEN}Template updated successfully!{Style.RESET_ALL}")

    def delete_template(self, name: str = None):
        """Delete a template."""
        templates = self._load_templates()
        
        if not templates:
            print(f"{Fore.YELLOW}No templates found.{Style.RESET_ALL}")
            return

        if name is None:
            print(f"\n{Fore.CYAN}Available Templates:{Style.RESET_ALL}")
            for idx, template_name in enumerate(templates.keys(), 1):
                print(f"{idx}. {template_name}")
            
            try:
                choice = int(input("\nEnter template number to delete (0 to cancel): "))
                if choice == 0:
                    return
                if 1 <= choice <= len(templates):
                    name = list(templates.keys())[choice - 1]
                else:
                    print(f"{Fore.RED}Invalid choice!{Style.RESET_ALL}")
                    return
            except ValueError:
                print(f"{Fore.RED}Invalid input!{Style.RESET_ALL}")
                return

        if name in templates:
            # Create backup before deletion
            backup_path = os.path.join(
                self.templates_dir,
                f"deleted_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.enc"
            )
            encrypted_backup = self.security.encrypt(json.dumps(templates[name]))
            with open(backup_path, 'wb') as f:
                f.write(encrypted_backup)

            del templates[name]
            self._save_templates(templates)
            print(f"{Fore.GREEN}Template '{name}' deleted successfully!{Style.RESET_ALL}")
            print(f"Backup saved to: {backup_path}")
        else:
            print(f"{Fore.RED}Template not found!{Style.RESET_ALL}")

    def get_templates(self) -> Dict:
        """Get all templates."""
        return self._load_templates()

    def get_template(self, name: str) -> Optional[Dict]:
        """Get a specific template."""
        templates = self._load_templates()
        return templates.get(name)

    def send_email(self, smtp_account: dict, recipient: str, subject: str, content: str) -> bool:
        """
        Send an email using the provided SMTP account.
        
        Args:
            smtp_account (dict): SMTP account configuration
            recipient (str): Recipient email address
            subject (str): Email subject
            content (str): Email content
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.utils import formataddr

            # Create message
            msg = MIMEMultipart()
            
            # Format the From header with sender name
            sender_name = smtp_account.get('sender_name', '')
            if sender_name:
                msg['From'] = formataddr((sender_name, smtp_account['username']))
            else:
                msg['From'] = smtp_account['username']
                
            msg['To'] = recipient
            msg['Subject'] = subject

            # Attach content
            if self._is_html_content(content):
                msg.attach(MIMEText(content, 'html'))
            else:
                msg.attach(MIMEText(content, 'plain'))

            # Connect to SMTP server
            with smtplib.SMTP(smtp_account['host'], smtp_account['port']) as server:
                server.starttls()
                server.login(smtp_account['username'], smtp_account['password'])
                server.send_message(msg)

            self.logger.info(f"Email sent successfully to {recipient}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send email to {recipient}: {str(e)}")
            return False

    def preview_template(self, name: str, variables: Dict = None):
        """Preview a template with optional variable substitution."""
        template = self.get_template(name)
        if not template:
            return None

        content = template['content']
        if variables:
            for var_name, var_value in variables.items():
                content = content.replace(f"{{{var_name}}}", str(var_value))

        return {
            'subject': template['subject'],
            'content': content,
            'is_html': template['is_html']
        }