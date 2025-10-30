from django.db import models, transaction
from django.utils import timezone

class Order(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_FAILED = "failed"
    STATUS_CANCELED = "canceled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PAID, "Paid"),
        (STATUS_FAILED, "Failed"),
        (STATUS_CANCELED, "Canceled"),
    ]

    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="orders")
    public_id = models.UUIDField(unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    currency = models.CharField(max_length=10, default="USD")
    subtotal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_intent_id = models.CharField(max_length=255, blank=True, default="")
    paid_at = models.DateTimeField(null=True, blank=True)  # <— new
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @transaction.atomic
    def mark_paid_and_decrement_stock(self):
        """
        Atomically mark order as paid and decrement product stock.
        Uses SELECT ... FOR UPDATE to prevent race conditions.
        """
        if self.status == self.STATUS_PAID:
            return  # idempotent

        # Lock order rows
        order = Order.objects.select_for_update().get(pk=self.pk)

        # Lock all involved products before decrement
        from catalog.models import Product
        item_qs = order.items.select_related(None).values("product_id", "qty")
        product_ids = [row["product_id"] for row in item_qs]
        products = {p.id: p for p in Product.objects.select_for_update().filter(id__in=product_ids)}

        # Validate stock and decrement
        for row in item_qs:
            p = products[row["product_id"]]
            need = int(row["qty"])
            if p.stock_qty < need:
                raise ValueError(f"Insufficient stock for product id={p.id}")
            p.stock_qty = p.stock_qty - need

        # Persist product updates
        Product.objects.bulk_update(products.values(), ["stock_qty"])

        # Mark paid
        order.status = Order.STATUS_PAID
        order.paid_at = timezone.now()
        order.save(update_fields=["status", "paid_at", "updated_at"])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product_id = models.IntegerField()
    sku = models.CharField(max_length=64)
    title = models.CharField(max_length=255)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    qty = models.PositiveIntegerField()
    line_total = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
