"""Tests for the stock-record caching layer.

Verifies cache key generation, hit/miss behaviour, invalidation on
stock movements and reservation changes, dashboard caching, and
graceful degradation when Redis is unavailable (LocMemCache fallback).
"""

from decimal import Decimal
from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase, override_settings

from inventory.models import MovementType
from inventory.services.cache import (
    cache_get,
    cache_set,
    dashboard_key,
    get_cached_dashboard,
    get_cached_stock_record,
    invalidate_dashboard,
    invalidate_product_stock,
    invalidate_stock_record,
    set_cached_dashboard,
    set_cached_stock_record,
    stock_record_key,
)
from inventory.services.stock import StockService

from ..factories import create_location, create_product, create_stock_record


LOCMEM_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-stock-cache",
    }
}


@override_settings(CACHES=LOCMEM_CACHES)
class CacheKeyTests(TestCase):
    """Test cache key generation."""

    def test_stock_record_key_format(self):
        key = stock_record_key(42, 7)
        self.assertIn("stock:", key)
        self.assertIn(":42:", key)
        self.assertIn(":7", key)

    def test_dashboard_key_format(self):
        key = dashboard_key("summary")
        self.assertIn("dashboard:", key)
        self.assertIn(":summary", key)

    def test_different_products_get_different_keys(self):
        k1 = stock_record_key(1, 10)
        k2 = stock_record_key(2, 10)
        self.assertNotEqual(k1, k2)

    def test_different_locations_get_different_keys(self):
        k1 = stock_record_key(1, 10)
        k2 = stock_record_key(1, 20)
        self.assertNotEqual(k1, k2)


@override_settings(CACHES=LOCMEM_CACHES)
class CacheGetSetTests(TestCase):
    """Test basic get/set/miss behaviour."""

    def setUp(self):
        cache.clear()

    def test_cache_miss_returns_none(self):
        result = cache_get("nonexistent")
        self.assertIsNone(result)

    def test_set_then_get(self):
        cache_set("mykey", {"qty": 100})
        result = cache_get("mykey")
        self.assertEqual(result, {"qty": 100})

    def test_stock_record_helpers(self):
        data = {"product_id": 1, "location_id": 2, "quantity": 50}
        set_cached_stock_record(1, 2, data)
        cached = get_cached_stock_record(1, 2)
        self.assertEqual(cached, data)

    def test_dashboard_helpers(self):
        data = {"total_products": 5}
        set_cached_dashboard("summary", data)
        cached = get_cached_dashboard("summary")
        self.assertEqual(cached, data)


@override_settings(CACHES=LOCMEM_CACHES)
class CacheInvalidationTests(TestCase):
    """Test that invalidation helpers delete the correct keys."""

    def setUp(self):
        cache.clear()

    def test_invalidate_stock_record(self):
        set_cached_stock_record(1, 2, {"qty": 10})
        self.assertIsNotNone(get_cached_stock_record(1, 2))
        invalidate_stock_record(1, 2)
        self.assertIsNone(get_cached_stock_record(1, 2))

    def test_invalidate_product_stock_with_location_ids(self):
        set_cached_stock_record(1, 10, {"qty": 10})
        set_cached_stock_record(1, 20, {"qty": 20})
        set_cached_stock_record(1, 30, {"qty": 30})
        invalidate_product_stock(1, location_ids=[10, 20])
        self.assertIsNone(get_cached_stock_record(1, 10))
        self.assertIsNone(get_cached_stock_record(1, 20))
        self.assertIsNotNone(get_cached_stock_record(1, 30))

    def test_invalidate_dashboard(self):
        set_cached_dashboard("summary", {"total": 5})
        set_cached_dashboard("stock_by_location", {"labels": []})
        invalidate_dashboard()
        self.assertIsNone(get_cached_dashboard("summary"))


