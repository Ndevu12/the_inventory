from django.db import models
from django.db.models import F, Q, UniqueConstraint
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel, FieldRowPanel, InlinePanel, MultiFieldPanel, TabbedInterface
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

    sku = models.CharField(
        "SKU",
        max_length=100,
        db_index=True,
        help_text="Unique Stock Keeping Unit identifier (e.g., PHONE-001). Unique per tenant.",
    )
    name = models.CharField(
        max_length=255,
        help_text="The product name displayed to users (e.g., 'iPhone 15 Pro').",
    )
    description = RichTextField(
        blank=True,
        help_text="Detailed product description with rich text formatting. Optional.",
    )
    category = models.ForeignKey(
        "inventory.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        help_text="Select the category this product belongs to.",
    )
    unit_of_measure = models.CharField(
        max_length=10,
        choices=UnitOfMeasure.choices,
        default=UnitOfMeasure.PIECES,
        help_text="The unit used to measure this product (pieces, kilograms, liters, etc.).",
    )
    unit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="The default or latest purchase cost per unit. Used for inventory valuation.",
    )
    reorder_point = models.PositiveIntegerField(
        default=0,
        help_text="When stock at any location falls to or below this amount, a low-stock alert is triggered. Set to 0 to disable alerts.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive products are hidden from most displays but preserved for historical records.",
    )
    tags = ClusterTaggableManager(
        through="inventory.ProductTag",
        blank=True,
        help_text="Add tags to help organize and filter products (e.g., 'featured', 'clearance').",
    )

    objects = ProductQuerySet.as_manager()

    panels = [
        TabbedInterface([
            MultiFieldPanel(
                [
                    FieldRowPanel([
                        FieldPanel("sku", classname="col6"),
                        FieldPanel("name", classname="col6"),
                    ]),
                    FieldPanel("description"),
                    FieldPanel("category"),
                ],
                heading="Basic Info",
            ),
            MultiFieldPanel(
                [
                    MultiFieldPanel(
                        [
                            FieldRowPanel([
                                FieldPanel("unit_of_measure", classname="col6"),
                                FieldPanel("unit_cost", classname="col6"),
                            ]),
                            FieldPanel("reorder_point"),
                        ],
                        heading="Stock Management",
                    ),
                ],
                heading="Pricing & Inventory",
            ),
            MultiFieldPanel(
                [
                    InlinePanel("images", label="Product Images", min_num=0),
                    FieldPanel("tags"),
                ],
                heading="Media & Details",
            ),
            MultiFieldPanel(
                [
                    FieldPanel("is_active"),
                ],
                heading="Publishing",
            ),
        ])
    ]

    search_fields = [
        index.SearchField("name"),
        index.SearchField("sku"),
        index.SearchField("description"),
        index.FilterField("category"),
        index.FilterField("is_active"),
        index.FilterField("unit_of_measure"),
    ]

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["tenant", "sku"],
                name="unique_product_sku_per_tenant",
            ),
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
        help_text="Upload an image to display for this product.",
    )
    caption = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional caption for the image (e.g., 'Front view', 'Product packaging').",
    )

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
