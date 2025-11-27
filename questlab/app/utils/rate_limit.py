"""Lightweight in-memory rate limiting helpers.

This avoids external dependencies while still enforcing basic limits
for login/registration/upload routes.  It is suitable for single-node
development and small deployments; for production a shared store
like Redis should be used.
"""

import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

# Store timestamps per key
_buckets: Dict[str, Deque[float]] = defaultdict(deque)


def _prune(bucket: Deque[float], window: int, now: float) -> None:
    """Remove entries older than the window."""
    while bucket and bucket[0] < now - window:
        bucket.popleft()


def check_rate_limit(key: str, limit: int, window: int) -> bool:
    """Return True if the action is allowed, False if rate limited."""
    now = time.time()
    bucket = _buckets[key]
    _prune(bucket, window, now)
    if len(bucket) >= limit:
        return False
    bucket.append(now)
    return True


def remaining(key: str, limit: int, window: int) -> int:
    """Return the number of remaining attempts in the window."""
    now = time.time()
    bucket = _buckets[key]
    _prune(bucket, window, now)
    return max(0, limit - len(bucket))


def record_failure(key: str, window: int) -> int:
    """Record a failure for alerting; returns count in current window."""
    now = time.time()
    bucket = _buckets[key]
    _prune(bucket, window, now)
    bucket.append(now)
    return len(bucket)
