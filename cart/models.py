from decimal import Decimal
from django.conf import settings
from django.db import models

class Cart(models.Model):
    """
    One open cart per user. Converted/abandoned carts can be kept for history later.
    """
    STATUS_OPEN = "open"
    STATUS_CONVERTED = "converted"
    STATUS_CANCELED = "canceled"
    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_CONVERTED, "Converted"),
        (STATUS_CANCELED, "Canceled"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="carts")
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["user", "status"])]
        constraints = [
            models.UniqueConstraint(fields=["user"], condition=models.Q(status="open"), name="uniq_open_cart_per_user")
        ]

    def __str__(self):
        return f"Cart(user={self.user_id}, status={self.status})"

    @property
    def subtotal(self) -> Decimal:
        return sum((item.unit_price * item.qty for item in self.items.all()), start=Decimal("0.00"))

class CartItem(models.Model):
    """
    Line item with unit_price snapshot from Product at time of add.
    """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("catalog.Product", on_delete=models.PROTECT, related_name="cart_items")
    qty = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["cart", "product"]),
        ]
        unique_together = [("cart", "product")]

    def __str__(self):
        return f"CartItem(cart={self.cart_id}, product={self.product_id}, qty={self.qty})"

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.qty
