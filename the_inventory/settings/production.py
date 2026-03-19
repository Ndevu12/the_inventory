import os
import dj_database_url

from .base import *  # noqa: F403,F401

DEBUG = False

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

CACHES = {  # noqa: F405
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

try:
    from .local import *  # noqa: F403,F401
except ImportError:
    pass
