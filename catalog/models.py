from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    """
    A simple product category.
    """
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["is_active"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)[:140]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    A sellable item with pricing & inventory.
    """
    sku = models.CharField(max_length=64, unique=True)  # merchant-facing code
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")

    stock_qty = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    # Optional simple image link (avoid media storage for now)
    image_url = models.URLField(blank=True)

    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["price"]),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.title)[:200]
            # ensure some uniqueness with sku portion if present
            self.slug = (base or "product")
            if self.sku and not self.slug.endswith(self.sku.lower()):
                self.slug = f"{self.slug}-{self.sku.lower()}"[:220]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.sku})"
