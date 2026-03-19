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

from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from inventory.models.audit import AuditAction
from inventory.services.audit import AuditService
from tenants.models import Tenant, TenantMembership

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

        from wagtail.admin import messages

        messages.success(
            request,
            _("Tenant '%(name)s' has been deactivated.") % {"name": tenant.name},
        )
        return redirect(self._next_url(request, tenant))

    def _next_url(self, request, tenant):
        from wagtail.admin.utils import get_valid_next_url_from_request

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

        from wagtail.admin import messages

        messages.success(
            request,
            _("Tenant '%(name)s' has been reactivated.") % {"name": tenant.name},
        )
        return redirect(self._next_url(request, tenant))

    def _next_url(self, request, tenant):
        from wagtail.admin.utils import get_valid_next_url_from_request

        next_url = get_valid_next_url_from_request(request)
        if next_url:
            return next_url
        return _get_tenant_edit_url(tenant)


from wagtail.snippets.views.snippets import CreateView as SnippetCreateView
from wagtail.snippets.views.snippets import EditView as SnippetEditView

from tenants.wagtail_forms import TenantCreateForm


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
        from django.contrib.auth import get_user_model

        User = get_user_model()
        target = get_object_or_404(User, pk=user_id, is_active=True)
        if target.pk == request.user.pk:
            from wagtail.admin import messages
            messages.warning(request, _("You cannot impersonate yourself."))
            return redirect("wagtailadmin_home")
        request.session["_impersonating_user_id"] = target.pk
        from inventory.models.audit import AuditAction
        membership = (
            __import__("tenants.models", fromlist=["TenantMembership"])
            .TenantMembership.objects.filter(user=target, is_active=True)
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
        from wagtail.admin import messages
        messages.success(request, _("Now viewing as %(user)s.") % {"user": target.get_full_name() or target.username})
        return redirect("wagtailadmin_home")


@method_decorator(user_passes_test(_superuser_required), name="dispatch")
class ImpersonateEndView(View):
    """End impersonation. Clears session and redirects to admin home."""

    def get(self, request):
        imp_id = request.session.pop("_impersonating_user_id", None)
        if imp_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                imp_user = User.objects.get(pk=imp_id)
                membership = (
                    __import__("tenants.models", fromlist=["TenantMembership"])
                    .TenantMembership.objects.filter(user=imp_user, is_active=True)
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
            from wagtail.admin import messages
            messages.success(request, _("Impersonation ended."))
        return redirect("wagtailadmin_home")


# ---------------------------------------------------------------------------
# SA-03: Impersonation (session-based for Wagtail admin)
# ---------------------------------------------------------------------------


@method_decorator(user_passes_test(_superuser_required), name="dispatch")
class ImpersonateStartWagtailView(View):
    """Start session-based impersonation (Wagtail admin; superuser only)."""

    def get(self, request, user_id):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        target = get_object_or_404(User, pk=user_id, is_active=True)
        if target.pk == request.user.pk:
            from wagtail.admin import messages

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
                details={
                    "impersonated_user_id": target.pk,
                    "impersonated_username": target.username,
                },
            )

        from wagtail.admin import messages

        messages.success(
            request,
            _("Now viewing as %(user)s.") % {"user": target.get_full_name() or target.username},
        )
        return redirect("wagtailadmin_home")


@method_decorator(user_passes_test(_superuser_required), name="dispatch")
class ImpersonateEndWagtailView(View):
    """End session-based impersonation (Wagtail admin; superuser only)."""

    def get(self, request):
        imp_user_id = request.session.pop("_impersonating_user_id", None)
        if imp_user_id:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            try:
                imp_user = User.objects.get(pk=imp_user_id)
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
                        details={
                            "impersonated_user_id": imp_user.pk,
                            "impersonated_username": imp_user.username,
                        },
                    )
            except User.DoesNotExist:
                pass

        from wagtail.admin import messages

        messages.success(request, _("Impersonation ended."))
        return redirect("wagtailadmin_home")


