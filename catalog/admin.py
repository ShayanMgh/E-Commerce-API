# catalog/admin.py
from django.contrib import admin
from .models import Category, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "sku", "price", "currency", "stock_qty", "is_active", "category")
    list_filter = ("is_active", "currency", "category")
    search_fields = ("title", "sku", "description")
    autocomplete_fields = ("category",)
    ordering = ("title",)
