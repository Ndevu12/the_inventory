"""Wagtail admin forms for tenant management.

Custom create form with owner selection/creation for SA-09.
"""

from django import forms
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from tenants.models import SubscriptionPlan, Tenant

User = get_user_model()

OWNER_MODE_NONE = "none"
OWNER_MODE_EXISTING = "existing"
OWNER_MODE_NEW_PASSWORD = "new_password"
OWNER_MODE_NEW_INVITE = "new_invite"


class TenantCreateForm(forms.ModelForm):
    """Custom create form for Tenant with owner selection/creation."""

    owner_mode = forms.ChoiceField(
        label=_("Owner"),
        choices=[
            (OWNER_MODE_NONE, _("No owner")),
            (OWNER_MODE_EXISTING, _("Select existing user")),
            (OWNER_MODE_NEW_PASSWORD, _("Create new user (set password)")),
            (OWNER_MODE_NEW_INVITE, _("Create new user (send invitation)")),
        ],
        initial=OWNER_MODE_NONE,
        required=True,
    )
    owner_user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True).order_by("username"),
        label=_("User"),
        required=False,
        empty_label=_("Select a user"),
    )
    owner_username = forms.CharField(
        label=_("Username"),
        max_length=150,
        required=False,
        help_text=_("For new users only."),
    )
    owner_email = forms.EmailField(
        label=_("Email"),
        required=False,
        help_text=_("Required when creating a new user."),
    )
    owner_password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        required=False,
        help_text=_("Required when creating new user with password."),
    )
    send_owner_invitation = forms.BooleanField(
        label=_("Send invitation email to owner"),
        required=False,
        initial=True,
        help_text=_("Send an email with the invitation link (when using invitation mode)."),
    )

    class Meta:
        model = Tenant
        fields = [
            "name",
            "slug",
            "subscription_plan",
            "max_users",
            "max_products",
            "is_active",
            "branding_site_name",
            "branding_primary_color",
        ]

    def __init__(self, *args, invited_by=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._invited_by = invited_by
        self.fields["owner_user"].queryset = User.objects.filter(
            is_active=True
        ).order_by("username")

    def clean_slug(self):
        slug = self.cleaned_data.get("slug")
        if slug and Tenant.objects.filter(slug=slug).exists():
            raise forms.ValidationError(
                _("A tenant with this slug already exists."),
                code="duplicate_slug",
            )
        return slug or slugify(self.cleaned_data.get("name", ""))

    def clean(self):
        data = super().clean()
        owner_mode = data.get("owner_mode", OWNER_MODE_NONE)

        if owner_mode == OWNER_MODE_EXISTING:
            if not data.get("owner_user"):
                self.add_error(
                    "owner_user",
                    _("Please select an existing user as owner."),
                )
        elif owner_mode == OWNER_MODE_NEW_PASSWORD:
            if not data.get("owner_username"):
                self.add_error(
                    "owner_username",
                    _("Username is required for new users."),
                )
            if not data.get("owner_email"):
                self.add_error(
                    "owner_email",
                    _("Email is required for new users."),
                )
            if not data.get("owner_password"):
                self.add_error(
                    "owner_password",
                    _("Password is required when creating a new user."),
                )
        elif owner_mode == OWNER_MODE_NEW_INVITE:
            if not data.get("owner_username"):
                self.add_error(
                    "owner_username",
                    _("Username is required for new users."),
                )
            if not data.get("owner_email"):
                self.add_error(
                    "owner_email",
                    _("Email is required for invitation."),
                )

        return data

    def save(self, commit=True):
        if not commit:
            return None

        from tenants.services import create_tenant_with_owner, send_invitation_email

        data = self.cleaned_data
        owner_mode = data["owner_mode"]

        owner_user = None
        owner_username = None
        owner_email = data.get("owner_email") or None
        owner_password = None
        send_owner_invitation = False
        invited_by = getattr(self, "_invited_by", None)

        if owner_mode == OWNER_MODE_EXISTING:
            owner_user = data.get("owner_user")
        elif owner_mode == OWNER_MODE_NEW_PASSWORD:
            owner_username = data.get("owner_username")
            owner_password = data.get("owner_password")
        elif owner_mode == OWNER_MODE_NEW_INVITE:
            owner_username = data.get("owner_username")
            send_owner_invitation = True  # Service creates invitation

        should_send_email = (
            owner_mode == OWNER_MODE_NEW_INVITE
            and data.get("send_owner_invitation", True)
        )

        tenant, invitation = create_tenant_with_owner(
            name=data["name"],
            slug=data["slug"] or slugify(data["name"]),
            subscription_plan=data.get("subscription_plan") or SubscriptionPlan.FREE,
            max_users=data.get("max_users"),
            max_products=data.get("max_products"),
            is_active=data.get("is_active", True),
            branding_site_name=data.get("branding_site_name") or "",
            branding_primary_color=data.get("branding_primary_color") or "",
            owner_user=owner_user,
            owner_username=owner_username,
            owner_email=owner_email,
            owner_password=owner_password,
            send_owner_invitation=send_owner_invitation,
            invited_by=invited_by,
        )

        if invitation and should_send_email:
            send_invitation_email(invitation)

        return tenant
