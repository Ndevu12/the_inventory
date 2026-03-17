from django.contrib import admin

from tenants.models import Tenant, TenantMembership


class TenantMembershipInline(admin.TabularInline):
    model = TenantMembership
    extra = 1
    fields = ("user", "role", "is_active", "is_default")


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "subscription_plan", "subscription_status", "is_active")
    list_filter = ("is_active", "subscription_plan", "subscription_status")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [TenantMembershipInline]
    fieldsets = (
        (None, {"fields": ("name", "slug", "is_active")}),
        (
            "Branding",
            {
                "fields": ("branding_site_name", "branding_primary_color", "branding_logo"),
                "classes": ("collapse",),
            },
        ),
        (
            "Subscription",
            {
                "fields": ("subscription_plan", "subscription_status", "max_users", "max_products"),
            },
        ),
    )


@admin.register(TenantMembership)
class TenantMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "tenant", "role", "is_active", "is_default")
    list_filter = ("role", "is_active", "tenant")
    search_fields = ("user__username", "user__email", "tenant__name")
    raw_id_fields = ("user",)