@override_settings(CACHES=LOCMEM_CACHES)
class StockServiceCacheInvalidationTests(TestCase):
    """Verify StockService busts cache on movements."""

    def setUp(self):
        cache.clear()
        self.service = StockService()
        self.product = create_product(sku="CACHE-001", unit_cost=Decimal("5.00"))
        self.warehouse = create_location(name="Cache Warehouse")
        self.store = create_location(name="Cache Store")

    def test_receive_invalidates_to_location_cache(self):
        set_cached_stock_record(self.product.pk, self.warehouse.pk, {"qty": 0})
        set_cached_dashboard("summary", {"stale": True})

        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
        )

        self.assertIsNone(get_cached_stock_record(self.product.pk, self.warehouse.pk))
        self.assertIsNone(get_cached_dashboard("summary"))

    def test_issue_invalidates_from_location_cache(self):
        create_stock_record(product=self.product, location=self.warehouse, quantity=100)
        set_cached_stock_record(self.product.pk, self.warehouse.pk, {"qty": 100})

        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=20,
            from_location=self.warehouse,
        )

        self.assertIsNone(get_cached_stock_record(self.product.pk, self.warehouse.pk))

    def test_transfer_invalidates_both_locations(self):
        create_stock_record(product=self.product, location=self.warehouse, quantity=100)
        set_cached_stock_record(self.product.pk, self.warehouse.pk, {"qty": 100})
        set_cached_stock_record(self.product.pk, self.store.pk, {"qty": 0})

        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.TRANSFER,
            quantity=30,
            from_location=self.warehouse,
            to_location=self.store,
        )

        self.assertIsNone(get_cached_stock_record(self.product.pk, self.warehouse.pk))
        self.assertIsNone(get_cached_stock_record(self.product.pk, self.store.pk))

    def test_failed_movement_does_not_invalidate(self):
        """Cache should stay intact when a movement fails."""
        set_cached_stock_record(self.product.pk, self.warehouse.pk, {"qty": 0})

        from inventory.exceptions import InsufficientStockError
        with self.assertRaises(InsufficientStockError):
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.ISSUE,
                quantity=10,
                from_location=self.warehouse,
            )

        self.assertIsNotNone(get_cached_stock_record(self.product.pk, self.warehouse.pk))


@override_settings(CACHES=LOCMEM_CACHES)
class CacheHitMissLoggingTests(TestCase):
    """Verify that cache operations produce the expected log messages."""

    def setUp(self):
        cache.clear()

    def test_miss_logs_debug_message(self):
        with self.assertLogs("inventory.services.cache", level="DEBUG") as cm:
            cache_get("absent-key")
        self.assertTrue(any("MISS" in msg for msg in cm.output))

    def test_hit_logs_debug_message(self):
        cache_set("present-key", "value")
        with self.assertLogs("inventory.services.cache", level="DEBUG") as cm:
            cache_get("present-key")
        self.assertTrue(any("HIT" in msg for msg in cm.output))

    def test_set_logs_debug_message(self):
        with self.assertLogs("inventory.services.cache", level="DEBUG") as cm:
            cache_set("new-key", "val")
        self.assertTrue(any("SET" in msg for msg in cm.output))

    def test_invalidate_logs_debug_message(self):
        set_cached_stock_record(1, 1, {"data": True})
        with self.assertLogs("inventory.services.cache", level="DEBUG") as cm:
            invalidate_stock_record(1, 1)
        self.assertTrue(any("INVALIDATE" in msg for msg in cm.output))


@override_settings(CACHES=LOCMEM_CACHES, STOCK_CACHE_TTL=600, DASHBOARD_CACHE_TTL=300)
class CacheTTLTests(TestCase):
    """Verify that TTL settings are respected."""

    def setUp(self):
        cache.clear()

    def test_stock_cache_uses_configured_ttl(self):
        with patch.object(cache, "set", wraps=cache.set) as mock_set:
            cache_set(stock_record_key(1, 1), {"qty": 10})
            mock_set.assert_called_once()
            _, kwargs_or_args = mock_set.call_args
            timeout = mock_set.call_args[0][2] if len(mock_set.call_args[0]) > 2 else mock_set.call_args[1].get("timeout")
            self.assertEqual(timeout, 600)

    def test_dashboard_cache_uses_configured_ttl(self):
        with patch.object(cache, "set", wraps=cache.set) as mock_set:
            cache_set(dashboard_key("summary"), {"total": 5}, kind="dashboard")
            timeout = mock_set.call_args[0][2] if len(mock_set.call_args[0]) > 2 else mock_set.call_args[1].get("timeout")
            self.assertEqual(timeout, 300)


@override_settings(CACHES=LOCMEM_CACHES)
class FallbackWithoutRedisTests(TestCase):
    """Confirm everything works with LocMemCache (no Redis dependency)."""

    def setUp(self):
        cache.clear()

    def test_full_lifecycle_without_redis(self):
        set_cached_stock_record(1, 1, {"qty": 99})
        self.assertEqual(get_cached_stock_record(1, 1), {"qty": 99})

        invalidate_stock_record(1, 1)
        self.assertIsNone(get_cached_stock_record(1, 1))

    def test_dashboard_lifecycle_without_redis(self):
        set_cached_dashboard("summary", {"total": 10})
        self.assertEqual(get_cached_dashboard("summary"), {"total": 10})

        invalidate_dashboard()
        self.assertIsNone(get_cached_dashboard("summary"))

    def test_invalidate_product_stock_without_pattern_support(self):
        """LocMemCache has no delete_pattern; verify no crash."""
        set_cached_stock_record(1, 10, {"qty": 10})
        invalidate_product_stock(1)
