"""Django admin site restricted to superusers only.

Used at /django-admin/ for auth.User, Group, and other system-level operations.
See SA-08 in docs/TASKS.MD.
"""

from django.contrib import admin
from django.shortcuts import redirect


class SuperuserOnlyAdminSite(admin.AdminSite):
    """Django AdminSite accessible only by users with is_superuser=True."""

    site_header = "Django Admin (Superuser only)"
    site_title = "Django Admin"
    index_title = "Platform administration"

    def has_permission(self, request):
        if not request.user.is_active:
            return False
        return request.user.is_superuser

    def login(self, request, extra_context=None):
        """Redirect non-superusers to Wagtail admin (before or after login)."""
        if request.user.is_authenticated and not request.user.is_superuser:
            return redirect("/admin/")
        response = super().login(request, extra_context)
        if request.user.is_authenticated and not request.user.is_superuser:
            return redirect("/admin/")
        return response


superuser_admin_site = SuperuserOnlyAdminSite(name="django_admin")
