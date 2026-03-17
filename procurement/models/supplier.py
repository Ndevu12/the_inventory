from django.db import models
from django.db.models import UniqueConstraint
from wagtail.admin.panels import FieldPanel, FieldRowPanel, MultiFieldPanel, TabbedInterface
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from inventory.models.base import TimeStampedModel


class PaymentTerms(models.TextChoices):
    NET_30 = "net_30", "Net 30"
    NET_60 = "net_60", "Net 60"
    NET_90 = "net_90", "Net 90"
    COD = "cod", "Cash on Delivery"
    PREPAID = "prepaid", "Prepaid"


@register_snippet
class Supplier(TimeStampedModel):
    """Vendor or supplier of goods.

    Tracks contact information, lead times, and payment terms.
    Used as the counterparty on purchase orders.
    """

    code = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Unique supplier code per tenant (e.g., SUP-001).",
    )
    name = models.CharField(
        max_length=255,
        help_text="Supplier or company name.",
    )
    contact_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Primary contact person at this supplier.",
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
    lead_time_days = models.PositiveIntegerField(
        default=0,
        help_text="Typical delivery lead time in days.",
    )
    payment_terms = models.CharField(
        max_length=20,
        choices=PaymentTerms.choices,
        default=PaymentTerms.NET_30,
        help_text="Standard payment terms for this supplier.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive suppliers are excluded from new orders but preserved for history.",
    )
    notes = models.TextField(
        blank=True,
        help_text="Internal notes about this supplier.",
    )

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
                heading="Supplier Details",
            ),
            MultiFieldPanel(
                [
                    FieldRowPanel([
                        FieldPanel("lead_time_days", classname="col6"),
                        FieldPanel("payment_terms", classname="col6"),
                    ]),
                    FieldPanel("notes"),
                ],
                heading="Terms & Notes",
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
                fields=["tenant", "code"],
                name="unique_supplier_code_per_tenant",
            ),
        ]

    def __str__(self):
        return f"{self.code} — {self.name}"
