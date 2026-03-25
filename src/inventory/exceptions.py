"""Domain exception hierarchy for the inventory module.

These exceptions allow callers to react to specific business-rule
violations without parsing error message strings.  All domain
exceptions inherit from :class:`InventoryError`, so a single
``except InventoryError`` still catches everything inventory-related.
"""


class InventoryError(Exception):
    """Base for all inventory domain errors."""


class InsufficientStockError(InventoryError):
    """Raised when a movement would cause negative stock."""


class LocationHierarchyError(InventoryError):
    """Raised for invalid location tree operations."""


class ReservationConflictError(InventoryError):
    """Raised when reserved stock cannot be allocated."""


class MovementImmutableError(InventoryError):
    """Raised when attempting to update an existing movement."""


class TenantLimitExceededError(InventoryError):
    """Raised when a tenant exceeds subscription limits."""


class LocationCapacityExceededError(InventoryError):
    """Raised when a movement would exceed a location's max capacity."""


class LotTrackingRequiredError(InventoryError):
    """Raised when a product requires lot info but none was provided."""


class MovementWarehouseScopeError(InventoryError):
    """Raised when a movement mixes facility-linked and retail-only locations."""
