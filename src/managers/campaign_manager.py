import os
import json
import threading
from datetime import datetime
from typing import Dict, List, Optional
from colorama import Fore, Style

from src.models.campaign import Campaign
from src.utils.security import Security
from src.utils.rate_limiter import RateLimiter
from src.utils.logger import setup_logger
from src.config.settings import Settings
from src.config.constants import Status

class CampaignManager:
    def __init__(self, smtp_manager, message_manager, recipient_manager):
        self.logger = setup_logger()
        self.security = Security()
        self.smtp_manager = smtp_manager
        self.message_manager = message_manager
        self.recipient_manager = recipient_manager
        self.campaigns_file = os.path.join(Settings.DATA_DIR, 'campaigns', 'campaigns.enc')
        self.active_campaigns = self._load_campaigns()
        self.running_campaigns = {}
        self.rate_limiter = RateLimiter(
            Settings.EMAIL_RATE_LIMIT,
            60  # 1 minute window
        )

    def _load_campaigns(self) -> Dict:
        """Load campaigns from encrypted file."""
        try:
            if os.path.exists(self.campaigns_file):
                encrypted_data = open(self.campaigns_file, 'rb').read()
                decrypted_data = self.security.decrypt(encrypted_data)
                return json.loads(decrypted_data)
            return {}
        except Exception as e:
            self.logger.error(f"Error loading campaigns: {str(e)}")
            return {}

    def _save_campaigns(self):
        """Save campaigns to encrypted file."""
        try:
            os.makedirs(os.path.dirname(self.campaigns_file), exist_ok=True)
            encrypted_data = self.security.encrypt(json.dumps(self.active_campaigns))
            with open(self.campaigns_file, 'wb') as f:
                f.write(encrypted_data)
        except Exception as e:
            self.logger.error(f"Error saving campaigns: {str(e)}")
            raise

    def view_campaigns(self):
        """Display all campaigns."""
        if not self.active_campaigns:
            print(f"{Fore.YELLOW}No campaigns found.{Style.RESET_ALL}")
            return

        print(f"\n{Fore.CYAN}Campaigns:{Style.RESET_ALL}")
        for campaign_id, campaign_data in self.active_campaigns.items():
            status_color = {
                Status.PENDING: Fore.BLUE,
                Status.IN_PROGRESS: Fore.YELLOW,
                Status.COMPLETED: Fore.GREEN,
                Status.FAILED: Fore.RED
            }.get(campaign_data['status'], '')

            print(f"\nCampaign ID: {campaign_id}")
            print(f"Name: {campaign_data['name']}")
            print(f"Template: {campaign_data['template_name']}")
            print(f"Status: {status_color}{campaign_data['status']}{Style.RESET_ALL}")
            print(f"Stats: {campaign_data['stats']}")
            if campaign_data['schedule_time']:
                print(f"Scheduled: {campaign_data['schedule_time']}")

    def create_campaign(self):
        """Create a new campaign."""
        try:
            # Get campaign details
            name = input("Enter campaign name: ")
            if not name:
                print(f"{Fore.RED}Campaign name is required!{Style.RESET_ALL}")
                return

            # Get template
            templates = self.message_manager.get_templates()
            if not templates:
                print(f"{Fore.RED}No templates available. Please create a template first.{Style.RESET_ALL}")
                return

            print("\nAvailable templates:")
            for idx, (template_name, template_data) in enumerate(templates.items(), 1):
                sender = template_data.get('sender_name', 'No sender specified')
                print(f"{idx}. {template_name} (Sender: {sender})")

            template_choice = input("\nSelect template number: ")
            if not template_choice.isdigit() or int(template_choice) < 1 or int(template_choice) > len(templates):
                print(f"{Fore.RED}Invalid template choice!{Style.RESET_ALL}")
                return

            template_name = list(templates.keys())[int(template_choice) - 1]
            template = templates[template_name]

            # Get SMTP accounts
            smtp_accounts = self.smtp_manager.get_verified_accounts()
            if not smtp_accounts:
                print(f"{Fore.RED}No verified SMTP accounts available.{Style.RESET_ALL}")
                return

            # Display SMTP account selection
            print("\nAvailable SMTP accounts:")
            for idx, account in enumerate(smtp_accounts, 1):
                print(f"{idx}. {account['username']} ({account['host']})")
            print(f"{len(smtp_accounts) + 1}. Use all accounts")

            smtp_choice = input("\nSelect SMTP account number: ")
            if not smtp_choice.isdigit() or int(smtp_choice) < 1 or int(smtp_choice) > len(smtp_accounts) + 1:
                print(f"{Fore.RED}Invalid SMTP account choice!{Style.RESET_ALL}")
                return

            # Set selected SMTP accounts
            if int(smtp_choice) == len(smtp_accounts) + 1:
                selected_smtp_accounts = smtp_accounts
                print(f"{Fore.GREEN}Selected all SMTP accounts{Style.RESET_ALL}")
            else:
                selected_smtp_accounts = [smtp_accounts[int(smtp_choice) - 1]]
                print(f"{Fore.GREEN}Selected SMTP account: {selected_smtp_accounts[0]['username']}{Style.RESET_ALL}")

            # Get recipient tags
            recipient_tags = self.recipient_manager.get_tag_stats()
            if not recipient_tags:
                print(f"{Fore.RED}No recipient tags available. Please add recipients first.{Style.RESET_ALL}")
                return

            print("\nAvailable recipient tags:")
            for stat in recipient_tags[0]:  # recipient_tags returns (stats, total)
                print(f"- {stat['tag']} ({stat['count']} recipients)")

            tags_input = input("\nEnter tags (comma-separated): ").split(',')
            selected_tags = [tag.strip() for tag in tags_input if tag.strip()]

            # Validate tags
            available_tags = [stat['tag'] for stat in recipient_tags[0]]
            invalid_tags = [tag for tag in selected_tags if tag not in available_tags]
            if invalid_tags:
                print(f"{Fore.RED}Invalid tags: {', '.join(invalid_tags)}{Style.RESET_ALL}")
                return

            # Get scheduling options
            schedule_option = input("\nDo you want to schedule this campaign? (y/n): ").lower()
            schedule_time = None
            if schedule_option == 'y':
                while True:
                    schedule_input = input("Enter schedule time (YYYY-MM-DD HH:MM): ")
                    try:
                        schedule_time = datetime.strptime(schedule_input, "%Y-%m-%d %H:%M")
                        if schedule_time <= datetime.now():
                            print(f"{Fore.RED}Schedule time must be in the future!{Style.RESET_ALL}")
                            continue
                        break
                    except ValueError:
                        print(f"{Fore.RED}Invalid date format. Please use YYYY-MM-DD HH:MM{Style.RESET_ALL}")

            # Create campaign object
            campaign = Campaign(
                name=name,
                template_name=template_name,
                recipient_tags=selected_tags,
                smtp_accounts=selected_smtp_accounts,
                schedule_time=schedule_time
            )

            # Show campaign summary
            print(f"\n{Fore.CYAN}Campaign Summary:{Style.RESET_ALL}")
            print(f"Name: {campaign.name}")
            print(f"Template: {campaign.template_name}")
            print(f"Sender Name: {template.get('sender_name', 'Not specified')}")
            print(f"SMTP Accounts: {len(selected_smtp_accounts)}")
            print(f"Recipient Tags: {', '.join(campaign.recipient_tags)}")
            if schedule_time:
                print(f"Scheduled for: {schedule_time.strftime('%Y-%m-%d %H:%M')}")

            # Confirm creation
            confirm = input(f"\n{Fore.YELLOW}Create this campaign? (yes/no): {Style.RESET_ALL}")
            if confirm.lower() != 'yes':
                print("Campaign creation cancelled.")
                return

            # Save campaign
            self.active_campaigns[campaign.id] = vars(campaign)
            self._save_campaigns()
            print(f"\n{Fore.GREEN}Campaign created successfully!{Style.RESET_ALL}")
            print(f"Campaign ID: {campaign.id}")

        except Exception as e:
            self.logger.error(f"Error creating campaign: {str(e)}")
            print(f"{Fore.RED}Error creating campaign: {str(e)}{Style.RESET_ALL}")
        
    def start_campaign(self):
        """Start a campaign."""
        pending_campaigns = {
            k: v for k, v in self.active_campaigns.items()
            if v['status'] == Status.PENDING
        }

        if not pending_campaigns:
            print(f"{Fore.YELLOW}No pending campaigns found.{Style.RESET_ALL}")
            return

        print("\nPending campaigns:")
        for idx, (campaign_id, campaign_data) in enumerate(pending_campaigns.items(), 1):
            print(f"{idx}. {campaign_data['name']} ({campaign_id})")

        choice = input("\nEnter campaign number to start: ")
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(pending_campaigns):
            print(f"{Fore.RED}Invalid choice!{Style.RESET_ALL}")
            return

        try:
            campaign_id = list(pending_campaigns.keys())[int(choice) - 1]
            campaign_data = pending_campaigns[campaign_id]

            # Validate campaign data before starting
            if not campaign_data.get('template_name'):
                print(f"{Fore.RED}Campaign template is missing!{Style.RESET_ALL}")
                return

            if not campaign_data.get('recipient_tags'):
                print(f"{Fore.RED}Campaign recipient tags are missing!{Style.RESET_ALL}")
                return

            if not campaign_data.get('smtp_accounts'):
                print(f"{Fore.RED}Campaign SMTP accounts are missing!{Style.RESET_ALL}")
                return

            # Check if campaign is already running
            if campaign_id in self.running_campaigns:
                print(f"{Fore.RED}Campaign is already running!{Style.RESET_ALL}")
                return

            # Set initial campaign status and stats
            self.active_campaigns[campaign_id]['status'] = Status.IN_PROGRESS
            self.active_campaigns[campaign_id]['start_time'] = datetime.now().isoformat()
            self.active_campaigns[campaign_id]['stats'] = {
                'total': 0,
                'sent': 0,
                'failed': 0,
                'remaining': 0
            }
            self._save_campaigns()

            # Start campaign in a new thread
            campaign_thread = threading.Thread(
                target=self._process_campaign,
                args=(campaign_id,),
                daemon=True
            )
            campaign_thread.start()
            self.running_campaigns[campaign_id] = campaign_thread

            print(f"{Fore.GREEN}Campaign started successfully!{Style.RESET_ALL}")
            self.logger.info(f"Campaign {campaign_id} started successfully")

        except IndexError:
            print(f"{Fore.RED}Invalid campaign selection!{Style.RESET_ALL}")
            self.logger.error("Invalid campaign selection")
        except Exception as e:
            self.logger.error(f"Error starting campaign: {str(e)}")
            print(f"{Fore.RED}Error starting campaign: {str(e)}{Style.RESET_ALL}")
            
            # Revert status if there was an error
            if 'campaign_id' in locals():
                self.active_campaigns[campaign_id]['status'] = Status.PENDING
                self._save_campaigns()
    def stop_campaign(self):
        """Stop a running campaign."""
        running_campaigns = {
            k: v for k, v in self.active_campaigns.items()
            if v['status'] == Status.IN_PROGRESS
        }

        if not running_campaigns:
            print(f"{Fore.YELLOW}No running campaigns found.{Style.RESET_ALL}")
            return

        print("\nRunning campaigns:")
        for idx, (campaign_id, campaign_data) in enumerate(running_campaigns.items(), 1):
            print(f"{idx}. {campaign_data['name']} ({campaign_id})")

        choice = input("\nEnter campaign number to stop: ")
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(running_campaigns):
            print(f"{Fore.RED}Invalid choice!{Style.RESET_ALL}")
            return

        campaign_id = list(running_campaigns.keys())[int(choice) - 1]
        try:
            if campaign_id in self.running_campaigns:
                # Set campaign status to indicate it should stop
                self.active_campaigns[campaign_id]['status'] = Status.COMPLETED
                self._save_campaigns()
                print(f"{Fore.GREEN}Campaign stopped successfully!{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}Campaign is not currently running.{Style.RESET_ALL}")

        except Exception as e:
            self.logger.error(f"Error stopping campaign: {str(e)}")
            print(f"{Fore.RED}Error stopping campaign: {str(e)}{Style.RESET_ALL}")

    def delete_campaign(self):
        """Delete a campaign."""
        if not self.active_campaigns:
            print(f"{Fore.YELLOW}No campaigns found.{Style.RESET_ALL}")
            return

        print("\nAvailable campaigns:")
        for idx, (campaign_id, campaign_data) in enumerate(self.active_campaigns.items(), 1):
            print(f"{idx}. {campaign_data['name']} ({campaign_id})")

        choice = input("\nEnter campaign number to delete: ")
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(self.active_campaigns):
            print(f"{Fore.RED}Invalid choice!{Style.RESET_ALL}")
            return

        campaign_id = list(self.active_campaigns.keys())[int(choice) - 1]
        campaign_data = self.active_campaigns[campaign_id]

        if campaign_data['status'] == Status.IN_PROGRESS:
            print(f"{Fore.RED}Cannot delete a running campaign. Stop it first.{Style.RESET_ALL}")
            return

        confirm = input(f"{Fore.RED}Are you sure you want to delete this campaign? (yes/no): {Style.RESET_ALL}")
        if confirm.lower() != 'yes':
            return

        try:
            del self.active_campaigns[campaign_id]
            self._save_campaigns()
            print(f"{Fore.GREEN}Campaign deleted successfully!{Style.RESET_ALL}")

        except Exception as e:
            self.logger.error(f"Error deleting campaign: {str(e)}")
            print(f"{Fore.RED}Error deleting campaign: {str(e)}{Style.RESET_ALL}")

    def _process_campaign(self, campaign_id: str):
        """Process a campaign."""
        try:
            campaign = Campaign(**self.active_campaigns[campaign_id])
            self.logger.info(f"Starting campaign: {campaign_id}")
            
            template = self.message_manager.get_template(campaign.template_name)
            self.logger.info(f"Template loaded: {campaign.template_name}")
            
            recipients = self.recipient_manager.get_recipients_by_tags(campaign.recipient_tags)
            self.logger.info(f"Found {len(recipients)} recipients for tags: {campaign.recipient_tags}")

            if not template:
                self.logger.error(f"Template '{campaign.template_name}' not found")
                raise ValueError(f"Template '{campaign.template_name}' not found")

            if not recipients:
                self.logger.error(f"No recipients found for tags: {campaign.recipient_tags}")
                raise ValueError("No recipients found for specified tags")

            campaign.stats['total'] = len(recipients)
            campaign.stats['remaining'] = len(recipients)
            self.active_campaigns[campaign_id] = vars(campaign)
            self._save_campaigns()

            for recipient in recipients:
                if self.active_campaigns[campaign_id]['status'] != Status.IN_PROGRESS:  # Check current status
                    self.logger.info(f"Campaign {campaign_id} stopped by user")
                    break

                try:
                    self.logger.info(f"Sending email to: {recipient}")
                    self.rate_limiter.wait_for_slot()

                    # Extract username from recipient email
                    recipient_username = self.utils.extract_username(recipient)
                    
                    # Create a copy of template content and replace variables
                    content = template['content']
                    if '%username%' in content:
                        content = content.replace('%username%', recipient_username)
                    

                    smtp_account = campaign.smtp_accounts[campaign.current_smtp_index].copy()  # Make a copy to avoid modifying original
                    smtp_account['sender_name'] = template.get('sender_name', '')  # Add sender name from template
                    self.logger.info(f"Using SMTP account: {smtp_account['username']} with sender name: {smtp_account['sender_name']}")

                    campaign.current_smtp_index = (campaign.current_smtp_index + 1) % len(campaign.smtp_accounts)

                    # Send email and get detailed result
                    success = self.message_manager.send_email(
                        smtp_account,
                        recipient,
                        template['subject'],
                        content
                    )
                    
                    if success:
                        self.logger.info(f"Email sent successfully to {recipient}")
                        campaign.stats['sent'] += 1
                    else:
                        self.logger.error(f"Failed to send email to {recipient}")
                        campaign.stats['failed'] += 1
                        campaign.failed_recipients.append(recipient)

                except Exception as e:
                    self.logger.error(f"Error sending email to {recipient}: {str(e)}")
                    campaign.stats['failed'] += 1
                    campaign.failed_recipients.append(recipient)

                campaign.stats['remaining'] -= 1
                self.active_campaigns[campaign_id] = vars(campaign)
                self._save_campaigns()

            # Update final status
            campaign.status = Status.COMPLETED
            campaign.end_time = datetime.now().isoformat()
            self.active_campaigns[campaign_id] = vars(campaign)
            self._save_campaigns()
            self.logger.info(f"Campaign {campaign_id} completed. Stats: {campaign.stats}")

        except Exception as e:
            self.logger.error(f"Campaign processing error: {str(e)}")
            self.active_campaigns[campaign_id]['status'] = Status.FAILED
            self._save_campaigns()
    def restart_campaign(self):
        """Restart a completed campaign with option to change sender."""
        completed_campaigns = {
            k: v for k, v in self.active_campaigns.items()
            if v['status'] in [Status.COMPLETED, Status.FAILED]
        }

        if not completed_campaigns:
            print(f"{Fore.YELLOW}No completed or failed campaigns found.{Style.RESET_ALL}")
            return

        print("\nCompleted/Failed campaigns:")
        for idx, (campaign_id, campaign_data) in enumerate(completed_campaigns.items(), 1):
            status_color = Fore.GREEN if campaign_data['status'] == Status.COMPLETED else Fore.RED
            print(f"{idx}. {campaign_data['name']} ({campaign_id}) - Status: {status_color}{campaign_data['status']}{Style.RESET_ALL}")
            print(f"   Stats: {campaign_data['stats']}")

        choice = input("\nEnter campaign number to restart: ")
        if not choice.isdigit() or int(choice) < 1 or int(choice) > len(completed_campaigns):
            print(f"{Fore.RED}Invalid choice!{Style.RESET_ALL}")
            return

        try:
            campaign_id = list(completed_campaigns.keys())[int(choice) - 1]
            campaign_data = completed_campaigns[campaign_id]

            # Option to change SMTP accounts
            print("\nCurrent SMTP accounts:")
            for idx, account in enumerate(campaign_data['smtp_accounts'], 1):
                print(f"{idx}. {account['username']} ({account['host']})")

            change_smtp = input("\nDo you want to change SMTP accounts? (yes/no): ").lower()
            if change_smtp == 'yes':
                # Get SMTP accounts
                smtp_accounts = self.smtp_manager.get_verified_accounts()
                if not smtp_accounts:
                    print(f"{Fore.RED}No verified SMTP accounts available.{Style.RESET_ALL}")
                    return

                # Display SMTP account selection
                print("\nAvailable SMTP accounts:")
                for idx, account in enumerate(smtp_accounts, 1):
                    print(f"{idx}. {account['username']} ({account['host']})")
                print(f"{len(smtp_accounts) + 1}. Use all accounts")

                smtp_choice = input("\nSelect SMTP account number: ")
                if not smtp_choice.isdigit() or int(smtp_choice) < 1 or int(smtp_choice) > len(smtp_accounts) + 1:
                    print(f"{Fore.RED}Invalid SMTP account choice!{Style.RESET_ALL}")
                    return

                # Set selected SMTP accounts
                if int(smtp_choice) == len(smtp_accounts) + 1:
                    campaign_data['smtp_accounts'] = smtp_accounts
                    print(f"{Fore.GREEN}Selected all SMTP accounts{Style.RESET_ALL}")
                else:
                    campaign_data['smtp_accounts'] = [smtp_accounts[int(smtp_choice) - 1]]
                    print(f"{Fore.GREEN}Selected SMTP account: {campaign_data['smtp_accounts'][0]['username']}{Style.RESET_ALL}")

            # Reset campaign stats and status
            campaign_data['status'] = Status.PENDING
            campaign_data['stats'] = {
                'total': 0,
                'sent': 0,
                'failed': 0,
                'remaining': 0
            }
            campaign_data['start_time'] = None
            campaign_data['end_time'] = None
            campaign_data['current_smtp_index'] = 0
            campaign_data['failed_recipients'] = []

            # Update campaign
            self.active_campaigns[campaign_id] = campaign_data
            self._save_campaigns()

            print(f"\n{Fore.GREEN}Campaign reset successfully! You can now start it again.{Style.RESET_ALL}")
            
            # Option to start immediately
            start_now = input("\nDo you want to start the campaign now? (yes/no): ").lower()
            if start_now == 'yes':
                self.active_campaigns[campaign_id]['status'] = Status.IN_PROGRESS
                self.active_campaigns[campaign_id]['start_time'] = datetime.now().isoformat()
                self._save_campaigns()

                # Start campaign in a new thread
                campaign_thread = threading.Thread(
                    target=self._process_campaign,
                    args=(campaign_id,),
                    daemon=True
                )
                campaign_thread.start()
                self.running_campaigns[campaign_id] = campaign_thread
                print(f"{Fore.GREEN}Campaign started successfully!{Style.RESET_ALL}")

        except Exception as e:
            self.logger.error(f"Error restarting campaign: {str(e)}")
            print(f"{Fore.RED}Error restarting campaign: {str(e)}{Style.RESET_ALL}")