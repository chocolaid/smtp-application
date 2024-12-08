import time
from collections import deque
from datetime import datetime, timedelta
from threading import Lock

class RateLimiter:
    def __init__(self, max_requests, time_window):
        self.max_requests = max_requests
        self.time_window = time_window  # in seconds
        self.requests = deque()
        self.lock = Lock()

    def can_proceed(self):
        with self.lock:
            now = datetime.now()
            
            # Remove old requests
            while self.requests and (now - self.requests[0]) > timedelta(seconds=self.time_window):
                self.requests.popleft()

            # Check if we can proceed
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
                
            return False

    def wait_for_slot(self):
        while not self.can_proceed():
            time.sleep(1)