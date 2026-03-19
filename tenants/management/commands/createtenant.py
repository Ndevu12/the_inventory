"""Management command to create a new tenant with an optional owner user.

Usage examples::

    # Minimal — interactive owner creation
    python manage.py createtenant "Acme Corp"

    # Explicit slug and subscription plan
    python manage.py createtenant "Acme Corp" --slug acme-corp --plan professional

    # Attach an existing user as owner
    python manage.py createtenant "Acme Corp" --owner-username alice

    # Create a brand-new owner user in one shot
    python manage.py createtenant "Acme Corp" \
        --owner-username alice \
        --owner-email alice@acme.com \
        --owner-password 'S3cret!'

    # Non-interactive (CI / Docker entrypoint)
    python manage.py createtenant "Acme Corp" --noinput \
        --owner-username alice --owner-email alice@acme.com --owner-password 'S3cret!'
"""

import getpass

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from tenants.models import SubscriptionPlan, Tenant
from tenants.services import create_tenant_with_owner

User = get_user_model()

PLAN_CHOICES = [p.value for p in SubscriptionPlan]


class Command(BaseCommand):
    help = "Create a new tenant (organization) and optionally assign an owner user."

    def add_arguments(self, parser):
        parser.add_argument(
            "name",
            type=str,
            help="Display name for the new tenant (e.g. 'Acme Corp').",
        )
        parser.add_argument(
            "--slug",
            type=str,
            default=None,
            help="URL-safe slug. Auto-generated from name if omitted.",
        )
        parser.add_argument(
            "--plan",
            type=str,
            choices=PLAN_CHOICES,
            default=SubscriptionPlan.FREE,
            help=f"Subscription plan ({', '.join(PLAN_CHOICES)}). Default: free.",
        )
        parser.add_argument(
            "--max-users",
            type=int,
            default=None,
            help="Override the default max-users limit for the plan.",
        )
        parser.add_argument(
            "--max-products",
            type=int,
            default=None,
            help="Override the default max-products limit for the plan.",
        )
        parser.add_argument(
            "--inactive",
            action="store_true",
            help="Create the tenant in an inactive state.",
        )

        owner = parser.add_argument_group("owner user")
        owner.add_argument(
            "--owner-username",
            type=str,
            default=None,
            help="Username of the owner. Uses an existing user if found, otherwise creates one.",
        )
        owner.add_argument(
            "--owner-email",
            type=str,
            default=None,
            help="Email for the owner (used when creating a new user).",
        )
        owner.add_argument(
            "--owner-password",
            type=str,
            default=None,
            help="Password for the owner (used when creating a new user). "
            "Prompted interactively if omitted.",
        )
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_true",
            dest="no_input",
            help="Suppress all interactive prompts.",
        )

    def handle(self, *args, **options):
        name = options["name"].strip()
        if not name:
            raise CommandError("Tenant name must not be empty.")

        slug = options["slug"] or slugify(name)
        if Tenant.objects.filter(slug=slug).exists():
            raise CommandError(
                f"A tenant with slug '{slug}' already exists. "
                "Choose a different name or pass an explicit --slug."
            )

        owner_username = options.get("owner_username")
        if not owner_username and not options["no_input"]:
            owner_username = input(
                "Owner username (leave blank to skip): "
            ).strip() or None

        owner_password = options.get("owner_password")
        if owner_username and not owner_password:
            if options["no_input"]:
                try:
                    User.objects.get(username=owner_username)
                except User.DoesNotExist:
                    raise CommandError(
                        f"User '{owner_username}' does not exist and no password was provided. "
                        "Pass --owner-password or run without --noinput."
                    )
            else:
                try:
                    User.objects.get(username=owner_username)
                except User.DoesNotExist:
                    owner_password = getpass.getpass(
                        f"Password for new user '{owner_username}': "
                    )
                    password_confirm = getpass.getpass("Confirm password: ")
                    if owner_password != password_confirm:
                        raise CommandError("Passwords do not match.")
                    if not owner_password:
                        raise CommandError("Password must not be empty.")

        tenant, invitation = create_tenant_with_owner(
            name=name,
            slug=slug,
            subscription_plan=options["plan"],
            max_users=options["max_users"],
            max_products=options["max_products"],
            is_active=not options["inactive"],
            owner_username=owner_username,
            owner_email=options.get("owner_email"),
            owner_password=owner_password,
        )

        self.stdout.write(
            self.style.SUCCESS(f"Created tenant '{tenant.name}' (slug={tenant.slug})")
        )
        if owner_username and invitation is None:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Assigned '{owner_username}' as owner of '{tenant.name}'"
                )
            )
        self.stdout.write(self.style.SUCCESS("Done."))