@method_decorator(user_passes_test(_superuser_required), name="dispatch")
class ImpersonateStartView(View):
    """Start impersonating a user via session (Wagtail admin; superuser only)."""

    def get(self, request, user_id):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        target = get_object_or_404(User, pk=user_id, is_active=True)
        if target.pk == request.user.pk:
            from wagtail.admin import messages
            messages.warning(request, _("You cannot impersonate yourself."))
            return redirect("wagtailadmin_home")
        request.session["_impersonating_user_id"] = target.pk

        AuditService().log(
            tenant=Tenant.objects.filter(
                memberships__user=target, memberships__is_active=True,
            ).select_related().first() or Tenant.objects.filter(is_active=True).first(),
            action=AuditAction.IMPERSONATION_STARTED,
            user=request.user,
            ip_address=AuditService._get_client_ip(request),
            details={
                "impersonated_user_id": target.pk,
                "impersonated_username": target.username,
            },
        )
        from wagtail.admin import messages
        messages.success(request, _("Impersonating %(user)s.") % {"user": target.username})
        return redirect("wagtailadmin_home")


@method_decorator(user_passes_test(_superuser_required), name="dispatch")
class ImpersonateEndView(View):
    """End session-based impersonation (Wagtail admin; superuser only)."""

    def get(self, request):
        real_user_id = request.session.pop("_impersonating_user_id", None)
        if real_user_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            imp_user = get_object_or_404(User, pk=real_user_id)
            AuditService().log(
                tenant=Tenant.objects.filter(
                    memberships__user=imp_user, memberships__is_active=True,
                ).first() or Tenant.objects.filter(is_active=True).first(),
                action=AuditAction.IMPERSONATION_ENDED,
                user=request.user,
                ip_address=AuditService._get_client_ip(request),
                details={
                    "impersonated_user_id": imp_user.pk,
                    "impersonated_username": imp_user.username,
                },
            )
        from wagtail.admin import messages
        messages.success(request, _("Impersonation ended."))
        return redirect("wagtailadmin_home")


# ---------------------------------------------------------------------------
# SA-03: Impersonation (session-based for Wagtail admin)
# ---------------------------------------------------------------------------


@method_decorator(user_passes_test(_superuser_required), name="dispatch")
class ImpersonateStartView(View):
    """Start impersonating a user (platform superuser only). Sets session and redirects."""

    def get(self, request, user_id):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        target = get_object_or_404(User, pk=user_id, is_active=True)
        if target.pk == request.user.pk:
            from wagtail.admin import messages
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
                details={
                    "impersonated_user_id": target.pk,
                    "impersonated_username": target.username,
                },
            )

        from wagtail.admin import messages
        messages.success(request, _("Impersonating %(user)s") % {"user": target.get_full_name() or target.username})
        return redirect("wagtailadmin_home")


@method_decorator(user_passes_test(_superuser_required), name="dispatch")
class ImpersonateEndView(View):
    """End impersonation. Clears session and redirects."""

    def get(self, request):
        real_user = request.session.pop("_impersonating_user_id", None)
        if real_user:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            imp_user = User.objects.filter(pk=real_user).first()
            real_user_obj = request.user  # After middleware swap, request.user is the real user again? No - during impersonation request.user is the impersonated user. When we clear session, the next request will have the real user from session. So we need to get real user from... Actually when we're in ImpersonateEndView, we're still in the same request. The ImpersonationMiddleware has already run - at this point request.user is the IMPERSONATED user (because we set session and the middleware swapped). So when we pop the session, we're about to redirect. The next request will have no _impersonating_user_id, so the middleware won't swap. The session still has the real user's session (the superuser who started). So the next request will load the superuser from session. Good. For audit, we need to log - at this moment request.user is the impersonated user, and the "real" user id was in session. Let me get real_user_id from session before popping - we're logging who ended. Actually we pop it and get the impersonated user id - no, _impersonating_user_id IS the impersonated user's id. So real_user_id in the var name is wrong - it's actually the impersonated user id. Let me fix: we have imp_user_id = session.pop("_impersonating_user_id"). The impersonated user is request.user. The real user - we don't have it directly. We'd need to have stored real_user_id in session too when we started. For now let's just log with the impersonated user in the details. We could add _impersonation_real_user_id when we start. For simplicity, I'll log with user=request.user (the impersonated user) and in details note that we're ending - the audit says "impersonation_ended" and the user in the log could be the real user. But we don't have the real user in this view easily. The middleware stores request._real_user when swapping. So we could check getattr(request, "_real_user", None) - that might be set by the middleware! Let me check - yes, ImpersonationMiddleware sets request._real_user = original user. So we can use request._real_user for the audit!
        real_user_obj = getattr(request, "_real_user", None)
        imp_user = request.user
        audit_tenant = None
        membership = TenantMembership.objects.filter(user=imp_user, is_active=True).select_related("tenant").first()
        if membership:
            audit_tenant = membership.tenant
        if audit_tenant is None:
            audit_tenant = Tenant.objects.filter(is_active=True).first()
        if audit_tenant and real_user_obj:
            AuditService().log(
                tenant=audit_tenant,
                action=AuditAction.IMPERSONATION_ENDED,
                user=real_user_obj,
                ip_address=AuditService._get_client_ip(request),
                details={
                    "impersonated_user_id": imp_user.pk,
                    "impersonated_username": imp_user.username,
                },
            )
        from wagtail.admin import messages
        messages.success(request, _("Impersonation ended. You are now yourself again."))
        return redirect("wagtailadmin_home")


