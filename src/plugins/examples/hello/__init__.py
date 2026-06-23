"""Reference plugin demonstrating the plugin framework.

This app is NOT installed by default. Enable it during development with::

    PLUGINS=plugins.examples.hello

It adds a single tenant-scoped endpoint at ``/api/v1/hello/`` and declares a
dependency on the core ``inventory`` plugin to exercise dependency validation.
"""
