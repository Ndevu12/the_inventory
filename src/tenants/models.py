"""Multi-tenancy models.

The ``Tenant`` model is the organizational root — every other data model
in the system is scoped to a tenant via the FK on ``TimeStampedModel``.

``TenantMembership`` links users to tenants and assigns a role that
drives RBAC permission checks throughout the application.

``TenantInvitation`` represents a pending invitation for a new user to
join a tenant.  It carries a unique token used in the accept-invitation
flow.

These models do NOT inherit from ``TimeStampedModel`` (which carries a
tenant FK itself) to avoid a circular dependency.
"""

import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import (
    FieldPanel,
    FieldRowPanel,
    InlinePanel,
    ObjectList,
    TabbedInterface,
)
from wagtail.search import index

from tenants.enums import InvitationStatus, SubscriptionPlan, SubscriptionStatus, TenantRole
from tenants.wagtail_locales import wagtail_locale_choices


# ---------------------------------------------------------------------------
# Tenant
# ---------------------------------------------------------------------------


class Tenant(ClusterableModel, index.Indexed, models.Model):
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
    preferred_language = models.CharField(
        max_length=32,
        default="en",
        choices=wagtail_locale_choices,
        help_text=(
            "Default locale for this tenant (admin strings, API fallbacks). "
            "Options match Wagtail Settings → Locales."
        ),
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
    max_users_override = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Platform override: temporarily increase user limit. Leave blank to use plan default.",
    )
    max_products_override = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Platform override: temporarily increase product limit. Leave blank to use plan default.",
    )
    billing_notes = models.TextField(
        blank=True,
        help_text="Optional notes for billing support (e.g., payment issues, custom arrangements).",
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
                FieldPanel("preferred_language"),
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
                FieldRowPanel([
                    FieldPanel("max_users_override", classname="col6"),
                    FieldPanel("max_products_override", classname="col6"),
                ]),
                FieldPanel("billing_notes"),
            ],
            heading="Subscription",
        ),
        ObjectList(
            [
                InlinePanel("memberships", label="Members", min_num=0),
            ],
            heading="Members",
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

    def effective_max_users(self):
        """Return the effective user limit (override if set, else plan default)."""
        if self.max_users_override is not None:
            return self.max_users_override
        return self.max_users

    def is_within_user_limit(self):
        return self.user_count() < self.effective_max_users()

    def product_count(self):
        from inventory.models import Product
        return Product.objects.filter(tenant=self, is_active=True).count()

    def effective_max_products(self):
        """Return the effective product limit (override if set, else plan default)."""
        if self.max_products_override is not None:
            return self.max_products_override
        return self.max_products

    def is_within_product_limit(self):
        return self.product_count() < self.effective_max_products()

    def usage_summary(self):
        """Return a short summary of usage vs limits for display in admin lists."""
        users = self.user_count()
        products = self.product_count()
        max_u = self.effective_max_users()
        max_p = self.effective_max_products()
        return f"{users}/{max_u} users, {products}/{max_p} products"


# ---------------------------------------------------------------------------
# TenantMembership
# ---------------------------------------------------------------------------


class TenantMembership(models.Model):
    """Links a user to a tenant with a specific role.

    A user may belong to multiple tenants (each with a separate role).
    The ``is_default`` flag indicates which tenant is loaded on login.
    """

    tenant = ParentalKey(
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
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    role__in=[
                        TenantRole.OWNER,
                        TenantRole.COORDINATOR,
                        TenantRole.MANAGER,
                        TenantRole.VIEWER,
                    ],
                ),
                name="tenants_tenantmembership_role_allowed",
            ),
        ]

    def __str__(self):
        return f"{self.user} → {self.tenant.name} ({self.get_role_display()})"

    def clean(self):
        super().clean()
        from tenants.role_validation import ensure_valid_tenant_role

        ensure_valid_tenant_role(self.role)

    def save(self, *args, **kwargs):
        # Enforce choices (Django does not validate CharField.choices on save).
        self.full_clean()
        super().save(*args, **kwargs)

    # -- RBAC helpers ------------------------------------------------------

    @property
    def can_manage(self):
        """Owner, coordinator, or manager — can create/edit data."""
        return self.role in {
            TenantRole.OWNER,
            TenantRole.COORDINATOR,
            TenantRole.MANAGER,
        }

    @property
    def can_manage_organization(self):
        """Owner or coordinator — can manage members and organization settings."""
        return self.role in {TenantRole.OWNER, TenantRole.COORDINATOR}

    @property
    def is_owner(self):
        return self.role == TenantRole.OWNER


# ---------------------------------------------------------------------------
# TenantInvitation
# ---------------------------------------------------------------------------

INVITATION_EXPIRY_DAYS = 7


def _make_token():
    return secrets.token_urlsafe(48)


class TenantInvitation(models.Model):
    """A pending invitation for someone to join a tenant.

    The workflow:
      1. An owner or coordinator creates an invitation (email + role).
      2. The system generates a unique token and (optionally) sends an email.
      3. The invitee visits the accept-invitation URL with the token.
      4. If the invitee has no account, one is created; a TenantMembership
         is created linking them to the tenant.
    """

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    email = models.EmailField(
        help_text="Email address of the person being invited.",
    )
    role = models.CharField(
        max_length=20,
        choices=TenantRole.choices,
        default=TenantRole.VIEWER,
    )
    token = models.CharField(
        max_length=128,
        unique=True,
        default=_make_token,
        editable=False,
    )
    status = models.CharField(
        max_length=20,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING,
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    role__in=[
                        TenantRole.OWNER,
                        TenantRole.COORDINATOR,
                        TenantRole.MANAGER,
                        TenantRole.VIEWER,
                    ],
                ),
                name="tenants_tenantinvitation_role_allowed",
            ),
        ]

    def __str__(self):
        return f"Invite {self.email} → {self.tenant.name} ({self.get_status_display()})"

    def clean(self):
        super().clean()
        from tenants.role_validation import ensure_valid_tenant_role

        ensure_valid_tenant_role(self.role)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(
                days=INVITATION_EXPIRY_DAYS
            )
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_pending(self):
        if self.status != InvitationStatus.PENDING:
            return False
        if self.is_expired:
            self.status = InvitationStatus.EXPIRED
            self.save(update_fields=["status"])
            return False
        return True
