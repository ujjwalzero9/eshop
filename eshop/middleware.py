# eshop/middleware.py

import time
import logging

logger = logging.getLogger("eshop.services.product_service")

class RequestTimingMiddleware:
    """
    Logs each request’s method, path, status and duration,
    but skips the Prometheus /metrics endpoint.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Don’t log Prometheus scrapes
        if request.path.startswith("/metrics"):
            return self.get_response(request)

        start = time.monotonic()
        response = self.get_response(request)
        elapsed = time.monotonic() - start

        logger.info(
            "HTTP %s %s → %s (%.3f s)",
            request.method,
            request.get_full_path(),
            response.status_code,
            elapsed,
        )
        return response
