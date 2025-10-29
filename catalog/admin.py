from django.contrib import admin
from .models import Category, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "sku", "title", "price", "currency", "stock_qty", "is_active", "category")
    list_filter = ("is_active", "currency", "category")
    search_fields = ("sku", "title", "slug", "description")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("category",)
    ordering = ("-created_at",)
