from django.db import models
from django.db.models import UniqueConstraint
from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel, TabbedInterface
from wagtail.models import TranslatableMixin
from wagtail.search import index
from wagtail_localize.fields import SynchronizedField

from inventory.models.base import TimeStampedModel


class Customer(TranslatableMixin, TimeStampedModel):
    """A customer or client who places sales orders.

    Tracks contact information and active status.  Used as the
    counterparty on sales orders.
    """

    code = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Unique customer code per tenant (e.g., CUST-001).",
    )
    name = models.CharField(
        max_length=255,
        help_text="Customer or company name.",
    )
    contact_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Primary contact person.",
    )
    email = models.EmailField(
        blank=True,
        help_text="Contact email address.",
    )
    phone = models.CharField(
        max_length=50,
        blank=True,
        help_text="Contact phone number.",
    )
    address = models.TextField(
        blank=True,
        help_text="Full mailing or physical address.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive customers are excluded from new orders but preserved for history.",
    )
    notes = models.TextField(
        blank=True,
        help_text="Internal notes about this customer.",
    )

    override_translatable_fields = [
        SynchronizedField("code"),
    ]

    panels = [
        TabbedInterface([
            MultiFieldPanel(
                [
                    FieldRowPanel([
                        FieldPanel("code", classname="col6"),
                        FieldPanel("name", classname="col6"),
                    ]),
                    FieldPanel("contact_name"),
                    FieldRowPanel([
                        FieldPanel("email", classname="col6"),
                        FieldPanel("phone", classname="col6"),
                    ]),
                    FieldPanel("address"),
                ],
                heading="Customer Details",
            ),
            MultiFieldPanel(
                [
                    FieldPanel("notes"),
                ],
                heading="Notes",
            ),
            MultiFieldPanel(
                [
                    FieldPanel("is_active"),
                ],
                heading="Status",
            ),
        ])
    ]

    search_fields = [
        index.SearchField("name"),
        index.SearchField("code"),
        index.SearchField("contact_name"),
        index.FilterField("is_active"),
    ]

    class Meta:
        ordering = ["name"]
        constraints = [
            UniqueConstraint(
                fields=["tenant", "code", "locale"],
                name="unique_customer_code_per_tenant_locale",
            ),
            UniqueConstraint(
                fields=["translation_key", "locale"],
                name="unique_translation_key_locale_sales_customer",
            ),
        ]

    def __str__(self):
        return f"{self.code} — {self.name}"