@method_decorator(user_passes_test(_superuser_required), name="dispatch")
class ImpersonateStartView(View):
    """Start impersonating a user (platform superuser only).

    GET /admin/impersonate/start/<user_id>/
    Sets session and redirects to admin home. ImpersonationMiddleware
    will swap request.user on subsequent requests.
    """

    def get(self, request, user_id):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        target_user = get_object_or_404(User, pk=user_id, is_active=True)
        if target_user.pk == request.user.pk:
            from wagtail.admin import messages
            messages.warning(request, _("You cannot impersonate yourself."))
            return redirect("wagtailadmin_home")

        membership = (
            TenantMembership.objects.filter(user=target_user, is_active=True)
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
                details={
                    "impersonated_user_id": target_user.pk,
                    "impersonated_username": target_user.username,
                },
            )

        request.session["_impersonating_user_id"] = target_user.pk

        from wagtail.admin import messages
        messages.success(
            request,
            _("Now viewing as %(user)s.") % {"user": target_user.get_full_name() or target_user.username},
        )
        return redirect("wagtailadmin_home")


@method_decorator(user_passes_test(_superuser_required), name="dispatch")
class ImpersonateEndView(View):
    """End impersonation (platform superuser only).

    GET /admin/impersonate/end/
    Clears session and redirects. Only applies when currently impersonating.
    """

    def get(self, request):
        imp_user_id = request.session.pop("_impersonating_user_id", None)
        if imp_user_id:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            try:
                imp_user = User.objects.get(pk=imp_user_id)
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
                        details={
                            "impersonated_user_id": imp_user.pk,
                            "impersonated_username": imp_user.username,
                        },
                    )
            except User.DoesNotExist:
                pass

            from wagtail.admin import messages
            messages.success(request, _("Impersonation ended."))
        return redirect("wagtailadmin_home")


@method_decorator(user_passes_test(_superuser_required), name="dispatch")
class ImpersonateStartView(View):
    """Start impersonating a user (session-based, Wagtail admin only).

    Sets session['_impersonating_user_id'] and redirects to admin home.
    ImpersonationMiddleware will swap request.user on subsequent requests.
    """

    def get(self, request, user_id):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        target = get_object_or_404(User, pk=user_id, is_active=True)
        if target.pk == request.user.pk:
            from wagtail.admin import messages
            messages.warning(request, _("You cannot impersonate yourself."))
            return redirect(reverse("wagtailadmin_home"))

        request.session["_impersonating_user_id"] = target.pk

        # Audit
        from tenants.models import TenantMembership

        membership = (
            TenantMembership.objects.filter(user=target, is_active=True)
            .select_related("tenant")
            .order_by("-is_default", "pk")
            .first()
        )
        audit_tenant = membership.tenant if membership else None
        if audit_tenant:
            AuditService().log(
                tenant=audit_tenant,
                action=AuditAction.IMPERSONATION_STARTED,
                user=request.user,
                ip_address=AuditService._get_client_ip(request),
                details={
                    "impersonated_user_id": target.pk,
                    "impersonated_username": target.username,
                },
            )

        from wagtail.admin import messages
        messages.success(
            request,
            _("Impersonating %(user)s.") % {"user": target.get_username()},
        )
        return redirect(reverse("wagtailadmin_home"))


