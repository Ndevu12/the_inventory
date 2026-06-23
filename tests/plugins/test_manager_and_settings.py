"""Tests for plugin discovery helpers, manager, and settings access."""

from unittest import mock

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from plugins import discovery, manager
from plugins.settings import plugin_setting, plugin_settings


class _FakePlugin:
    def __init__(self, name, version="1.0.0", requires=None):
        self.resolved_plugin_name = name
        self.plugin_version = version
        self.plugin_requires = requires or []

    def plugin_metadata(self):
        return {
            "name": self.resolved_plugin_name,
            "version": self.plugin_version,
            "requires": list(self.plugin_requires),
        }


class GetLoadedPluginsTests(SimpleTestCase):
    def test_includes_core_domains(self):
        names = {meta["name"] for meta in manager.get_loaded_plugins()}
        # The four business domains are registered as first-class plugins.
        self.assertLessEqual({"inventory", "procurement", "sales", "reports"}, names)

    def test_sorted_by_name(self):
        names = [meta["name"] for meta in manager.get_loaded_plugins()]
        self.assertEqual(names, sorted(names))


class ValidatePluginsTests(SimpleTestCase):
    def _patch(self, plugins):
        return mock.patch.object(manager, "get_plugin_configs", return_value=plugins)

    def test_satisfied_presence_dependency(self):
        with self._patch([_FakePlugin("a", requires=["b"]), _FakePlugin("b")]):
            manager.validate_plugins()  # no raise

    def test_missing_dependency_raises(self):
        with self._patch([_FakePlugin("a", requires=["b"])]):
            with self.assertRaises(ImproperlyConfigured):
                manager.validate_plugins()

    def test_version_mismatch_raises(self):
        with self._patch([_FakePlugin("a", requires=["b>=2.0"]), _FakePlugin("b", "1.0.0")]):
            with self.assertRaises(ImproperlyConfigured):
                manager.validate_plugins()

    def test_version_satisfied(self):
        with self._patch([_FakePlugin("a", requires=["b>=1.0"]), _FakePlugin("b", "1.5.0")]):
            manager.validate_plugins()  # no raise


class DiscoveryTests(SimpleTestCase):
    def test_env_plugins_parsed_and_trimmed(self):
        with mock.patch.dict("os.environ", {"PLUGINS": " a.b , c.d ,, "}):
            with mock.patch.object(discovery, "_entry_point_plugin_apps", return_value=[]):
                self.assertEqual(discovery.discover_plugin_apps(), ["a.b", "c.d"])

    def test_already_installed_and_duplicates_dropped(self):
        with mock.patch.dict("os.environ", {"PLUGINS": "a.b,a.b,e.f"}):
            with mock.patch.object(discovery, "_entry_point_plugin_apps", return_value=["e.f"]):
                result = discovery.discover_plugin_apps(already_installed=["a.b"])
        self.assertEqual(result, ["e.f"])


class SettingsAccessTests(SimpleTestCase):
    @override_settings(PLUGIN_SETTINGS={"hello": {"GREETING": "Hi"}})
    def test_plugin_setting_returns_configured_value(self):
        self.assertEqual(plugin_setting("hello", "GREETING"), "Hi")
        self.assertEqual(plugin_settings("hello"), {"GREETING": "Hi"})

    @override_settings(PLUGIN_SETTINGS={})
    def test_plugin_setting_falls_back_to_default(self):
        self.assertEqual(plugin_setting("hello", "GREETING", default="Hello"), "Hello")
        self.assertEqual(plugin_settings("missing"), {})
