from django.db import models
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from .base import TimeStampedModel


class UnitOfMeasure(models.TextChoices):
    PIECES = "pcs", "Pieces"
    KILOGRAMS = "kg", "Kilograms"
    LITERS = "lt", "Liters"
    METERS = "m", "Meters"
    BOXES = "box", "Boxes"
    PACKS = "pack", "Packs"


@register_snippet
class Product(TimeStampedModel, ClusterableModel):
    """Central product model for the inventory system."""

    sku = models.CharField("SKU", max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    description = RichTextField(blank=True)
    category = models.ForeignKey(
        "inventory.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )
    unit_of_measure = models.CharField(
        max_length=10,
        choices=UnitOfMeasure.choices,
        default=UnitOfMeasure.PIECES,
    )
    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Default / latest purchase cost per unit.",
    )
    reorder_point = models.PositiveIntegerField(
        default=0,
        help_text=(
            "Low-stock alert triggers when any location's quantity "
            "falls to or below this."
        ),
    )
    is_active = models.BooleanField(default=True)

    panels = [
        FieldPanel("sku"),
        FieldPanel("name"),
        FieldPanel("description"),
        FieldPanel("category"),
        FieldPanel("unit_of_measure"),
        FieldPanel("unit_cost"),
        FieldPanel("reorder_point"),
        FieldPanel("is_active"),
        # InlinePanel("images", ...) — added by ProductImage (#10)
        # FieldPanel("tags") — added by ProductTag (#11)
    ]

    search_fields = [
        index.SearchField("name"),
        index.SearchField("sku"),
        index.SearchField("description"),
        index.FilterField("category"),
        index.FilterField("is_active"),
        index.FilterField("unit_of_measure"),
    ]

    def __str__(self):
        return f"{self.sku} — {self.name}"
