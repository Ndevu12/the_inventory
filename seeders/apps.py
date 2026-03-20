"""Seeders app configuration."""

from django.apps import AppConfig


class SeedersConfig(AppConfig):
    """Configuration for the seeders app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "seeders"
    verbose_name = "Database Seeders"
