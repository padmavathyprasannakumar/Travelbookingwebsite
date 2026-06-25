"""
Django settings for travel_booking_site project.
Render deployment ready.
"""

import os
from pathlib import Path

import dj_database_url


# --------------------------------------------------
# Base directory
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent


# --------------------------------------------------
# Helper functions
# --------------------------------------------------

def env_bool(name, default=False):
    value = os.environ.get(name)

    if value is None:
        return default

    return value.strip().lower() in ("1", "true", "yes", "on")


def env_list(name, default=""):
    value = os.environ.get(name, default)

    if not value:
        return []

    return [item.strip() for item in value.split(",") if item.strip()]


# --------------------------------------------------
# Security
# --------------------------------------------------

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-)btjd$)a2ix%l_kyncae%h52b8ewz#dj1*-0@t+z)lc@1_x8%a"
)

DEBUG = env_bool("DJANGO_DEBUG", False)

ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    "127.0.0.1,localhost,.onrender.com"
)

CSRF_TRUSTED_ORIGINS = env_list(
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "https://*.onrender.com"
)


# --------------------------------------------------
# Application definition
# --------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Local app
    "booking",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    # WhiteNoise for static files on Render
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "travel_booking_site.urls"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",

                # Global site/footer data
                "booking.context_processors.global_site_data",
            ],
        },
    },
]


WSGI_APPLICATION = "travel_booking_site.wsgi.application"


# --------------------------------------------------
# Database
# --------------------------------------------------
# Local: SQLite
# Render: PostgreSQL using DATABASE_URL

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}


# --------------------------------------------------
# Password validation
# --------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# --------------------------------------------------
# Internationalization
# --------------------------------------------------

LANGUAGE_CODE = "en-us"

TIME_ZONE = os.environ.get("DJANGO_TIME_ZONE", "Asia/Kolkata")

USE_I18N = True

USE_TZ = True


# --------------------------------------------------
# Static files
# --------------------------------------------------

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = []

ROOT_STATIC_DIR = BASE_DIR / "static"

if ROOT_STATIC_DIR.exists():
    STATICFILES_DIRS.append(ROOT_STATIC_DIR)

# Django 6 compatible staticfiles storage setting
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# --------------------------------------------------
# Media files
# --------------------------------------------------

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# --------------------------------------------------
# Login / logout redirects
# --------------------------------------------------

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "home"


# --------------------------------------------------
# Default primary key field type
# --------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --------------------------------------------------
# Cashfree Payment Gateway
# --------------------------------------------------
# Do not hardcode Cashfree secret keys here.
# Add keys in Render Environment Variables.

CASHFREE_CLIENT_ID = os.environ.get("CASHFREE_CLIENT_ID", "")
CASHFREE_CLIENT_SECRET = os.environ.get("CASHFREE_CLIENT_SECRET", "")
CASHFREE_ENVIRONMENT = os.environ.get("CASHFREE_ENVIRONMENT", "sandbox").lower()
CASHFREE_API_VERSION = os.environ.get("CASHFREE_API_VERSION", "2025-01-01")
CASHFREE_ORDER_CURRENCY = os.environ.get("CASHFREE_ORDER_CURRENCY", "INR")

CASHFREE_DEFAULT_CUSTOMER_PHONE = os.environ.get(
    "CASHFREE_DEFAULT_CUSTOMER_PHONE",
    "9999999999"
)

CASHFREE_DEFAULT_CUSTOMER_EMAIL = os.environ.get(
    "CASHFREE_DEFAULT_CUSTOMER_EMAIL",
    "customer@example.com"
)


# --------------------------------------------------
# Production security for Render
# --------------------------------------------------

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"