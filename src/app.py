import os
import platform
import subprocess
from datetime import datetime
from colorama import Fore, Style
from typing import Dict, List, Optional

from src.managers.smtp_manager import SMTPManager
from src.managers.message_manager import MessageManager
from src.managers.recipient_manager import RecipientManager
from src.managers.campaign_manager import CampaignManager
from src.managers.settings_manager import SettingsManager
from src.utils.helpers import clear_screen
from src.utils.logger import setup_logger

class SMTPApplication:
    def __init__(self):
        self.logger = setup_logger()
        self.smtp_manager = SMTPManager()
        self.message_manager = MessageManager()
        self.recipient_manager = RecipientManager()
        self.campaign_manager = CampaignManager(
            smtp_manager=self.smtp_manager,
            message_manager=self.message_manager,
            recipient_manager=self.recipient_manager
        )
        self.settings_manager = SettingsManager()
        self.current_menu = 'main'
        self.running = True

    def start(self):
        """Start the application."""
        while self.running:
            try:
                clear_screen()
                self._display_header()
                self._display_menu()
                self._handle_input()
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"{Fore.RED}An error occurred: {str(e)}{Style.RESET_ALL}")
                input("Press Enter to continue...")

    def _display_header(self):
        """Display application header."""
        print(f"{Fore.CYAN}================================{Style.RESET_ALL}")
        print(f"{Fore.CYAN}       SMTP Mail Manager        {Style.RESET_ALL}")
        print(f"{Fore.CYAN}================================{Style.RESET_ALL}\n")

    def _display_menu(self):
        """Display current menu."""
        menus = {
            'main': [
                'Manage SMTP Accounts',
                'Manage Email Templates',
                'Manage Recipients',
                'Manage Campaigns',
                'Settings',
                'View Logs',
                'Backup/Restore',
                'Exit'
            ],
            'smtp': [
                'View SMTP Accounts',
                'Add SMTP Account',
                'Import SMTP Accounts',
                'Test SMTP Accounts',
                'Delete SMTP Account',
                'Back'
            ],
            'templates': [
                'View Templates',
                'Import Template',
                'Edit Template',
                'Delete Template',
                'Back'
            ],
            'recipients': [
                'View Recipients',
                'Add Recipients',
                'Import Recipients',
                'Export Recipients',
                'Manage Tags',
                'Delete Recipients',
                'Back'
            ],
            'campaigns': [
                'View Campaigns',
                'Create Campaign',
                'Start Campaign',
                'Stop Campaign',
                'Delete Campaign',
                'Restart Campaign',
                'Back'
            ],
            'settings': [
                'View Settings',
                'Configure Settings',
                'Back'
            ],
            'backup': [
                'Create Backup',
                'Restore Backup',
                'Back'
            ]
        }

        print(f"Current Menu: {self.current_menu.upper()}\n")
        if self.current_menu in menus:
            for idx, item in enumerate(menus[self.current_menu], 1):
                print(f"{idx}. {item}")
        print()

    def _handle_input(self):
        """Handle user input."""
        choice = input("Enter your choice: ")

        if self.current_menu == 'main':
            self._handle_main_menu(choice)
        elif self.current_menu == 'smtp':
            self._handle_smtp_menu(choice)
        elif self.current_menu == 'templates':
            self._handle_templates_menu(choice)
        elif self.current_menu == 'recipients':
            self._handle_recipients_menu(choice)
        elif self.current_menu == 'campaigns':
            self._handle_campaigns_menu(choice)
        elif self.current_menu == 'settings':
            self._handle_settings_menu(choice)
        elif self.current_menu == 'backup':
            self._handle_backup_menu(choice)

    def _handle_main_menu(self, choice):
        """Handle main menu choices."""
        if choice == '1':
            self.current_menu = 'smtp'
        elif choice == '2':
            self.current_menu = 'templates'
        elif choice == '3':
            self.current_menu = 'recipients'
        elif choice == '4':
            self.current_menu = 'campaigns'
        elif choice == '5':
            self.current_menu = 'settings'
        elif choice == '6':
            self._view_logs()
        elif choice == '7':
            self.current_menu = 'backup'
        elif choice == '8':
            self.running = False
        else:
            print(f"{Fore.RED}Invalid choice!{Style.RESET_ALL}")
            input("Press Enter to continue...")

    def _handle_smtp_menu(self, choice):
        """Handle SMTP menu choices."""
        if choice == '1':
            self.smtp_manager.view_accounts()
        elif choice == '2':
            self.smtp_manager.add_account()
        elif choice == '3':
            self.smtp_manager.import_accounts()
        elif choice == '4':
            self.smtp_manager.test_accounts()
        elif choice == '5':
            self.smtp_manager.delete_account()
        elif choice == '6':
            self.current_menu = 'main'
        else:
            print(f"{Fore.RED}Invalid choice!{Style.RESET_ALL}")
        input("Press Enter to continue...")

    def _handle_templates_menu(self, choice):
        """Handle templates menu choices."""
        if choice == '1':
            self.message_manager.view_templates()
        elif choice == '2':
            name = input("Enter template name: ")
            subject = input("Enter email subject: ")
            file_path = input("Enter template file path: ")
            self.message_manager.import_template(name, subject, file_path)
        elif choice == '3':
            self.message_manager.edit_template()
        elif choice == '4':
            self.message_manager.delete_template()
        elif choice == '5':
            self.current_menu = 'main'
        else:
            print(f"{Fore.RED}Invalid choice!{Style.RESET_ALL}")
        input("Press Enter to continue...")

    def _handle_recipients_menu(self, choice):
        """Handle recipients menu choices."""
        if choice == '1':
            self.recipient_manager.view_recipients()
        elif choice == '2':
            self.recipient_manager.add_recipients()
        elif choice == '3':
            self.recipient_manager.import_recipients()
        elif choice == '4':
            self.recipient_manager.export_recipients()
        elif choice == '5':
            self.recipient_manager.manage_tags()
        elif choice == '6':
            self.recipient_manager.delete_recipients()
        elif choice == '7':
            self.current_menu = 'main'
        else:
            print(f"{Fore.RED}Invalid choice!{Style.RESET_ALL}")
        input("Press Enter to continue...")

    def _handle_campaigns_menu(self, choice):
        """Handle campaigns menu choices."""
        if choice == '1':
            self.campaign_manager.view_campaigns()
        elif choice == '2':
            self.campaign_manager.create_campaign()
        elif choice == '3':
            self.campaign_manager.start_campaign()
        elif choice == '4':
            self.campaign_manager.stop_campaign()
        elif choice == '5':
            self.campaign_manager.delete_campaign()
        elif choice == '6':
            self.campaign_manager.restart_campaign()
        elif choice == '7':
            self.current_menu = 'main'
        else:
            print(f"{Fore.RED}Invalid choice!{Style.RESET_ALL}")
        input("Press Enter to continue...")

    def _handle_settings_menu(self, choice):
        """Handle settings menu choices."""
        if choice == '1':
            self.settings_manager.view_settings()
        elif choice == '2':
            self.settings_manager.configure_settings()
        elif choice == '3':
            self.current_menu = 'main'
        else:
            print(f"{Fore.RED}Invalid choice!{Style.RESET_ALL}")
        input("Press Enter to continue...")

    def _handle_backup_menu(self, choice):
        """Handle backup menu choices."""
        if choice == '1':
            self._backup_data()
        elif choice == '2':
            self._restore_backup()
        elif choice == '3':
            self.current_menu = 'main'
        else:
            print(f"{Fore.RED}Invalid choice!{Style.RESET_ALL}")
        input("Press Enter to continue...")

    def _view_logs(self):
        """View application logs."""
        try:
            with open(self.settings_manager.settings['log_file'], 'r') as f:
                logs = f.readlines()

            print(f"\n{Fore.CYAN}Recent Logs:{Style.RESET_ALL}")
            for log in logs[-50:]:  # Show last 50 logs
                if 'ERROR' in log:
                    print(f"{Fore.RED}{log.strip()}{Style.RESET_ALL}")
                elif 'WARNING' in log:
                    print(f"{Fore.YELLOW}{log.strip()}{Style.RESET_ALL}")
                else:
                    print(log.strip())
        except Exception as e:
            print(f"{Fore.RED}Error viewing logs: {str(e)}{Style.RESET_ALL}")
        input("Press Enter to continue...")

    def _backup_data(self):
        """Backup application data."""
        try:
            backup_dir = os.path.join(
                "data/backups",
                f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            os.makedirs(backup_dir, exist_ok=True)

            # Backup all data files
            files_to_backup = [
                self.smtp_manager.data_file,
                self.message_manager.templates_file,
                self.recipient_manager.recipients_file,
                self.campaign_manager.campaigns_file,
                self.settings_manager.settings_file
            ]

            for file_path in files_to_backup:
                if os.path.exists(file_path):
                    backup_path = os.path.join(
                        backup_dir,
                        os.path.basename(file_path)
                    )
                    with open(file_path, 'rb') as src, open(backup_path, 'wb') as dst:
                        dst.write(src.read())

            print(f"{Fore.GREEN}Backup created successfully in: {backup_dir}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Backup failed: {str(e)}{Style.RESET_ALL}")
        input("Press Enter to continue...")

    def _restore_backup(self):
        """Restore from backup."""
        try:
            backup_root = "data/backups"
            if not os.path.exists(backup_root):
                print(f"{Fore.RED}No backups found!{Style.RESET_ALL}")
                return

            # List available backups
            backups = sorted([d for d in os.listdir(backup_root) if d.startswith('backup_')])
            if not backups:
                print(f"{Fore.RED}No backups found!{Style.RESET_ALL}")
                return

            print("\nAvailable backups:")
            for idx, backup in enumerate(backups, 1):
                print(f"{idx}. {backup}")

            choice = input("\nEnter backup number to restore (or 0 to cancel): ")
            if not choice.isdigit() or int(choice) < 0 or int(choice) > len(backups):
                print(f"{Fore.RED}Invalid choice!{Style.RESET_ALL}")
                return

            if choice == '0':
                return

            selected_backup = backups[int(choice) - 1]
            backup_dir = os.path.join(backup_root, selected_backup)

            # Restore all data files
            for file_name in os.listdir(backup_dir):
                backup_path = os.path.join(backup_dir, file_name)
                restore_path = os.path.join("data", file_name)
                with open(backup_path, 'rb') as src, open(restore_path, 'wb') as dst:
                    dst.write(src.read())

            print(f"{Fore.GREEN}Backup restored successfully!{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Please restart the application for changes to take effect.{Style.RESET_ALL}")
            self.running = False
        except Exception as e:
            print(f"{Fore.RED}Restore failed: {str(e)}{Style.RESET_ALL}")
        input("Press Enter to continue...")