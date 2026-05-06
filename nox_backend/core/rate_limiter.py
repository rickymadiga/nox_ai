import time
from collections import defaultdict

class RateLimiter:
    def __init__(self):
        self.storage = defaultdict(list)

    def is_allowed(self, key: str, limit: int, window: int):
        now = time.time()

        # remove old requests
        self.storage[key] = [
            t for t in self.storage[key] if now - t < window
        ]

        if len(self.storage[key]) >= limit:
            return False

        self.storage[key].append(now)
        return True

rate_limiter = RateLimiter()