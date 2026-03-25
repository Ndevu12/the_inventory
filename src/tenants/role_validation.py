"""Validate tenant membership / invitation role strings (legacy ``admin`` rejected)."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

LEGACY_TENANT_ROLE_ADMIN = "admin"


def ensure_valid_tenant_role(value: str) -> None:
    """Raise ValidationError if *value* is not a current :class:`~tenants.models.TenantRole`.

    The historical role key ``admin`` is rejected with an explicit message because it was
    renamed to ``coordinator`` — :class:`~django.db.models.CharField` choices are not
    enforced on :meth:`~django.db.models.Model.save`.
    """
    # Late import so tenants.models can depend on this module without a cycle.
    from tenants.models import TenantRole

    if not value:
        raise ValidationError(_("This field may not be blank."), code="blank")

    if value == LEGACY_TENANT_ROLE_ADMIN:
        raise ValidationError(
            _(
                'The tenant role "admin" was renamed to "coordinator". '
                'Use "coordinator" for organization governance.'
            ),
            code="legacy_admin_role",
        )

    valid = {item.value for item in TenantRole}
    if value not in valid:
        raise ValidationError(
            _("Select a valid tenant role."),
            code="invalid_role",
        )
