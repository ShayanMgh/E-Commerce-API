# payments/admin.py
from django.contrib import admin

# Safely import Refund model if it exists
try:
    from .models import Refund  # type: ignore
except Exception:
    Refund = None  # model not present; skip registration

if Refund:
    @admin.register(Refund)
    class RefundAdmin(admin.ModelAdmin):
        list_display = ("id", "order", "refund_id", "status", "created_at")
        list_filter = ("status", "created_at")
        search_fields = ("refund_id", "order__public_id", "order__payment_intent_id")
        readonly_fields = ("created_at",)
        autocomplete_fields = ("order",)
        ordering = ("-id",)
