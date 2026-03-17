"""Multi-tenancy models.

The ``Tenant`` model is the organizational root — every other data model
in the system is scoped to a tenant via the FK on ``TimeStampedModel``.

``TenantMembership`` links users to tenants and assigns a role that
drives RBAC permission checks throughout the application.

These models do NOT inherit from ``TimeStampedModel`` (which carries a
tenant FK itself) to avoid a circular dependency.
"""

from django.conf import settings
from django.db import models
from wagtail.admin.panels import (
    FieldPanel,
    FieldRowPanel,
    MultiFieldPanel,
    ObjectList,
    TabbedInterface,
)
from wagtail.search import index


# ---------------------------------------------------------------------------
# Choices
# ---------------------------------------------------------------------------


class TenantRole(models.TextChoices):
    OWNER = "owner", "Owner"
    ADMIN = "admin", "Admin"
    MANAGER = "manager", "Manager"
    VIEWER = "viewer", "Viewer"


class SubscriptionPlan(models.TextChoices):
    FREE = "free", "Free"
    STARTER = "starter", "Starter"
    PROFESSIONAL = "professional", "Professional"
    ENTERPRISE = "enterprise", "Enterprise"


class SubscriptionStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    TRIAL = "trial", "Trial"
    PAST_DUE = "past_due", "Past Due"
    CANCELLED = "cancelled", "Cancelled"
    SUSPENDED = "suspended", "Suspended"


# ---------------------------------------------------------------------------
# Tenant
# ---------------------------------------------------------------------------


class Tenant(index.Indexed, models.Model):
    """An organization that owns a self-contained data silo.

    All inventory, procurement, and sales data is scoped to a tenant.
    The model also holds branding overrides and subscription metadata.
    """

    name = models.CharField(
        max_length=255,
        help_text="Organization or company name.",
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text="URL-safe identifier (e.g., 'acme-corp'). Must be unique.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive tenants cannot log in or access data.",
    )

    # -- Branding ----------------------------------------------------------

    branding_site_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Custom site name shown in the admin header. Falls back to tenant name.",
    )
    branding_primary_color = models.CharField(
        max_length=7,
        blank=True,
        help_text="Hex color code for primary brand color (e.g., '#3B82F6').",
    )
    branding_logo = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text="Custom logo displayed in the admin header.",
    )

    # -- Subscription / Billing hooks --------------------------------------

    subscription_plan = models.CharField(
        max_length=20,
        choices=SubscriptionPlan.choices,
        default=SubscriptionPlan.FREE,
    )
    subscription_status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.ACTIVE,
    )
    max_users = models.PositiveIntegerField(
        default=5,
        help_text="Maximum number of users allowed under the current plan.",
    )
    max_products = models.PositiveIntegerField(
        default=100,
        help_text="Maximum number of active products allowed.",
    )

    # -- Audit -------------------------------------------------------------

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    edit_handler = TabbedInterface([
        ObjectList(
            [
                FieldRowPanel([
                    FieldPanel("name", classname="col6"),
                    FieldPanel("slug", classname="col6"),
                ]),
                FieldPanel("is_active"),
            ],
            heading="Identity",
        ),
        ObjectList(
            [
                FieldPanel("branding_site_name"),
                FieldRowPanel([
                    FieldPanel("branding_primary_color", classname="col6"),
                    FieldPanel("branding_logo", classname="col6"),
                ]),
            ],
            heading="Branding",
        ),
        ObjectList(
            [
                FieldRowPanel([
                    FieldPanel("subscription_plan", classname="col6"),
                    FieldPanel("subscription_status", classname="col6"),
                ]),
                FieldRowPanel([
                    FieldPanel("max_users", classname="col6"),
                    FieldPanel("max_products", classname="col6"),
                ]),
            ],
            heading="Subscription",
        ),
    ])

    search_fields = [
        index.SearchField("name"),
        index.SearchField("slug"),
        index.FilterField("is_active"),
    ]

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def display_name(self):
        """Return branding name or fall back to tenant name."""
        return self.branding_site_name or self.name

    def user_count(self):
        return self.memberships.filter(is_active=True).count()

    def is_within_user_limit(self):
        return self.user_count() < self.max_users

    def product_count(self):
        from inventory.models import Product
        return Product.objects.filter(tenant=self, is_active=True).count()

    def is_within_product_limit(self):
        return self.product_count() < self.max_products


# ---------------------------------------------------------------------------
# TenantMembership
# ---------------------------------------------------------------------------


class TenantMembership(models.Model):
    """Links a user to a tenant with a specific role.

    A user may belong to multiple tenants (each with a separate role).
    The ``is_default`` flag indicates which tenant is loaded on login.
    """

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tenant_memberships",
    )
    role = models.CharField(
        max_length=20,
        choices=TenantRole.choices,
        default=TenantRole.VIEWER,
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive memberships are preserved for audit but deny access.",
    )
    is_default = models.BooleanField(
        default=False,
        help_text="If True, this tenant is loaded automatically on login.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("tenant", "user")
        ordering = ["-is_default", "tenant__name"]

    def __str__(self):
        return f"{self.user} → {self.tenant.name} ({self.get_role_display()})"

    # -- RBAC helpers ------------------------------------------------------

    @property
    def can_manage(self):
        """Owner, admin, or manager — can create/edit data."""
        return self.role in {
            TenantRole.OWNER,
            TenantRole.ADMIN,
            TenantRole.MANAGER,
        }

    @property
    def can_admin(self):
        """Owner or admin — can manage users and settings."""
        return self.role in {TenantRole.OWNER, TenantRole.ADMIN}

    @property
    def is_owner(self):
        return self.role == TenantRole.OWNER
