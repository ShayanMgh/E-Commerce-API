# orders/admin.py
from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("product_id", "sku", "title", "qty", "unit_price", "line_total")
    readonly_fields = ()
    ordering = ("id",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "public_id",
        "user",
        "status",
        "currency",
        "total_amount",
        "payment_intent_id",
        "created_at",
    )
    list_filter = ("status", "currency", "created_at")
    search_fields = ("public_id", "payment_intent_id", "user__email")
    readonly_fields = ("public_id", "created_at", "updated_at")
    ordering = ("-id",)
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "product_id",
        "sku",
        "title",
        "qty",
        "unit_price",
        "line_total",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = ("sku", "title", "order__public_id", "order__payment_intent_id")
    readonly_fields = ("created_at",)
    ordering = ("-id",)
    autocomplete_fields = ("order",)  # only valid FK here
