import os
from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

# ─── Load Environment ────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

def get_env_var(name):
    val = os.getenv(name)
    if not val:
        raise ImproperlyConfigured(f"Missing required environment variable: {name}")
    return val

# ─── Ensure logs directory exists ─────────────────────────────────────────
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

print(f"[DEBUG] Log directory is: {LOG_DIR}")
print(f"[DEBUG] Log file will be: {os.path.join(LOG_DIR, 'product_service.log')}")

# ─── Django Core ─────────────────────────────────────────────────────────
SECRET_KEY = get_env_var("DJANGO_SECRET_KEY")
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost").split(",")

# ─── Installed Apps ─────────────────────────────────────────────────────
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "products",
]

# ─── Middleware ─────────────────────────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "eshop.middleware.RequestTimingMiddleware",
]

# ─── URLs & App Config ──────────────────────────────────────────────────
ROOT_URLCONF = "eshop.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "eshop.wsgi.application"
ASGI_APPLICATION = "eshop.asgi.application"

# ─── Database: PostgreSQL (AWS RDS) ──────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": get_env_var("POSTGRES_DB"),
        "USER": get_env_var("POSTGRES_USER"),
        "PASSWORD": get_env_var("POSTGRES_PASSWORD"),
        "HOST": get_env_var("POSTGRES_HOST"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 600,
        "OPTIONS": {
            "sslmode": os.getenv("POSTGRES_SSLMODE", "require")
        },
    }
}

# ─── Redis: Upstash Direct (used manually, not via CACHES) ──────────────
REDIS_URL = get_env_var("REDIS_URL")
REDIS_READ_URL = get_env_var("REDIS_URL")
REDIS_WRITE_URL = get_env_var("REDIS_URL")
# ─── Password Validation ────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

from decouple import config, Csv
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# ─── Sentry Configuration ────────────────────────────────────────────────────
sentry_sdk.init(
    dsn=config('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=config('SENTRY_TRACES_SAMPLE_RATE', default=0.0, cast=float),
    environment=config('ENVIRONMENT', default='development'),
    release=config('RELEASE', default=None),
    send_default_pii=True,
)

# ─── Logging Configuration ─────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": os.path.join(LOG_DIR, "product_service.log"),
            "formatter": "verbose",
            "level": "INFO",
        },
    },
    "loggers": {
        "eshop.services.product_service": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# ─── Internationalization ───────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ─── Static Files ───────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# ─── Default Primary Key Field ──────────────────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
