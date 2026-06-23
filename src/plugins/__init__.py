"""Plugin framework for The Inventory.

This package turns The Inventory into a host for optional, self-contained
plugins.  A plugin is an ordinary Django app that:

* subclasses :class:`plugins.base.PluginConfig` in its ``apps.py`` so it can
  declare metadata (name, version, dependencies);
* optionally ships an ``api_register.py`` module that registers DRF ViewSets
  or extra URL routes against the shared :data:`plugins.registry.registry`;
* is loaded either by being listed in ``INSTALLED_APPS``, via the ``PLUGINS``
  environment variable, or by exposing a ``the_inventory.plugins`` entry point
  from an installed distribution.

The framework leans on Django/Celery/Wagtail's existing auto-discovery instead
of inventing new machinery: ``api_register`` modules are discovered exactly the
way Wagtail discovers ``wagtail_hooks`` and Celery discovers ``tasks``.

See ``docs/plugins.md`` for the authoring guide.
"""
