import time
from collections import defaultdict
from fastapi import Request, HTTPException


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    client = request.client
    return client.host if client else "unknown"


class TokenBucket:
    def __init__(self, rate: int, per_seconds: int):
        self.rate = rate
        self.per_seconds = per_seconds
        self.tokens = rate
        self.last_refill = time.monotonic()

    def consume(self, tokens: int = 1) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(
            self.rate, self.tokens + elapsed * (self.rate / self.per_seconds)
        )
        self.last_refill = now
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


class InMemoryRateLimiter:
    def __init__(self, rate_str: str = "20/minute"):
        count, window = rate_str.split("/")
        self.rate = int(count)
        self.per_seconds = {
            "second": 1, "minute": 60, "hour": 3600
        }[window]
        self.buckets: dict[str, TokenBucket] = {}

    def is_rate_limited(self, key: str) -> bool:
        bucket = self.buckets.get(key)
        if bucket is None:
            bucket = TokenBucket(self.rate, self.per_seconds)
            self.buckets[key] = bucket
        return not bucket.consume()

    def check(self, key: str):
        if self.is_rate_limited(key):
            raise HTTPException(
                status_code=429, detail="Too many requests. Please wait."
            )


def create_rate_limiter(rate: str = "20/minute") -> InMemoryRateLimiter:
    return InMemoryRateLimiter(rate)
