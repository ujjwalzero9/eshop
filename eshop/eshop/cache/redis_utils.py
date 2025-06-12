import json
import uuid
import redis
import decimal
import threading
import functools
import logging

from django.conf import settings
from redis.exceptions import ConnectionError, TimeoutError

"""
Redis utility module: provides a singleton Redis client,
JSON encoding for UUID and Decimal, and safe cache operations
with automatic exception handling.
"""

try:
    from rediscluster.exceptions import ClusterError, MovedError
    RedisDownExceptions = (ConnectionError, TimeoutError, ClusterError, MovedError)
except ImportError:
    RedisDownExceptions = (ConnectionError, TimeoutError)

_lock = threading.Lock()


class SingletonRedisClient:
    """Singleton pattern for Redis client initialization."""
    _instances = {}

    def __new__(cls, mode="read"):  
        """Instantiate or return existing Redis client for given mode."""
        with _lock:
            if mode not in cls._instances:
                instance = super(SingletonRedisClient, cls).__new__(cls)
                instance.init_client(mode)
                cls._instances[mode] = instance
            return cls._instances[mode]

    def init_client(self, mode):
        """Initialize Redis client using read or write URL from settings."""
        redis_url = settings.REDIS_READ_URL if mode == "read" else settings.REDIS_WRITE_URL
        self.client = redis.StrictRedis.from_url(redis_url, decode_responses=True)

    def get_client(self):
        """Retrieve the underlying Redis client instance."""
        if not hasattr(self, "client"):
            raise AttributeError("Redis client not initialized.")
        return self.client


class EnhancedJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder handling UUID and Decimal serialization."""
    def default(self, obj):
        """Convert UUID to str and Decimal to float."""
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super().default(obj)


def log_redis_exceptions(logging_data, exception):
    """Log Redis connection or timeout exceptions without raising."""
    logging.warning(f"[Redis Exception] {logging_data['p']}: {logging_data['e']}")


def redis_except(return_val=None):
    """Decorator to catch Redis-related errors and return a safe default."""
    if callable(return_val):
        return redis_except()(return_val)

    def decorator(func):
        """Wrap function to handle RedisDownExceptions gracefully."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """Execute function and catch Redis errors."""
            try:
                return func(*args, **kwargs)
            except RedisDownExceptions as e:
                log_redis_exceptions({
                    "p": func.__name__,
                    "e": str(e)
                }, e)
                return return_val
        return wrapper
    return decorator


@redis_except(return_val=None)
def get_cached(key):
    """Retrieve JSON-deserialized value from Redis for the given key."""
    client = SingletonRedisClient("read").get_client()
    data = client.get(key)
    return json.loads(data) if data else None


@redis_except(return_val=False)
def set_cached(key, value, ex=None):
    """Store a JSON-serializable value in Redis with optional expiry."""
    client = SingletonRedisClient("write").get_client()
    return client.set(key, json.dumps(value, cls=EnhancedJSONEncoder), ex=ex)


@redis_except(return_val=0)
def invalidate(key_pattern):
    """Delete all Redis keys matching the given pattern and return deletion count."""
    client = SingletonRedisClient("write").get_client()
    deleted_count = 0
    for key in client.scan_iter(key_pattern):
        client.delete(key)
        deleted_count += 1
    return deleted_count
