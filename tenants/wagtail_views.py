"""Wagtail admin views for tenant oversight (SA-02).

Provides custom action views for platform superusers to force-deactivate
or reactivate tenants. All actions are audited and restricted to
is_superuser.
"""

from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View

from django.contrib.auth import get_user_model
from wagtail.admin import messages
from wagtail.admin.utils import get_valid_next_url_from_request
from wagtail.snippets.views.snippets import CreateView as SnippetCreateView
from wagtail.snippets.views.snippets import EditView as SnippetEditView

from inventory.models.audit import AuditAction
from inventory.services.audit import AuditService
from tenants.models import Tenant, TenantMembership
from tenants.wagtail_forms import TenantCreateForm

User = get_user_model()


def _superuser_required(user):
    """Require platform superuser for tenant oversight actions."""
    return user.is_authenticated and user.is_superuser


def _get_tenant_edit_url(tenant):
    """Return the edit URL for a tenant using its snippet viewset."""
    viewset = getattr(Tenant, "snippet_viewset", None)
    if viewset:
        return reverse(viewset.get_url_name("edit"), args=[tenant.pk])
    return reverse("wagtailsnippets:index")


@method_decorator(user_passes_test(_superuser_required), name="dispatch")
class TenantDeactivateView(View):
    """Force-deactivate a tenant (platform superuser only)."""

    template_name = "tenants/admin/confirm_deactivate.html"

    def get(self, request, pk):
        tenant = get_object_or_404(Tenant, pk=pk)
        if not tenant.is_active:
            return redirect(_get_tenant_edit_url(tenant))
        return TemplateResponse(
            request,
            self.template_name,
            {
                "tenant": tenant,
                "action_url": request.path,
                "cancel_url": _get_tenant_edit_url(tenant),
                "page_title": _("Deactivate tenant"),
                "header_title": _("Deactivate tenant"),
                "header_icon": "warning",
            },
        )

    def post(self, request, pk):
        tenant = get_object_or_404(Tenant, pk=pk)
        if not tenant.is_active:
            return redirect(self._next_url(request, tenant))

        tenant.is_active = False
        tenant.save(update_fields=["is_active"])

        AuditService().log(
            tenant=tenant,
            action=AuditAction.TENANT_DEACTIVATED,
            user=request.user,
            ip_address=AuditService._get_client_ip(request),
            details={"reason": "Platform admin force-deactivation"},
        )


        messages.success(
            request,
            _("Tenant '%(name)s' has been deactivated.") % {"name": tenant.name},
        )
        return redirect(self._next_url(request, tenant))

    def _next_url(self, request, tenant):

        next_url = get_valid_next_url_from_request(request)
        if next_url:
            return next_url
        return _get_tenant_edit_url(tenant)


@method_decorator(user_passes_test(_superuser_required), name="dispatch")
class TenantReactivateView(View):
    """Reactivate a deactivated tenant (platform superuser only)."""

    template_name = "tenants/admin/confirm_reactivate.html"

    def get(self, request, pk):
        tenant = get_object_or_404(Tenant, pk=pk)
        if tenant.is_active:
            return redirect(_get_tenant_edit_url(tenant))
        return TemplateResponse(
            request,
            self.template_name,
            {
                "tenant": tenant,
                "action_url": request.path,
                "cancel_url": _get_tenant_edit_url(tenant),
                "page_title": _("Reactivate tenant"),
                "header_title": _("Reactivate tenant"),
                "header_icon": "view",
            },
        )

    def post(self, request, pk):
        tenant = get_object_or_404(Tenant, pk=pk)
        if tenant.is_active:
            return redirect(self._next_url(request, tenant))

        tenant.is_active = True
        tenant.save(update_fields=["is_active"])

        AuditService().log(
            tenant=tenant,
            action=AuditAction.TENANT_REACTIVATED,
            user=request.user,
            ip_address=AuditService._get_client_ip(request),
            details={"reason": "Platform admin reactivation"},
        )

        messages.success(
            request,
            _("Tenant '%(name)s' has been reactivated.") % {"name": tenant.name},
        )
        return redirect(self._next_url(request, tenant))

    def _next_url(self, request, tenant):

        next_url = get_valid_next_url_from_request(request)
        if next_url:
            return next_url
        return _get_tenant_edit_url(tenant)


