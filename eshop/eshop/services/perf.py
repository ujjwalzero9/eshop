# eshop/services/perf.py

import time
import logging
from django.db import connection

logger = logging.getLogger("eshop.services.product_service")

# If you want basic DB-query counting (only in DEBUG mode)
def get_db_query_count():
    # Make sure DEBUG = True in settings for this to work
    return len(connection.queries)

# eshop/services/perf.py  (modify existing log_timing)

from .metrics import PRODUCT_CACHE, PRODUCT_LATENCY

def log_timing(func):
    def wrapper(*args, **kwargs):
        start = time.monotonic()
        data, cache_hit = func(*args, **kwargs)
        elapsed = time.monotonic() - start

        # Logging as before...
        logger.info(
            "%s elapsed=%.4fs cache_hit=%s",
            func.__name__, elapsed, cache_hit,
        )

        # Prometheus
        labels = {"method": func.__name__, "cache_hit": str(cache_hit)}
        PRODUCT_CACHE.labels(**labels).inc()
        PRODUCT_LATENCY.labels(**labels).observe(elapsed)

        return data, cache_hit
    return wrapper

