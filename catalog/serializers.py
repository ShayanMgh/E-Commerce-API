from rest_framework import serializers
from .models import Category, Product

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description", "is_active")

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        write_only=True, source="category", queryset=Category.objects.all()
    )

    class Meta:
        model = Product
        fields = (
            "id", "sku", "title", "slug", "description",
            "price", "currency", "stock_qty", "is_active",
            "image_url",
            "category", "category_id",
            "created_at", "updated_at",
        )
        read_only_fields = ("slug", "created_at", "updated_at")

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("price must be > 0")
        return value
