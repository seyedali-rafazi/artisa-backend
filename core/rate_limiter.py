"""In-memory sliding window rate limiter dependency for FastAPI endpoints."""

import time
from collections import defaultdict
from typing import Dict, List, Optional
from fastapi import HTTPException, Request, status


class SlidingWindowRateLimiter:
    """Thread-safe sliding window rate limiter per client IP address.

    Attributes:
        max_requests: Maximum allowed requests within the time window.
        window_seconds: Duration of the sliding window in seconds.
        prefix: Unique identifier prefix for this limiter instance.
    """

    def __init__(self, max_requests: int, window_seconds: int, prefix: str = "rate_limit"):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.prefix = prefix
        self._records: Dict[str, List[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request or forwarded headers."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # First IP in X-Forwarded-For is client
            return forwarded_for.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "127.0.0.1"

    def _cleanup_old_records(self, key: str, now: float) -> List[float]:
        """Prune timestamps older than current window."""
        cutoff = now - self.window_seconds
        valid = [ts for ts in self._records[key] if ts > cutoff]
        self._records[key] = valid
        return valid

    async def __call__(self, request: Request):
        """FastAPI dependency entrypoint."""
        ip = self._get_client_ip(request)
        key = f"{self.prefix}:{ip}"
        now = time.time()

        timestamps = self._cleanup_old_records(key, now)

        if len(timestamps) >= self.max_requests:
            oldest = timestamps[0]
            retry_after = max(1, int(self.window_seconds - (now - oldest)))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"تعداد درخواست‌ها بیش از حد مجاز است. لطفاً {retry_after} ثانیه دیگر مجدداً تلاش کنید.",
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(now + retry_after)),
                },
            )

        # Record this request
        self._records[key].append(now)


# Pre-configured rate limiters for common auth routes
login_rate_limiter = SlidingWindowRateLimiter(
    max_requests=10, window_seconds=300, prefix="login"
)
refresh_rate_limiter = SlidingWindowRateLimiter(
    max_requests=30, window_seconds=60, prefix="refresh"
)
auth_general_rate_limiter = SlidingWindowRateLimiter(
    max_requests=20, window_seconds=60, prefix="auth_general"
)
