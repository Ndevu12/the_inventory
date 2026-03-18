"""Stock-record caching with smart invalidation.

Provides a thin facade over Django's cache framework with:

* Tenant-aware cache keys:  ``stock:{tenant_id}:{product_id}:{location_id}``
* Hit/miss logging at DEBUG level
* Bulk-invalidation helpers used by :class:`StockService` and
  :class:`ReservationService`
* Dashboard summary caching with a separate TTL
* Graceful degradation — any cache backend (LocMem, Redis, Dummy) works

All public functions are module-level so they can be called without
instantiating a class.
"""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from django.core.cache import cache

from tenants.context import get_current_tenant

logger = logging.getLogger(__name__)

STOCK_RECORD_PREFIX = "stock"
DASHBOARD_PREFIX = "dashboard"


def _tenant_id() -> str:
    tenant = get_current_tenant()
    return str(tenant.pk) if tenant else "0"


# ------------------------------------------------------------------
# Key builders
# ------------------------------------------------------------------

def stock_record_key(product_id: int, location_id: int) -> str:
    """Build ``stock:{tenant}:{product}:{location}``."""
    return f"{STOCK_RECORD_PREFIX}:{_tenant_id()}:{product_id}:{location_id}"


def stock_product_pattern(product_id: int) -> str:
    """Prefix for all locations of a given product within the current tenant."""
    return f"{STOCK_RECORD_PREFIX}:{_tenant_id()}:{product_id}:"


def dashboard_key(name: str) -> str:
    return f"{DASHBOARD_PREFIX}:{_tenant_id()}:{name}"


# ------------------------------------------------------------------
# Get / set with logging
# ------------------------------------------------------------------

def _ttl(kind: str = "stock") -> int:
    if kind == "dashboard":
        return getattr(settings, "DASHBOARD_CACHE_TTL", 300)
    return getattr(settings, "STOCK_CACHE_TTL", 600)


def cache_get(key: str) -> Any | None:
    """Fetch from cache, logging hit/miss."""
    value = cache.get(key)
    if value is not None:
        logger.debug("Cache HIT: %s", key)
    else:
        logger.debug("Cache MISS: %s", key)
    return value


def cache_set(key: str, value: Any, kind: str = "stock") -> None:
    cache.set(key, value, timeout=_ttl(kind))
    logger.debug("Cache SET: %s (ttl=%ds)", key, _ttl(kind))


# ------------------------------------------------------------------
# Invalidation helpers
# ------------------------------------------------------------------

def invalidate_stock_record(product_id: int, location_id: int) -> None:
    """Delete a single stock-record cache entry."""
    key = stock_record_key(product_id, location_id)
    cache.delete(key)
    logger.debug("Cache INVALIDATE: %s", key)


def invalidate_product_stock(product_id: int, location_ids: list[int] | None = None) -> None:
    """Invalidate stock-record caches for a product.

    If *location_ids* are given, only those keys are deleted;
    otherwise a ``delete_pattern`` is attempted (django-redis).
    With LocMemCache the pattern delete is a best-effort no-op;
    callers should pass explicit *location_ids* when possible.
    """
    if location_ids:
        for loc_id in location_ids:
            invalidate_stock_record(product_id, loc_id)
        return

    pattern = stock_product_pattern(product_id) + "*"
    delete_pattern = getattr(cache, "delete_pattern", None)
    if callable(delete_pattern):
        delete_pattern(pattern)
        logger.debug("Cache INVALIDATE pattern: %s", pattern)
    else:
        logger.debug("Cache INVALIDATE (no pattern support, skipped): %s", pattern)


_KNOWN_DASHBOARD_NAMES = ("summary", "stock_by_location")


def invalidate_dashboard() -> None:
    """Wipe all dashboard summary caches for the current tenant."""
    delete_pattern = getattr(cache, "delete_pattern", None)
    if callable(delete_pattern):
        pattern = f"{DASHBOARD_PREFIX}:{_tenant_id()}:*"
        delete_pattern(pattern)
        logger.debug("Cache INVALIDATE pattern: %s", pattern)
    else:
        keys = [dashboard_key(name) for name in _KNOWN_DASHBOARD_NAMES]
        cache.delete_many(keys)
        logger.debug("Cache INVALIDATE dashboard keys: %s", keys)


# ------------------------------------------------------------------
# High-level wrappers used by services / views
# ------------------------------------------------------------------

def get_cached_stock_record(product_id: int, location_id: int):
    """Return cached stock-record dict or ``None``."""
    return cache_get(stock_record_key(product_id, location_id))


def set_cached_stock_record(product_id: int, location_id: int, data: dict) -> None:
    cache_set(stock_record_key(product_id, location_id), data)


def get_cached_dashboard(name: str):
    return cache_get(dashboard_key(name))


def set_cached_dashboard(name: str, data) -> None:
    cache_set(dashboard_key(name), data, kind="dashboard")
