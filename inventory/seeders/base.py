"""Base seeder class providing common functionality for all seeders."""

from abc import ABC, abstractmethod
from django.db import transaction


class BaseSeeder(ABC):
    """Abstract base class for all seeders.

    Provides common interface and utilities for seeding data.
    Each subclass should implement the `seed()` method.
    """

    def __init__(self, verbose=True):
        """Initialize the seeder.

        Args:
            verbose: If True, print progress messages to stdout.
        """
        self.verbose = verbose

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

    def execute(self):
        """Execute the seeder within a transaction.

        Ensures atomicity: either all data is created or none.
        """
        try:
            with transaction.atomic():
                self.seed()
                if self.verbose:
                    self.log("✓ Complete")
        except Exception as e:
            if self.verbose:
                self.log(f"✗ Failed: {str(e)}")
            raise
