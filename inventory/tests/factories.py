"""Shared test data factories for the inventory app.

Provides convenience functions to create common test objects with
sensible defaults, reducing boilerplate across test modules.

All factory functions accept ``**kwargs`` so tests can override any
field when needed.
"""

from decimal import Decimal

from django.contrib.auth import get_user_model

from inventory.models import (
    Category,
    MovementType,
    Product,
    StockLocation,
    StockMovement,
    StockRecord,
    UnitOfMeasure,
)

User = get_user_model()


def create_user(*, username="testuser", password="testpass123", **kwargs):
    """Create and return a Django user."""
    defaults = {
        "username": username,
        "password": password,
        "is_staff": True,
    }
    defaults.update(kwargs)
    password = defaults.pop("password")
    user = User.objects.create_user(password=password, **defaults)
    return user


def create_admin_user(*, username="admin", password="adminpass123", **kwargs):
    """Create and return a Django superuser."""
    defaults = {
        "username": username,
        "password": password,
        "email": "admin@example.com",
    }
    defaults.update(kwargs)
    password = defaults.pop("password")
    user = User.objects.create_superuser(password=password, **defaults)
    return user


def create_category(*, name="Test Category", slug="test-category", **kwargs):
    """Create and return a root Category node."""
    defaults = {
        "name": name,
        "slug": slug,
        "is_active": True,
    }
    defaults.update(kwargs)
    return Category.add_root(**defaults)


def create_product(*, sku="TEST-001", name="Test Product", category=None, **kwargs):
    """Create and return a Product with sensible defaults."""
    defaults = {
        "sku": sku,
        "name": name,
        "category": category,
        "unit_of_measure": UnitOfMeasure.PIECES,
        "unit_cost": Decimal("10.00"),
        "reorder_point": 5,
        "is_active": True,
    }
    defaults.update(kwargs)
    return Product.objects.create(**defaults)


def create_location(*, name="Main Warehouse", **kwargs):
    """Create and return a root StockLocation node."""
    defaults = {
        "name": name,
        "is_active": True,
    }
    defaults.update(kwargs)
    return StockLocation.add_root(**defaults)


def create_stock_record(*, product, location, quantity=0, **kwargs):
    """Create and return a StockRecord."""
    defaults = {
        "product": product,
        "location": location,
        "quantity": quantity,
    }
    defaults.update(kwargs)
    return StockRecord.objects.create(**defaults)


def create_stock_movement(
    *,
    product,
    movement_type=MovementType.RECEIVE,
    quantity=10,
    from_location=None,
    to_location=None,
    **kwargs,
):
    """Create and return a StockMovement (bypasses service layer).

    Use this only when you need a raw movement record without
    processing side-effects.  For integration tests, prefer
    :meth:`StockService.process_movement`.
    """
    defaults = {
        "product": product,
        "movement_type": movement_type,
        "quantity": quantity,
        "from_location": from_location,
        "to_location": to_location,
    }
    defaults.update(kwargs)
    return StockMovement.objects.create(**defaults)