class TenantCreateView(SnippetCreateView):
    """Custom create view for Tenant with owner selection (SA-09)."""

    form_class = TenantCreateForm

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form._invited_by = self.request.user if self.request.user.is_authenticated else None
        return form

    def get_success_url(self):
        """Redirect to tenant edit view with Members inline."""
        return _get_tenant_edit_url(self.object)


class TenantEditView(SnippetEditView):
    """Custom edit view that audits limit overrides when changed by superusers."""

    def form_valid(self, form):
        # Capture old override values before save (only when editing existing tenant)
        old_users = old_products = None
        if form.instance.pk and self.request.user.is_superuser:
            try:
                old = Tenant.objects.get(pk=form.instance.pk)
                old_users = old.max_users_override
                old_products = old.max_products_override
            except Tenant.DoesNotExist:
                pass

        response = super().form_valid(form)

        # Audit if limit overrides were changed (superuser only)
        if (
            old_users is not None
            and self.request.user.is_superuser
            and (
                form.instance.max_users_override != old_users
                or form.instance.max_products_override != old_products
            )
        ):
            AuditService().log(
                tenant=form.instance,
                action=AuditAction.TENANT_LIMIT_OVERRIDDEN,
                user=self.request.user,
                ip_address=AuditService._get_client_ip(self.request),
                details={
                    "max_users_override": form.instance.max_users_override,
                    "max_products_override": form.instance.max_products_override,
                },
            )
        return response


@method_decorator(user_passes_test(_superuser_required), name="dispatch")
class ImpersonateStartView(View):
    """Start impersonating a user (Wagtail session). Sets session and redirects to admin home."""

    def get(self, request, user_id):

        User = get_user_model()
        target = get_object_or_404(User, pk=user_id, is_active=True)
        if target.pk == request.user.pk:

            messages.warning(request, _("You cannot impersonate yourself."))
            return redirect("wagtailadmin_home")
        request.session["_impersonating_user_id"] = target.pk
        membership = (
            TenantMembership.objects.filter(user=target, is_active=True)
            .select_related("tenant")
            .order_by("-is_default", "pk")
            .first()
        )
        audit_tenant = membership.tenant if membership else Tenant.objects.filter(is_active=True).first()
        if audit_tenant:
            AuditService().log(
                tenant=audit_tenant,
                action=AuditAction.IMPERSONATION_STARTED,
                user=request.user,
                ip_address=AuditService._get_client_ip(request),
                details={"impersonated_user_id": target.pk, "impersonated_username": target.username},
            )
        messages.success(request, _("Now viewing as %(user)s.") % {"user": target.get_full_name() or target.username})
        return redirect("wagtailadmin_home")


@method_decorator(user_passes_test(_superuser_required), name="dispatch")
class ImpersonateEndView(View):
    """End impersonation. Clears session and redirects to admin home."""

    def get(self, request):
        imp_id = request.session.pop("_impersonating_user_id", None)
        if imp_id:
            User = get_user_model()
            try:
                imp_user = User.objects.get(pk=imp_id)
                membership = (
                    TenantMembership.objects.filter(user=imp_user, is_active=True)
                    .select_related("tenant")
                    .first()
                )
                audit_tenant = membership.tenant if membership else Tenant.objects.filter(is_active=True).first()
                if audit_tenant:
                    AuditService().log(
                        tenant=audit_tenant,
                        action=AuditAction.IMPERSONATION_ENDED,
                        user=request.user,
                        ip_address=AuditService._get_client_ip(request),
                        details={"impersonated_user_id": imp_user.pk, "impersonated_username": imp_user.username},
                    )
            except User.DoesNotExist:
                pass

            messages.success(request, _("Impersonation ended."))
        return redirect("wagtailadmin_home")