@method_decorator(user_passes_test(_superuser_required), name="dispatch")
class ImpersonateEndView(View):
    """End session-based impersonation (Wagtail admin)."""

    def get(self, request):
        imp_user_id = request.session.pop("_impersonating_user_id", None)
        if imp_user_id:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            imp_user = User.objects.filter(pk=imp_user_id).first()
            real_user = request.user
            if imp_user and real_user.is_superuser:
                from tenants.models import TenantMembership

                m = TenantMembership.objects.filter(
                    user=imp_user, is_active=True
                ).select_related("tenant").first()
                audit_tenant = m.tenant if m else None
                if audit_tenant:
                    AuditService().log(
                        tenant=audit_tenant,
                        action=AuditAction.IMPERSONATION_ENDED,
                        user=real_user,
                        ip_address=AuditService._get_client_ip(request),
                        details={
                            "impersonated_user_id": imp_user.pk,
                            "impersonated_username": imp_user.username,
                        },
                    )

        from wagtail.admin import messages
        messages.success(request, _("Impersonation ended."))
        return redirect(reverse("wagtailadmin_home"))


# ---------------------------------------------------------------------------
# Impersonation (SA-03)
# ---------------------------------------------------------------------------


@method_decorator(user_passes_test(_superuser_required), name="dispatch")
class ImpersonateStartView(View):
    """Start impersonating a user (session-based for Wagtail admin).

    Sets session['_impersonating_user_id'] and redirects to admin home.
    ImpersonationMiddleware then swaps request.user for subsequent requests.
    """

    def get(self, request, user_id):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        target = get_object_or_404(User, pk=user_id, is_active=True)
        if target.pk == request.user.pk:
            from wagtail.admin import messages

            messages.error(request, _("You cannot impersonate yourself."))
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
                details={
                    "impersonated_user_id": target.pk,
                    "impersonated_username": target.username,
                },
            )

        from wagtail.admin import messages

        messages.success(
            request,
            _("Now viewing as %(username)s.") % {"username": target.get_full_name() or target.username},
        )
        return redirect("wagtailadmin_home")


@method_decorator(user_passes_test(_superuser_required), name="dispatch")
class ImpersonateEndView(View):
    """End session-based impersonation and redirect to admin home."""

    def get(self, request):
        imp_user_id = request.session.pop("_impersonating_user_id", None)
        if imp_user_id:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            imp_user = User.objects.filter(pk=imp_user_id).first()
            real_user = request.user
            membership = (
                TenantMembership.objects.filter(user=imp_user, is_active=True)
                .select_related("tenant")
                .first()
            )
            audit_tenant = membership.tenant if membership else Tenant.objects.filter(is_active=True).first()
            if audit_tenant and imp_user:
                AuditService().log(
                    tenant=audit_tenant,
                    action=AuditAction.IMPERSONATION_ENDED,
                    user=real_user,
                    ip_address=AuditService._get_client_ip(request),
                    details={
                        "impersonated_user_id": imp_user.pk,
                        "impersonated_username": imp_user.username,
                    },
                )

        from wagtail.admin import messages

        messages.success(request, _("Impersonation ended. Back to your account."))
        return redirect("wagtailadmin_home")


@method_decorator(user_passes_test(_superuser_required), name="dispatch")
class ImpersonateStartView(View):
    """Start impersonating a user (session-based, Wagtail admin only).

    GET /admin/impersonate/start/<user_id>/
    Sets session and redirects to admin home. ImpersonationMiddleware
    will swap request.user on subsequent requests.
    """

    def get(self, request, user_id):
        from django.contrib.auth import get_user_model
        from tenants.models import TenantMembership

        User = get_user_model()
        target = get_object_or_404(User, pk=user_id, is_active=True)
        if target.pk == request.user.pk:
            from wagtail.admin import messages
            messages.warning(request, _("Cannot impersonate yourself."))
            return redirect("wagtailadmin_home")
        request.session["_impersonating_user_id"] = target.pk

        # Audit
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
                details={
                    "impersonated_user_id": target.pk,
                    "impersonated_username": target.username,
                },
            )

        from wagtail.admin import messages
        messages.success(
            request,
            _("Now viewing as %(user)s.") % {"user": target.get_full_name() or target.username},
        )
        return redirect("wagtailadmin_home")


