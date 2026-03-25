from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, TabbedInterface
from wagtail.search import index

from .base import TimeStampedModel


class Warehouse(TimeStampedModel):
    """Tenant-scoped storage facility (building, DC, or site).

    Stock locations may optionally reference a warehouse; when ``warehouse`` is
    null on locations, the tenant uses a retail-only / single-site location tree.
    """

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(
        default=True,
        help_text=_("Inactive warehouses are hidden from day-to-day operations."),
    )
    timezone_name = models.CharField(
        max_length=64,
        blank=True,
        help_text=_("IANA timezone name (e.g. America/Chicago), optional."),
    )
    address = models.TextField(
        blank=True,
        help_text=_("Full mailing or physical site address."),
    )

    panels = [
        TabbedInterface([
            MultiFieldPanel(
                [
                    FieldPanel("name"),
                    FieldPanel("description"),
                    FieldPanel("is_active"),
                    FieldPanel("timezone_name"),
                ],
                heading=_("Warehouse"),
            ),
            MultiFieldPanel(
                [FieldPanel("address")],
                heading=_("Location"),
            ),
        ])
    ]

    search_fields = [
        index.SearchField("name"),
        index.SearchField("description"),
        index.SearchField("address"),
        index.FilterField("is_active"),
    ]

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
