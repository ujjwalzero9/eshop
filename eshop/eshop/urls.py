# project/urls.py

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from .views import sentry_test

from prometheus_client import make_wsgi_app
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

@csrf_exempt
@require_GET
def metrics_view(request):
    """
    Expose Prometheus metrics at /metrics/ in plain text,
    regardless of any Accept-Encoding the client sends.
    """
    # Copy the WSGI environ so we don't mutate the real one
    environ = request.META.copy()
    # Remove any Accept-Encoding header so prometheus_client won’t gzip
    environ.pop('HTTP_ACCEPT_ENCODING', None)

    # Prepare our dummy start_response
    def start_response(status, headers, exc_info=None):
        # We’re going to let Django manage headers, so no-op
        pass

    # Call the Prometheus WSGI app
    wsgi_app = make_wsgi_app()
    output = wsgi_app(environ, start_response)

    # Join the iterable into a single bytes object
    body = b''.join(output)

    return HttpResponse(
        body,
        content_type='text/plain; version=0.0.4; charset=utf-8',
        status=200
    )

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('products.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('sentry-test/', sentry_test, name='sentry_test'),

    # Prometheus scrape endpoint (plain text)
    path('metrics/', metrics_view),
]
