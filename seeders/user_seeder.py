"""Seeder for User and TenantMembership models."""

from django.contrib.auth import get_user_model
from tenants.models import TenantMembership, TenantRole
from .base import BaseSeeder

User = get_user_model()


class UserSeeder(BaseSeeder):
    """Create test users and assign them to the tenant with various roles."""

    def seed(self):
        """Create test users and add them to the tenant."""
        self.log("Creating test users...")

        # Admin user
        admin_user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@example.com",
                "first_name": "Admin",
                "last_name": "User",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin_user.set_password("admin123")
            admin_user.save()
            self.log(f"✓ Created superuser: {admin_user.username}")
        else:
            self.log(f"✓ Using existing superuser: {admin_user.username}")

        # Manager user
        manager_user, created = User.objects.get_or_create(
            username="manager",
            defaults={
                "email": "manager@example.com",
                "first_name": "Manager",
                "last_name": "User",
                "is_staff": True,
            },
        )
        if created:
            manager_user.set_password("manager123")
            manager_user.save()
            self.log(f"✓ Created staff user: {manager_user.username}")
        else:
            self.log(f"✓ Using existing staff user: {manager_user.username}")

        # Regular user
        regular_user, created = User.objects.get_or_create(
            username="user",
            defaults={
                "email": "user@example.com",
                "first_name": "Regular",
                "last_name": "User",
                "is_staff": False,
            },
        )
        if created:
            regular_user.set_password("user123")
            regular_user.save()
            self.log(f"✓ Created regular user: {regular_user.username}")
        else:
            self.log(f"✓ Using existing regular user: {regular_user.username}")

        # Add users to tenant with appropriate roles
        if self.tenant:
            self._add_user_to_tenant(admin_user, TenantRole.ADMIN, is_default=True)
            self._add_user_to_tenant(manager_user, TenantRole.MANAGER)
            self._add_user_to_tenant(regular_user, TenantRole.VIEWER)

    def _add_user_to_tenant(self, user, role, is_default=False):
        """Add a user to the tenant with the specified role."""
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
