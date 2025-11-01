"""
Production Django settings.

- Import everything from base.
- Apply stricter security defaults for production.
- Configure Redis caching + session backend (django-redis).
- Configure static/media roots to match docker-compose volumes (/vol/*).
- Read Stripe keys and other secrets from environment.
"""

from .base import *  # noqa: E402,F401
import os

# -------------------------
# Basic flags
# -------------------------
DEBUG = False

# ALLOWED_HOSTS: prefer the env value; fall back to localhost for local docker dev.
# Example .env: ALLOWED_HOSTS=example.com,api.example.com
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# -------------------------
# Security-related settings
# -------------------------
# When serving behind a reverse proxy (nginx) that terminates TLS:
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Cookies
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=True)
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=True)

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=3600)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True)
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=True)

# Redirect HTTP to HTTPS (set False for local non-TLS debugging)
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)

# -------------------------
# Static & media (Docker volumes)
# -------------------------
# In docker-compose we mount static_volume:/vol/static and media_volume:/vol/media
STATIC_ROOT = env("STATIC_ROOT", default=os.getenv("STATIC_ROOT", "/vol/static"))
MEDIA_ROOT = env("MEDIA_ROOT", default=os.getenv("MEDIA_ROOT", "/vol/media"))
# STATIC_URL defined in base.py already; MEDIA_URL can be set via env or default:
MEDIA_URL = env("MEDIA_URL", default="/media/")

# -------------------------
# Redis caching & sessions
# -------------------------
# Make sure django-redis is in requirements.txt (django-redis>=6)
REDIS_HOST = env("REDIS_HOST", default="redis")
REDIS_PORT = env.int("REDIS_PORT", default=6379)
REDIS_DB_CACHE = env.int("REDIS_DB_CACHE", default=1)
REDIS_DB_RATELIMIT = env.int("REDIS_DB_RATELIMIT", default=2)

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB_CACHE}",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            # You can enable compression and other options here
        },
    }
}

# Use cache-backed sessions for faster session reads/writes (optional)
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

# -------------------------
# Stripe & external service keys
# -------------------------
# These should be set in the runtime environment / .env (do NOT commit real keys)
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default=None)
STRIPE_PUBLISHABLE_KEY = env("STRIPE_PUBLISHABLE_KEY", default=None)
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default=None)

# Optional: quick warning during startup if keys missing (won't crash import)
if not STRIPE_SECRET_KEY:
    # Only import logging if settings initialization expects it
    import logging as _logging
    _logging.getLogger("ecom.settings.prod").warning(
        "STRIPE_SECRET_KEY not configured. Payment endpoints will fail until provided."
    )

# -------------------------
# Database: defer to base DATABASE_URL or env; leave default SQLite if none
# -------------------------
# (The base settings already handle DATABASE_URL if provided).
# If you want to enforce Postgres in production, set DATABASE_URL in env:
# DATABASE_URL=postgres://user:pass@postgres:5432/dbname

# -------------------------
# Logging: keep base logging but raise root log level if requested
# -------------------------
LOG_LEVEL = env("LOG_LEVEL", default="INFO").upper()
LOGGING["root"]["level"] = LOG_LEVEL

# Slightly more verbose gunicorn/django request logs in prod
LOGGING.setdefault("loggers", {})
LOGGING["loggers"].setdefault("django.request", {"handlers": ["console"], "level": "INFO", "propagate": False})
LOGGING["loggers"].setdefault("gunicorn.error", {"handlers": ["console"], "level": "INFO", "propagate": False})
LOGGING["loggers"].setdefault("gunicorn.access", {"handlers": ["console"], "level": "INFO", "propagate": False})

# -------------------------
# Other production niceties (optional)
# -------------------------
# Allow larger uploads behind proxy if needed (nginx should also be configured)
DATA_UPLOAD_MAX_MEMORY_SIZE = env.int("DATA_UPLOAD_MAX_MEMORY_SIZE", default=52428800)  # 50 MB

# -------------------------
# End of production settings
# -------------------------
