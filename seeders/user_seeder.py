"""Seeder for tenant-plane users and ``TenantMembership`` rows.

Usernames match tenant roles; emails use ``@org.seed.local`` (fictional org mailbox)
so they read as **organization members**, not system operators—see
docs/ARCHITECTURE.md (*Vocabulary: tenant identifiers vs platform terminology*).
"""

from django.contrib.auth import get_user_model

from tenants.models import TenantMembership, TenantRole

from .base import BaseSeeder

User = get_user_model()

# Shared synthetic domain for seeded tenant mailboxes (not deliverable).
_TENANT_SEED_EMAIL_DOMAIN = "org.seed.local"


class UserSeeder(BaseSeeder):
    """Create tenant-only users (``is_staff=False``) and link them to the tenant.

    Inventory SPA + tenant JWT require at least one active membership; these
    accounts are **org members**, not Wagtail-only operators (see
    ``PlatformUserSeeder``).
    """

    def seed(self):
        self.log("Creating tenant users and memberships...")
        if not self.tenant:
            self.log("✗ No tenant context; skipping tenant users")
            return

        specs = [
            (
                "owner",
                {
                    "email": f"owner@{_TENANT_SEED_EMAIL_DOMAIN}",
                    "first_name": "Elena",
                    "last_name": "Martinez",
                },
                TenantRole.OWNER,
                True,
            ),
            (
                "coordinator",
                {
                    "email": f"coordinator@{_TENANT_SEED_EMAIL_DOMAIN}",
                    "first_name": "Jordan",
                    "last_name": "Lee",
                },
                TenantRole.COORDINATOR,
                False,
            ),
            (
                "manager",
                {
                    "email": f"manager@{_TENANT_SEED_EMAIL_DOMAIN}",
                    "first_name": "Sam",
                    "last_name": "Nguyen",
                },
                TenantRole.MANAGER,
                False,
            ),
            (
                "tenant_viewer",
                {
                    "email": f"viewer@{_TENANT_SEED_EMAIL_DOMAIN}",
                    "first_name": "Riley",
                    "last_name": "Chen",
                },
                TenantRole.VIEWER,
                False,
            ),
        ]

        passwords = {
            "owner": "owner123",
            "coordinator": "coordinator123",
            "manager": "manager123",
            "tenant_viewer": "tenant_viewer123",
        }

        for username, name_fields, role, is_default in specs:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    **name_fields,
                    "is_staff": False,
                    "is_superuser": False,
                },
            )
            if created:
                user.set_password(passwords[username])
                user.save()
                self.log(f"✓ Created tenant user: {username} (role seed: {role})")
            else:
                self.log(f"✓ Using existing tenant user: {username}")

            self._add_user_to_tenant(user, role, is_default=is_default)

    def _add_user_to_tenant(self, user, role, is_default=False):
        membership, created = TenantMembership.objects.get_or_create(
            tenant=self.tenant,
            user=user,
            defaults={
                "role": role,
                "is_active": True,
                "is_default": is_default,
            },
        )
        if created:
            self.log(
                f"  ✓ Added {user.username} to {self.tenant.name} as {role}"
            )
        else:
            self.log(
                f"  ✓ {user.username} already member of {self.tenant.name}"
            )
