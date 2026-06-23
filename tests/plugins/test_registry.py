"""Tests for the API registry that plugins contribute to."""

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase
from django.urls import path
from rest_framework import viewsets

from plugins.registry import PLATFORM_SCOPE, TENANT_SCOPE, APIRegistry


class _DummyViewSet(viewsets.ViewSet):
    pass


class _FakeRouter:
    """Minimal stand-in capturing router.register calls."""

    def __init__(self):
        self.registered = []

    def register(self, prefix, viewset, basename=None):
        self.registered.append((prefix, viewset, basename))


class RegisterViewSetTests(SimpleTestCase):
    def setUp(self):
        self.registry = APIRegistry()

    def test_register_and_apply_tenant_scope(self):
        self.registry.register_viewset("widgets", _DummyViewSet, basename="widget", source="p")
        router, platform = _FakeRouter(), _FakeRouter()
        self.registry.apply(router, platform)
        self.assertEqual(router.registered, [("widgets", _DummyViewSet, "widget")])
        self.assertEqual(platform.registered, [])

    def test_platform_scope_routes_to_platform_router(self):
        self.registry.register_viewset("audit", _DummyViewSet, scope=PLATFORM_SCOPE)
        router, platform = _FakeRouter(), _FakeRouter()
        self.registry.apply(router, platform)
        self.assertEqual(router.registered, [])
        self.assertEqual(len(platform.registered), 1)

    def test_basename_defaults_from_prefix(self):
        self.registry.register_viewset("my/widgets", _DummyViewSet)
        router, platform = _FakeRouter(), _FakeRouter()
        self.registry.apply(router, platform)
        self.assertEqual(router.registered[0][2], "my-widgets")

    def test_duplicate_prefix_same_scope_raises(self):
        self.registry.register_viewset("widgets", _DummyViewSet, source="a")
        with self.assertRaises(ImproperlyConfigured):
            self.registry.register_viewset("widgets", _DummyViewSet, source="b")

    def test_same_prefix_different_scope_is_allowed(self):
        self.registry.register_viewset("things", _DummyViewSet, scope=TENANT_SCOPE)
        self.registry.register_viewset("things", _DummyViewSet, scope=PLATFORM_SCOPE)
        # No exception; both recorded.
        self.assertEqual(len(self.registry.contributions()["viewsets"]), 2)

    def test_unknown_scope_raises(self):
        with self.assertRaises(ImproperlyConfigured):
            self.registry.register_viewset("x", _DummyViewSet, scope="galaxy")

    def test_empty_prefix_raises(self):
        with self.assertRaises(ImproperlyConfigured):
            self.registry.register_viewset("/", _DummyViewSet)


class RegisterRouteTests(SimpleTestCase):
    def setUp(self):
        self.registry = APIRegistry()

    def test_route_collected_and_returned(self):
        route = path("ping/", lambda r: None, name="ping")
        self.registry.register_route(route, source="p")
        self.assertEqual(self.registry.get_url_patterns(), [route])

    def test_contributions_and_reset(self):
        self.registry.register_viewset("widgets", _DummyViewSet, source="p")
        self.registry.register_route(path("ping/", lambda r: None), source="p")
        contrib = self.registry.contributions()
        self.assertEqual(len(contrib["viewsets"]), 1)
        self.assertEqual(len(contrib["routes"]), 1)

        self.registry.reset()
        self.assertEqual(self.registry.get_url_patterns(), [])
        self.assertEqual(self.registry.contributions(), {"viewsets": [], "routes": []})
        # Prefix is free again after reset.
        self.registry.register_viewset("widgets", _DummyViewSet)
