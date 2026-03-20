"""Base seeder class providing common functionality for all seeders."""

from abc import ABC, abstractmethod
from django.db import transaction


class BaseSeeder(ABC):
    """Abstract base class for all seeders.

    Provides common interface and utilities for seeding data.
    Each subclass should implement the `seed()` method.

    **Tenant Seeder Pattern:**
    The system uses a multi-tenancy model where all data must be associated with a Tenant.
    The TenantSeeder runs first to create or retrieve the default tenant, and its instance
    is passed to all downstream seeders. Downstream seeders should accept tenant as a
    parameter and use it when creating data models.

    Example::

        # TenantSeeder creates/retrieves default tenant
        tenant_seeder = TenantSeeder(verbose=True)
        tenant = tenant_seeder.execute()  # Returns Tenant instance

        # Other seeders receive tenant and use it
        product_seeder = ProductSeeder(verbose=True)
        product_seeder.execute(tenant=tenant)

    All data models inherit from TimeStampedModel which includes a tenant FK,
    ensuring data isolation at the database level.
    """

    def __init__(self, verbose=True):
        """Initialize the seeder.

        Args:
            verbose: If True, print progress messages to stdout.
        """
        self.verbose = verbose
        self.tenant = None

    def log(self, message):
        """Print a message if verbose mode is enabled."""
        if self.verbose:
            print(f"  {message}")

    @abstractmethod
    def seed(self):
        """Seed the model with sample data.

        Subclasses must implement this method.
        """
        pass

    def execute(self, tenant=None):
        """Execute the seeder within a transaction.

        Args:
            tenant: The tenant instance to associate with seeded data.
                   If None, raises an error when helpers are called.

        Ensures atomicity: either all data is created or none.
        """
        self.tenant = tenant
        try:
            with transaction.atomic():
                self.seed()
                if self.verbose:
                    self.log("✓ Complete")
        except Exception as e:
            if self.verbose:
                self.log(f"✗ Failed: {str(e)}")
            raise

    def create_with_tenant(self, model, **kwargs):
        """Create a model instance with tenant assignment.

        Args:
            model: The model class to instantiate.
            **kwargs: Fields to set on the model.

        Returns:
            The created model instance.

        Raises:
            ValueError: If tenant is None.
        """
        if self.tenant is None:
            raise ValueError(
                f"Cannot create {model.__name__} without a tenant. "
                "Ensure tenant is passed to execute()."
            )
        kwargs["tenant"] = self.tenant
        return model.objects.create(**kwargs)

    def add_root_with_tenant(self, model, **kwargs):
        """Create a root node in a treebeard model with tenant assignment.

        Used for models that inherit from treebeard (e.g., Category, StockLocation).

        Args:
            model: The treebeard model class to instantiate.
            **kwargs: Fields to set on the model.

        Returns:
            The created root model instance.

        Raises:
            ValueError: If tenant is None.
        """
        if self.tenant is None:
            raise ValueError(
                f"Cannot create root {model.__name__} without a tenant. "
                "Ensure tenant is passed to execute()."
            )
        kwargs["tenant"] = self.tenant
        return model.add_root(**kwargs)