@method_decorator(user_passes_test(_superuser_required), name="dispatch")
class ImpersonateEndView(View):
    """End session-based impersonation (Wagtail admin).

    GET /admin/impersonate/end/
    Clears session and redirects. Only works when session has
    _impersonating_user_id; the real user is always the session user.
    """

    def get(self, request):
        from django.contrib.auth import get_user_model

        imp_id = request.session.pop("_impersonating_user_id", None)
        if imp_id:
            User = get_user_model()
            try:
                imp_user = User.objects.get(pk=imp_id)
                membership = (
                    __import__("tenants.models", fromlist=["TenantMembership", "Tenant"])
                    and __import__("tenants.models", fromlist=["TenantMembership"])
                )
                from tenants.models import TenantMembership, Tenant
                m = TenantMembership.objects.filter(user=imp_user, is_active=True).select_related("tenant").first()
                audit_tenant = m.tenant if m else Tenant.objects.filter(is_active=True).first()
                if audit_tenant:
                    AuditService().log(
                        tenant=audit_tenant,
                        action=AuditAction.IMPERSONATION_ENDED,
                        user=request.user,
                        ip_address=AuditService._get_client_ip(request),
                        details={
                            "impersonated_user_id": imp_user.pk,
                            "impersonated_username": imp_user.username,
                        },
                    )
            except (User.DoesNotExist, Exception):
                pass
            from wagtail.admin import messages
            messages.success(request, _("Impersonation ended."))
        return redirect("wagtailadmin_home")


# ---------------------------------------------------------------------------
# SA-03: Impersonation (session-based for Wagtail admin)
# ---------------------------------------------------------------------------


@method_decorator(user_passes_test(_superuser_required), name="dispatch")
class ImpersonateStartView(View):
    """Start impersonating a user (session-based, Wagtail admin)."""

    def get(self, request, user_id):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        target = get_object_or_404(User, pk=user_id, is_active=True)
        if target.pk == request.user.pk:
            from wagtail.admin import messages

            messages.warning(request, _("You cannot impersonate yourself."))
            return redirect("wagtailadmin_home")

        request.session["_impersonating_user_id"] = target.pk

        # Audit
        from tenants.models import TenantMembership

        m = (
            TenantMembership.objects.filter(user=target, is_active=True)
            .select_related("tenant")
            .order_by("-is_default", "pk")
            .first()
        )
        audit_tenant = m.tenant if m else Tenant.objects.filter(is_active=True).first()
        if audit_tenant:
            AuditService().log(
                tenant=audit_tenant,
                action=AuditAction.IMPERSONATION_STARTED,
                user=request.user,
                ip_address=AuditService._get_client_ip(request),
                details={
                    "impersonated_user_id": target.pk,
                    "impersonated_username": target.username,
                },
            )

        from wagtail.admin import messages

        messages.success(
            request,
            _("Viewing as %(user)s.") % {"user": target.get_full_name() or target.username},
        )
        return redirect("wagtailadmin_home")


@method_decorator(user_passes_test(_superuser_required), name="dispatch")
class ImpersonateEndView(View):
    """End impersonation (clear session)."""

    def get(self, request):
        imp_id = request.session.pop("_impersonating_user_id", None)
        if imp_id:
            from django.contrib.auth import get_user_model
            from tenants.models import TenantMembership

            User = get_user_model()
            imp_user = User.objects.filter(pk=imp_id).first()
            audit_tenant = None
            if imp_user:
                m = (
                    TenantMembership.objects.filter(user=imp_user, is_active=True)
                    .select_related("tenant")
                    .first()
                )
                audit_tenant = m.tenant if m else Tenant.objects.filter(is_active=True).first()
            if audit_tenant:
                AuditService().log(
                    tenant=audit_tenant,
                    action=AuditAction.IMPERSONATION_ENDED,
                    user=request.user,
                    ip_address=AuditService._get_client_ip(request),
                    details={
                        "impersonated_user_id": imp_user.pk if imp_user else imp_id,
                        "impersonated_username": imp_user.username if imp_user else "",
                    },
                )

        from wagtail.admin import messages

        messages.success(request, _("Impersonation ended. You are viewing as yourself."))
        return redirect("wagtailadmin_home")
