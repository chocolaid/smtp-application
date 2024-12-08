from datetime import datetime
from typing import Dict, List, Optional

from src.config.constants import Status

class Campaign:
    def __init__(self, 
                 name: str,
                 template_name: str,
                 recipient_tags: List[str],
                 smtp_accounts: List[Dict],
                 schedule_time: Optional[datetime] = None,
                 id: str = None,
                 status: str = Status.PENDING,
                 stats: Dict = None,
                 failed_recipients: List = None,
                 current_smtp_index: int = 0,
                 start_time: str = None,
                 end_time: str = None,
                 created_at: str = None,
                 updated_at: str = None):
        
        self.id = id or datetime.now().strftime('%Y%m%d_%H%M%S')
        self.name = name
        self.template_name = template_name
        self.recipient_tags = recipient_tags
        self.smtp_accounts = smtp_accounts
        self.schedule_time = schedule_time
        self.status = status
        
        self.stats = stats or {'total': 0, 'sent': 0, 'failed': 0, 'remaining': 0}
        self.failed_recipients = failed_recipients or []
        self.current_smtp_index = current_smtp_index
        self.start_time = start_time
        self.end_time = end_time
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()

    def update_status(self, new_status: str):
        """Update campaign status and updated_at timestamp."""
        if new_status not in [Status.PENDING, Status.IN_PROGRESS, Status.COMPLETED, Status.FAILED]:
            raise ValueError(f"Invalid status: {new_status}")
        
        self.status = new_status
        self.updated_at = datetime.now().isoformat()
        
        if new_status == Status.IN_PROGRESS and not self.start_time:
            self.start_time = datetime.now().isoformat()
        elif new_status in [Status.COMPLETED, Status.FAILED] and not self.end_time:
            self.end_time = datetime.now().isoformat()

    def update_stats(self, sent: bool = True):
        """Update campaign statistics."""
        if sent:
            self.stats['sent'] += 1
        else:
            self.stats['failed'] += 1
        self.stats['remaining'] -= 1
        self.updated_at = datetime.now().isoformat()

    def add_failed_recipient(self, recipient: str):
        """Add a recipient to the failed recipients list."""
        if recipient not in self.failed_recipients:
            self.failed_recipients.append(recipient)
            self.updated_at = datetime.now().isoformat()

    def rotate_smtp_account(self) -> int:
        """Rotate to the next SMTP account and return its index."""
        self.current_smtp_index = (self.current_smtp_index + 1) % len(self.smtp_accounts)
        self.updated_at = datetime.now().isoformat()
        return self.current_smtp_index

    def get_progress(self) -> float:
        """Calculate campaign progress percentage."""
        if self.stats['total'] == 0:
            return 0.0
        return round((self.stats['sent'] + self.stats['failed']) / self.stats['total'] * 100, 2)

    def is_scheduled(self) -> bool:
        """Check if campaign is scheduled for future execution."""
        return bool(self.schedule_time and datetime.fromisoformat(self.schedule_time) > datetime.now())

    def can_start(self) -> bool:
        """Check if campaign can be started."""
        if self.status != Status.PENDING:
            return False
        if self.is_scheduled():
            return False
        return True

    def to_dict(self) -> Dict:
        """Convert campaign to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'template_name': self.template_name,
            'recipient_tags': self.recipient_tags,
            'smtp_accounts': self.smtp_accounts,
            'schedule_time': self.schedule_time,
            'status': self.status,
            'stats': self.stats,
            'failed_recipients': self.failed_recipients,
            'current_smtp_index': self.current_smtp_index,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Campaign':
        """Create campaign instance from dictionary."""
        return cls(**data)

    def __str__(self) -> str:
        """String representation of campaign."""
        return (
            f"Campaign: {self.name}\n"
            f"Status: {self.status}\n"
            f"Progress: {self.get_progress()}%\n"
            f"Stats: {self.stats}"
        )