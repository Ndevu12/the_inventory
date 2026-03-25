"""Wagtail admin: cross-tenant, read-only compliance audit log for platform operators."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db.models import Q
from django.urls import path
from django.utils.translation import gettext_lazy as _
from wagtail.admin.ui.tables import Column
from wagtail.permission_policies.base import BasePermissionPolicy
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from inventory.audit_display import build_audit_summary, event_scope_for_action
from inventory.models import ComplianceAuditLog


def _audit_summary_cell(obj):
    return build_audit_summary(obj)


def _action_label(obj):
    return obj.get_action_display()


def _event_scope_cell(obj):
    return event_scope_for_action(obj.action)


class PlatformAuditLogPermissionPolicy(BasePermissionPolicy):
    """Who may open the snippet mirrors Wagtail admin access; the log is immutable (no add/change/delete).

    REST parity: :class:`~api.permissions.IsPlatformAuditAPIAccess` on ``PlatformAuditLogViewSet``.
    """

    _access_admin = "wagtailadmin.access_admin"

    def user_has_permission(self, user, action):
        if not getattr(user, "is_authenticated", False) or not user.is_active:
            return False
        if action == "view":
            return bool(user.is_superuser or user.has_perm(self._access_admin))
        return False

    def user_has_any_permission(self, user, actions):
        return any(self.user_has_permission(user, action) for action in actions)

    def users_with_any_permission(self, actions):
        User = get_user_model()
        if "view" not in frozenset(actions):
            return User.objects.none()
        # Match ``wagtail.admin.auth.require_admin_access`` (superuser or access_admin).
        admin_perm = Permission.objects.get(
            content_type__app_label="wagtailadmin",
            codename="access_admin",
        )
        return (
            User.objects.filter(is_active=True)
            .filter(
                Q(is_superuser=True)
                | Q(user_permissions=admin_perm)
                | Q(groups__permissions=admin_perm)
            )
            .distinct()
        )


class PlatformAuditLogSnippetViewSet(SnippetViewSet):
    model = ComplianceAuditLog
    icon = "history"
    menu_label = _("Platform audit log")
    menu_name = "platform-audit-log"
    menu_order = 110
    add_to_admin_menu = True

    add_to_reference_index = False
    inspect_view_enabled = True
    copy_view_enabled = False

    inspect_view_fields = [
        "id",
        "timestamp",
        "tenant",
        "action",
        "event_scope",
        "user",
        "ip_address",
        "product",
        "details",
    ]

    list_display = [
        "timestamp",
        "tenant",
        Column("action", label=_("Action"), accessor=_action_label, sort_key="action"),
        Column(
            "event_scope",
            label=_("Scope"),
            accessor=_event_scope_cell,
            sort_key="action",
        ),
        Column("summary", label=_("Summary"), accessor=_audit_summary_cell),
        "user",
        "ip_address",
    ]
    list_filter = ["tenant", "action", "timestamp"]
    search_fields = ["user__username", "product__sku", "action"]
    ordering = ["-timestamp"]

    @property
    def permission_policy(self):
        return PlatformAuditLogPermissionPolicy(self.model)

    def register_chooser_viewset(self):
        return

    def get_urlpatterns(self):
        conv = self.pk_path_converter
        return [
            path("", self.index_view, name="list"),
            path("results/", self.index_results_view, name="list_results"),
            path(f"inspect/<{conv}:pk>/", self.inspect_view, name="inspect"),
        ]

    def get_queryset(self, request):
        return (
            ComplianceAuditLog.objects.all()
            .select_related("tenant", "user", "product")
            .order_by("-timestamp")
        )


register_snippet(PlatformAuditLogSnippetViewSet)
