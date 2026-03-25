"""Seeder for platform-plane operator accounts (Wagtail / platform API).

Usernames use the ``platform_*`` prefix and emails the ``@system.local`` domain so
they are never confused with tenant org accounts (see docs/ARCHITECTURE.md).

These users have Django ``is_staff`` / ``is_superuser`` as needed for Wagtail but
**no** ``TenantMembership`` rows so they cannot obtain tenant JWTs for the
inventory SPA.
"""

from django.contrib.auth import get_user_model

from .base import BaseSeeder

User = get_user_model()


class PlatformUserSeeder(BaseSeeder):
    """Create platform operators with explicit Django flags and **no** org memberships."""

    def seed(self):
        self.log("Creating platform operator accounts (no tenant memberships)...")

        superuser, created = User.objects.get_or_create(
            username="platform_super",
            defaults={
                "email": "platform.superoperator@system.local",
                "first_name": "Platform",
                "last_name": "Superoperator",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            superuser.set_password("platform_super123")
            superuser.save()
            self.log(
                f"✓ Created platform superuser: {superuser.username} (Wagtail / break-glass)"
            )
        else:
            self.log(f"✓ Using existing platform superuser: {superuser.username}")

        staff_only, created = User.objects.get_or_create(
            username="platform_staff",
            defaults={
                "email": "platform.operator@system.local",
                "first_name": "Platform",
                "last_name": "Operator",
                "is_staff": True,
                "is_superuser": False,
            },
        )
        if created:
            staff_only.set_password("platform_staff123")
            staff_only.save()
            self.log(f"✓ Created staff-only platform user: {staff_only.username}")
        else:
            self.log(f"✓ Using existing staff platform user: {staff_only.username}")
