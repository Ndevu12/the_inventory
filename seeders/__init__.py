"""Seeders for populating the inventory app with sample data.

This module provides data seeders for development and testing.
Each seeder handles one or more related models and creates realistic sample data.

Usage:
    python manage.py seed_database --clear --create-default
    python manage.py seed_database --tenant=acme-corp
    python manage.py seed_database --models=categories,products
"""

default_app_config = "seeders.apps.SeedersConfig"


def __getattr__(name):
    """Lazy import SeederManager to avoid AppRegistryNotReady errors."""
    if name == "SeederManager":
        from .seeder_manager import SeederManager
        return SeederManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["SeederManager"]
