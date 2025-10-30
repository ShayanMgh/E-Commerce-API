from django.contrib import admin
from .models import StripeEvent

@admin.register(StripeEvent)
class StripeEventAdmin(admin.ModelAdmin):
    list_display = ("event_id", "created_at")
    search_fields = ("event_id",)
