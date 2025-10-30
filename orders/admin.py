from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_id", "sku", "title", "unit_price", "qty", "created_at")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "currency", "total_amount", "created_at")
    list_filter = ("status", "currency", "created_at")
    search_fields = ("user__email", "public_id", "payment_intent_id")
    inlines = [OrderItemInline]
