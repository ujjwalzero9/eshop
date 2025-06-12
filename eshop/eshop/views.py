import sentry_sdk
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def sentry_test(request):
    # 1) log a breadcrumb (optional)
    sentry_sdk.add_breadcrumb(
        category="test",
        message="Sentry test endpoint hit",
        level="info",
    )

    # 2) raise an exception
    try:
        1 / 0
    except ZeroDivisionError as e:
        # capture it explicitly
        sentry_sdk.capture_exception(e)
        # re-raise so DRF returns a 500
        raise

    return Response({"detail": "This should never run"})
