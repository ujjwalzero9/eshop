# eshop/services/metrics.py

from prometheus_client import Counter, Histogram

# Counter for cache hits/misses
PRODUCT_CACHE = Counter(
    "eshop_product_cache_requests_total",
    "Total product service calls, labeled by method and cache_hit",
    ["method", "cache_hit"],
)

# Histogram for timings
PRODUCT_LATENCY = Histogram(
    "eshop_product_latency_seconds",
    "Latency of product service calls, labeled by method and cache_hit",
    ["method", "cache_hit"],
)
