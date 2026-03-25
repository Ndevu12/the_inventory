from django.db import models

from inventory.utils.warehouse_scope import WAREHOUSE_SCOPE_UNSPECIFIED
from django.utils.translation import gettext_lazy as _
from django.db.models import F, OuterRef, Subquery, UniqueConstraint
from django.db.models.functions import Coalesce
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel, FieldRowPanel, InlinePanel, MultiFieldPanel, TabbedInterface
from wagtail.fields import RichTextField
from wagtail.models import Orderable, TranslatableMixin
from wagtail.search import index
from wagtail_localize.fields import SynchronizedField

from .base import TimeStampedModel


class UnitOfMeasure(models.TextChoices):
    PIECES = "pcs", _("Pieces")
    KILOGRAMS = "kg", _("Kilograms")
    LITERS = "lt", _("Liters")
    METERS = "m", _("Meters")
    BOXES = "box", _("Boxes")
    PACKS = "pack", _("Packs")


class TrackingMode(models.TextChoices):
    NONE = "none", _("No Tracking")
    OPTIONAL = "optional", _("Optional Lot Tracking")
    REQUIRED = "required", _("Required Lot Tracking")


class ProductQuerySet(models.QuerySet):
    """Custom queryset with inventory-specific and tenant-aware filters.

    Inherits the ``filter_by_current_tenant()`` contract from
    ``TenantAwareQuerySet`` so that Product scoping is consistent with
    other ``TimeStampedModel`` subclasses.
    """

    def filter_by_current_tenant(self):
        """Filter to thread-local tenant; empty queryset if unset."""
        from tenants.context import get_current_tenant

        current_tenant = get_current_tenant()
        if current_tenant is None:
            return self.none()
        return self.filter(tenant=current_tenant)

    def low_stock(self, *, warehouse_id: int | None | object = WAREHOUSE_SCOPE_UNSPECIFIED):
        """Return products where any location's available quantity <= reorder_point.

        Available quantity = physical quantity minus active reservations
        (pending + confirmed).  Products with ``reorder_point = 0`` are
        excluded (no alert configured).

        When *warehouse_id* is :data:`inventory.services.stock.WAREHOUSE_SCOPE_UNSPECIFIED`
        (default), all locations are considered. ``None`` limits to retail-only
        locations (no facility on ``StockLocation``). A positive int limits to
        that facility's locations.
        """
        from inventory.models.reservation import StockReservation

        reserved_subquery = Subquery(
            StockReservation.objects.filter(
                product=OuterRef("product"),
                location=OuterRef("location"),
                status__in=["pending", "confirmed"],
            ).order_by().values("product", "location").annotate(
                total=models.Sum("quantity"),
            ).values("total")[:1]
        )

        from inventory.models.stock import StockRecord

        low_records = StockRecord.objects.annotate(
            _reserved=Coalesce(reserved_subquery, 0),
            _available=F("quantity") - Coalesce(reserved_subquery, 0),
        ).filter(
            _available__lte=F("product__reorder_point"),
            product__reorder_point__gt=0,
        )
        if warehouse_id is not WAREHOUSE_SCOPE_UNSPECIFIED:
            if warehouse_id is None:
                low_records = low_records.filter(location__warehouse_id__isnull=True)
            else:
                low_records = low_records.filter(location__warehouse_id=warehouse_id)

        return self.filter(
            reorder_point__gt=0,
            pk__in=low_records.values("product_id"),
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


class Product(TranslatableMixin, TimeStampedModel, ClusterableModel):
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
    tracking_mode = models.CharField(
        max_length=10,
        choices=TrackingMode.choices,
        default=TrackingMode.NONE,
        help_text="Whether lot/batch tracking is required for this product.",
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

    override_translatable_fields = [
        SynchronizedField("sku"),
    ]

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
                fields=["translation_key", "locale"],
                name="unique_translation_key_locale_inventory_product",
            ),
            UniqueConstraint(
                fields=["tenant", "sku", "locale"],
                name="unique_product_sku_per_tenant_locale",
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
