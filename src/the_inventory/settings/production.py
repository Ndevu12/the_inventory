import os

import dj_database_url

from .base import *  # noqa: F403,F401
from .env_utils import env_bool, env_str

DEBUG = False

# Console logging for PaaS (Render, Fly, etc.): Gunicorn already streams access/error logs;
# this sends Django/Wagtail log records to the same process stdout/stderr stream.
_lvl = env_str("DJANGO_LOG_LEVEL", "INFO").upper()
if _lvl not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
    _lvl = "INFO"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "production": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "production",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": _lvl,
    },
    "loggers": {
        # 4xx/5xx and suspicious requests (visible at WARNING+)
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}


def _normalize_allowed_host(raw: str) -> str:
    """ALLOWED_HOSTS must be host[:port] only — no scheme or path (common env mistake)."""
    h = raw.strip()
    if not h:
        return ""
    lower = h.lower()
    for prefix in ("https://", "http://"):
        if lower.startswith(prefix):
            h = h[len(prefix) :]
            lower = h.lower()
            break
    if "/" in h:
        h = h.split("/", 1)[0]
    return h.strip()


# ALLOWED_HOSTS — explicit hostnames for every public URL (and leading-dot suffixes, e.g. .example.com).
# Normalize strips accidental https:// and paths from env. No platform-specific entries here:
# set ALLOWED_HOSTS in your orchestration (K8s, PaaS, systemd) for each environment.
# See https://docs.djangoproject.com/en/stable/ref/settings/#allowed-hosts
_default_allowed_hosts = [
    "localhost",
    "127.0.0.1",
]
_env_allowed = (os.environ.get("ALLOWED_HOSTS") or "").strip()
_raw_hosts = (
    [x.strip() for x in _env_allowed.split(",") if x.strip()]
    if _env_allowed
    else list(_default_allowed_hosts)
)
ALLOWED_HOSTS = []
_seen_hosts: set[str] = set()
for item in _raw_hosts:
    host = _normalize_allowed_host(item)
    if host and host not in _seen_hosts:
        _seen_hosts.add(host)
        ALLOWED_HOSTS.append(host)

# SECRET_KEY must be set in production
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError(
        "The SECRET_KEY environment variable is not set. "
        "This is required for production deployments."
    )

# Database - Use PostgreSQL in production via DATABASE_URL environment variable
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    DATABASES["default"] = dj_database_url.config(  # noqa: F405
        default=DATABASE_URL,
        conn_max_age=600,
        conn_health_checks=True,
    )

# ManifestStaticFilesStorage is recommended in production, to prevent
# outdated JavaScript / CSS assets being served from cache
# (e.g. after a Wagtail upgrade).
# See https://docs.djangoproject.com/en/6.0/ref/contrib/staticfiles/#manifeststaticfilesstorage
STORAGES["staticfiles"]["BACKEND"] = "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"  # noqa: F405

# Wagtail uses the default cache for site root paths on every page request. If Redis
# is not configured, use LocMem (single-process only). Only enable django-redis when REDIS_URL is set.
_redis_url = (os.environ.get("REDIS_URL") or "").strip()
if _redis_url:
    CACHES = {  # noqa: F405
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": _redis_url,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
        }
    }
else:
    CACHES = {  # noqa: F405
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "the-inventory-production",
        }
    }

# TLS is usually terminated at a load balancer / ingress / PaaS edge. Trust X-Forwarded-Proto
# unless you terminate TLS on the app process (set USE_X_FORWARDED_PROTO=false).
if env_bool("USE_X_FORWARDED_PROTO", True):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# JWT cookies should be secure by default in production.
JWT_COOKIE_SECURE = env_bool("JWT_COOKIE_SECURE", True)

try:
    from .local import *  # noqa: F403,F401
except ImportError:
    pass
