import time
from collections import deque
from typing import Deque, Dict


class SlidingWindowLimiter:
    def __init__(self, max_events: int, window_seconds: int) -> None:
        self.max_events = max_events
        self.window_seconds = window_seconds
        self._buckets: Dict[str, Deque[float]] = {}

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        dq = self._buckets.setdefault(key, deque())
        # Drop old events
        cutoff = now - self.window_seconds
        while dq and dq[0] < cutoff:
            dq.popleft()
        if len(dq) >= self.max_events:
            return False
        dq.append(now)
        return True


import os

# Get rate limiting config from environment
_max_attempts = int(os.getenv("LOGIN_MAX_ATTEMPTS", "5"))
_window_seconds = int(os.getenv("LOGIN_WINDOW_SECONDS", "60"))

login_limiter = SlidingWindowLimiter(max_events=_max_attempts, window_seconds=_window_seconds)


