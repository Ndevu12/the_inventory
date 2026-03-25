"""Tenant domain choice enums (subscription, roles, invitations)."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class TenantRole(models.TextChoices):
    OWNER = "owner", _("Owner")
    COORDINATOR = "coordinator", _("Coordinator")
    MANAGER = "manager", _("Manager")
    VIEWER = "viewer", _("Viewer")


class SubscriptionPlan(models.TextChoices):
    FREE = "free", _("Free")
    STARTER = "starter", _("Starter")
    PROFESSIONAL = "professional", _("Professional")
    ENTERPRISE = "enterprise", _("Enterprise")


class SubscriptionStatus(models.TextChoices):
    ACTIVE = "active", _("Active")
    TRIAL = "trial", _("Trial")
    PAST_DUE = "past_due", _("Past Due")
    CANCELLED = "cancelled", _("Cancelled")
    SUSPENDED = "suspended", _("Suspended")


class InvitationStatus(models.TextChoices):
    PENDING = "pending", _("Pending")
    ACCEPTED = "accepted", _("Accepted")
    CANCELLED = "cancelled", _("Cancelled")
    EXPIRED = "expired", _("Expired")
