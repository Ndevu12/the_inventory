"""Tests for seed_database management command with tenant context."""

from io import StringIO
from django.test import TransactionTestCase
from django.core.management import call_command
from django.core.management.base import CommandError

from tenants.models import Tenant
from tenants.context import get_current_tenant
from tests.fixtures.factories import create_tenant


class SeedDatabaseCommandTest(TransactionTestCase):
    """Test suite for the seed_database management command.
    
    Uses TransactionTestCase for proper test isolation with database transactions.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.stdout = StringIO()
        self.stderr = StringIO()

    def test_seed_command_fails_without_default_tenant(self):
        """Test: seed_database fails if Default tenant missing and not --clear / --create-default."""
        # Ensure no default tenant exists
        Tenant.objects.filter(slug="default").delete()

        # Call command without --create-default
        with self.assertRaises(CommandError) as cm:
            call_command(
                "seed_database",
                "--quiet",
                stdout=self.stdout,
                stderr=self.stderr,
            )

        self.assertIn("Default tenant does not exist", str(cm.exception))
        self.assertIn("--create-default", str(cm.exception))

    def test_seed_command_clear_creates_default_tenant_if_missing(self):
        """Test: --clear creates Default tenant when missing (dev full reset)."""
        Tenant.objects.filter(slug="default").delete()

        call_command(
            "seed_database",
            "--clear",
            "--quiet",
            stdout=self.stdout,
            stderr=self.stderr,
        )

        tenant = Tenant.objects.get(slug="default")
        self.assertEqual(tenant.name, "Default")
        self.assertTrue(tenant.is_active)

    def test_seed_command_uses_specified_tenant(self):
        """Test: seed_database seeds into specified tenant when --tenant is provided."""
        # Create a specific tenant
        create_tenant(name="Acme Corp", slug="acme-corp")

        # Call command with --tenant flag
        call_command(
            "seed_database",
            "--tenant",
            "acme-corp",
            "--quiet",
            stdout=self.stdout,
            stderr=self.stderr,
        )

        # Verify command succeeded and output mentions tenant
        output = self.stdout.getvalue()
        self.assertIn("acme-corp", output.lower())
        self.assertIn("Acme Corp", output)

    def test_seed_command_fails_with_nonexistent_tenant(self):
        """Test: seed_database fails if specified tenant does not exist."""
        # Call command with non-existent tenant
        with self.assertRaises(CommandError) as cm:
            call_command(
                "seed_database",
                "--tenant",
                "nonexistent",
                "--quiet",
                stdout=self.stdout,
                stderr=self.stderr,
            )

        self.assertIn("nonexistent", str(cm.exception))
        self.assertIn("not found", str(cm.exception))

    def test_seed_command_clears_context_after_seeding(self):
        """Test: seed_database clears tenant context after seeding completes."""
        # Create a tenant
        create_tenant(name="Cleanup Test", slug="cleanup-test")

        # Call command
        call_command(
            "seed_database",
            "--tenant",
            "cleanup-test",
            "--quiet",
            stdout=self.stdout,
            stderr=self.stderr,
        )

        # Verify context is cleared (should be None after command completes)
        current_tenant = get_current_tenant()
        self.assertIsNone(current_tenant, "Tenant context should be cleared after seeding")

    def test_seed_command_clears_context_on_error(self):
        """Test: seed_database clears tenant context even if seeding fails."""
        # Create a tenant
        create_tenant(name="Error Test", slug="error-test")

        # Call command with invalid model to trigger error
        with self.assertRaises(CommandError):
            call_command(
                "seed_database",
                "--tenant",
                "error-test",
                "--models",
                "invalid_model",
                stdout=self.stdout,
                stderr=self.stderr,
            )

        # Verify context is cleared despite error
        current_tenant = get_current_tenant()
        self.assertIsNone(
            current_tenant,
            "Tenant context should be cleared even after error",
        )

    def test_seed_command_with_create_default_uses_existing(self):
        """Test: --create-default doesn't re-create if Default tenant already exists."""
        # Create Default tenant
        original_default = create_tenant(name="Default", slug="default")

        # Call command with --create-default
        call_command(
            "seed_database",
            "--create-default",
            "--quiet",
            stdout=self.stdout,
            stderr=self.stderr,
        )

        # Verify same tenant is used (no duplicate created)
        default_tenant = Tenant.objects.get(slug="default")
        self.assertEqual(default_tenant.id, original_default.id)
        self.assertEqual(Tenant.objects.filter(slug="default").count(), 1)

    def test_seed_command_default_behavior_no_flags(self):
        """Test: seed_database with no --tenant or --create-default requires existing Default."""
        # Create Default tenant
        create_tenant(name="Default", slug="default")

        # Call command without any tenant flags
        call_command(
            "seed_database",
            "--quiet",
            stdout=self.stdout,
            stderr=self.stderr,
        )

        # Should succeed using existing Default
        output = self.stdout.getvalue()
        self.assertIn("seeding completed successfully", output.lower())

    def test_seed_command_models_users_runs_user_seeders(self):
        """Test: --models=users seeds platform + tenant users for resolved tenant."""
        from django.contrib.auth import get_user_model
        from tenants.models import TenantMembership

        tenant = create_tenant(name="Default", slug="default")
        User = get_user_model()

        call_command(
            "seed_database",
            "--models",
            "users",
            "--quiet",
            stdout=self.stdout,
            stderr=self.stderr,
        )

        self.assertTrue(User.objects.filter(username="platform_super").exists())
        owner = User.objects.get(username="owner")
        self.assertTrue(
            TenantMembership.objects.filter(user=owner, tenant=tenant).exists(),
        )

    def test_seed_command_create_default_flag_ignored_with_tenant(self):
        """Test: --create-default is ignored when --tenant is specified."""
        # Create a specific tenant
        create_tenant(name="Specific", slug="specific")

        # Ensure Default doesn't exist
        Tenant.objects.filter(slug="default").delete()

        # Call command with both --tenant and --create-default
        # Should use the specified tenant, not create Default
        call_command(
            "seed_database",
            "--tenant",
            "specific",
            "--create-default",
            "--quiet",
            stdout=self.stdout,
            stderr=self.stderr,
        )

        # Default should not be created
        self.assertEqual(Tenant.objects.filter(slug="default").count(), 0)

        # Specific tenant should be used
        output = self.stdout.getvalue()
        self.assertIn("specific", output.lower())
