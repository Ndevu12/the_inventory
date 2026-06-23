# Plugins

**The Inventory** supports plugins: optional, self-contained Django apps that
extend the system — adding API endpoints, Celery tasks, Wagtail admin panels,
models, and more — without modifying core code.

The framework deliberately reuses the auto-discovery that Django, Celery, and
Wagtail already provide, and adds one thin seam — an **API registry** — so
plugins can contribute REST routes without editing `api/urls.py`.

> The four business domains (`inventory`, `procurement`, `sales`, `reports`) are
> themselves registered as first-class plugins, so the mechanism is dogfooded by
> the core app.

---

## What a plugin can do out of the box

Because a plugin is a normal Django app, these all work with **zero** extra
wiring once the app is installed:

| Capability        | How it's discovered                                            |
| ----------------- | -------------------------------------------------------------- |
| Models / migrations | Django app loading (`makemigrations`, `migrate`)            |
| Celery tasks      | `app.autodiscover_tasks()` scans every app's `tasks.py`        |
| Wagtail admin     | Wagtail auto-loads each app's `wagtail_hooks.py` / snippets    |
| Multi-tenancy     | `tenants.context.get_current_tenant()` is available anywhere   |
| Signals           | Connect them in your `AppConfig.ready()`                       |

The one thing core Django can't do — let an app add DRF routes under
`/api/v1/` — is solved by the registry below.

---

## Anatomy of a plugin

```
my_plugin/
├── __init__.py
├── apps.py            # PluginConfig subclass with metadata
├── api_register.py    # registers ViewSets / routes (auto-discovered)
├── views.py           # your DRF views/viewsets
├── models.py          # optional
├── tasks.py           # optional Celery tasks (auto-discovered)
└── wagtail_hooks.py   # optional admin extensions (auto-discovered)
```

### 1. Declare the app — `apps.py`

```python
from plugins.base import PluginConfig


class MyPluginConfig(PluginConfig):
    # Required when subclassing an AppConfig imported from another module:
    # tells Django to pick this class over the imported PluginConfig base.
    default = True

    name = "my_plugin"
    plugin_name = "my_plugin"          # stable id other plugins depend on
    plugin_version = "1.0.0"
    plugin_verbose_name = "My Plugin"
    plugin_description = "Adds gizmo endpoints."
    plugin_requires = ["inventory>=1.0"]  # optional dependencies
```

`plugin_requires` entries are validated at startup against other loaded plugins'
`plugin_name`/`plugin_version`. A missing or version-incompatible dependency
raises `ImproperlyConfigured` so misconfiguration fails fast. Supported
specifiers: `==`, `>=`, `<=`, `>`, `<`, `~=`, or a bare name (presence only).

> **Why `default = True`?** When your `apps.py` does
> `from plugins.base import PluginConfig`, the module now contains *two*
> `AppConfig` subclasses (the imported base and yours). Django needs
> `default = True` to know which one to use. (The base class can't set it —
> the value would be inherited and reintroduce the ambiguity.)

### 2. Add API routes — `api_register.py`

This module is auto-discovered at startup (like `wagtail_hooks.py`). Register
against the shared registry:

```python
from django.urls import path
from rest_framework import viewsets

from plugins.registry import registry, PLATFORM_SCOPE
from my_plugin.views import GizmoViewSet, GizmoStatsView

# A DRF ViewSet → mounted at /api/v1/gizmos/
registry.register_viewset("gizmos", GizmoViewSet, basename="gizmo", source="my_plugin")

# A platform-admin ViewSet → mounted at /api/v1/platform/gizmos/
registry.register_viewset("gizmos", GizmoViewSet, scope=PLATFORM_SCOPE, source="my_plugin")

# A plain APIView route → mounted at /api/v1/gizmos/stats/
registry.register_route(
    path("gizmos/stats/", GizmoStatsView.as_view(), name="api-gizmo-stats"),
    source="my_plugin",
)
```

- `register_viewset(prefix, viewset, *, basename=None, scope="tenant", source=None)`
  — `scope` is `"tenant"` (default, under `/api/v1/`) or `"platform"` (under
  `/api/v1/platform/`). `basename` defaults to a slug of the prefix.
- `register_route(path_obj, *, source=None)` — for `APIView`-style endpoints.
- Prefix collisions within the same scope raise `ImproperlyConfigured`, so two
  plugins can't silently shadow each other.

### 3. Per-plugin settings (optional)

Don't add top-level Django settings; namespace them under `PLUGIN_SETTINGS`:

```python
# settings/base.py (or via your production settings / env)
PLUGIN_SETTINGS = {
    "my_plugin": {"GIZMO_LIMIT": 100},
}
```

```python
from plugins.settings import plugin_setting

limit = plugin_setting("my_plugin", "GIZMO_LIMIT", default=50)
```

---

## Installing a plugin

There are three ways to load a plugin; pick whichever fits.

1. **In-tree app** — add it to `INSTALLED_APPS` in settings, like any Django app.

2. **`PLUGINS` environment variable** — a comma-separated list of dotted app
   paths, appended to `INSTALLED_APPS` at startup. Great for local development:

   ```bash
   PLUGINS=plugins.examples.hello,my_company.barcodes
   ```

3. **Entry points** (pip-installable plugins) — a distribution advertises its
   app via the `the_inventory.plugins` entry-point group:

   ```toml
   # the plugin package's own pyproject.toml
   [project.entry-points."the_inventory.plugins"]
   barcodes = "inventory_barcodes"
   ```

   After `pip install inventory-barcodes`, the app is discovered and installed
   automatically — no settings change required.

Discovery is handled by `plugins.discovery.discover_plugin_apps()`, called from
`settings/base.py`. Already-installed and duplicate apps are skipped.

---

## Inspecting plugins

- **CLI:** `python manage.py plugins` lists loaded plugins, versions,
  dependencies, and all registered API contributions.
- **API:** `GET /api/v1/plugins/` (authenticated) returns plugin metadata as
  JSON. This endpoint is itself registered through the registry.

---

## A complete example

A working reference plugin ships at `src/plugins/examples/hello/`. It is **not**
installed by default. Enable it with:

```bash
PLUGINS=plugins.examples.hello python manage.py runserver
```

Then `GET /api/v1/hello/` returns a tenant-scoped greeting, and the plugin shows
up in `GET /api/v1/plugins/` and `manage.py plugins`. Read its source as a
starting template.

---

## How it wires together

1. `settings/base.py` builds `INSTALLED_APPS`, then appends plugin apps from the
   `PLUGINS` env var and entry points.
2. On startup, `plugins.apps.PluginsConfig.ready()`:
   - runs `autodiscover_modules("api_register")`, importing every app's
     `api_register.py` so its `registry.register_*` calls execute;
   - calls `plugins.manager.validate_plugins()` to enforce dependencies.
3. When the URLconf loads, `api/urls.py` calls `registry.apply(...)` to mount
   plugin ViewSets onto the routers and splices in `registry.get_url_patterns()`.

Because `ready()` runs before the URLconf is imported, the registry is fully
populated by the time routes are built.
