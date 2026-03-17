from django.conf import settings
from django.db import models
from wagtail.search import index


class TimeStampedModel(index.Indexed, models.Model):
    """Audit fields inherited by all domain models.

    Provides audit timestamps, an optional ``created_by`` user link,
    and a **tenant** foreign key that scopes data to a single
    organization in a multi-tenant deployment.

    The ``tenant`` field is nullable during migration; the
    ``TenantMiddleware`` and ``TenantAwareManager`` enforce
    tenant-scoping at runtime.
    """

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_set",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created",
    )

    class Meta:
        abstract = True
