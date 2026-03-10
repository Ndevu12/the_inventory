from django.db import models
from django.db.models import F
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable
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


class ProductQuerySet(models.QuerySet):
    """Custom queryset with inventory-specific filters."""

    def low_stock(self):
        """Return products where any StockRecord quantity <= reorder_point.

        Products with ``reorder_point = 0`` are excluded (no alert configured).
        """
        return self.filter(
            reorder_point__gt=0,
            stock_records__quantity__lte=F("reorder_point"),
        ).distinct()

    def out_of_stock(self):
        """Return products that have at least one StockRecord with quantity 0."""
        return self.filter(
            stock_records__quantity=0,
        ).distinct()

    def in_stock(self):
        """Return products where all StockRecords are above reorder_point."""
        return self.exclude(
            pk__in=self.low_stock().values_list("pk", flat=True),
        ).filter(stock_records__quantity__gt=0).distinct()


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
    tags = ClusterTaggableManager(
        through="inventory.ProductTag",
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    panels = [
        FieldPanel("sku"),
        FieldPanel("name"),
        FieldPanel("description"),
        FieldPanel("category"),
        FieldPanel("unit_of_measure"),
        FieldPanel("unit_cost"),
        FieldPanel("reorder_point"),
        FieldPanel("is_active"),
        InlinePanel("images", label="Product images"),
        FieldPanel("tags"),
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


class ProductImage(Orderable):
    """Multiple images per product with ordering and optional captions."""

    product = ParentalKey(
        "inventory.Product",
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.CASCADE,
        related_name="+",
    )
    caption = models.CharField(max_length=255, blank=True)

    panels = [
        FieldPanel("image"),
        FieldPanel("caption"),
    ]

    def __str__(self):
        return f"Image for {self.product.sku}"


class ProductTag(TaggedItemBase):
    """Free-form tagging for products via django-taggit."""

    content_object = ParentalKey(
        "inventory.Product",
        on_delete=models.CASCADE,
        related_name="tagged_items",
    )

    def __str__(self):
        return f"Image for {self.product.sku}"
