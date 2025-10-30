from decimal import Decimal
from rest_framework import serializers
from .models import Cart, CartItem
from catalog.models import Product

class CartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(source="product", queryset=Product.objects.all(), write_only=True)
    line_total = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CartItem
        fields = ("id", "product_id", "product", "qty", "unit_price", "line_total", "created_at", "updated_at")
        read_only_fields = ("id", "unit_price", "line_total", "product", "created_at", "updated_at")

    def get_line_total(self, obj):
        return f"{(obj.unit_price * obj.qty):.2f}"

    def validate(self, data):
        product = data.get("product") or getattr(self.instance, "product", None)
        qty = data.get("qty", getattr(self.instance, "qty", None))
        if not product or qty is None:
            return data
        if qty <= 0:
            raise serializers.ValidationError({"qty": "qty must be >= 1"})
        if not product.is_active:
            raise serializers.ValidationError({"product_id": "product is not active"})
        if qty > product.stock_qty:
            raise serializers.ValidationError({"qty": f"requested {qty} exceeds available stock {product.stock_qty}"})
        return data

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Cart
        fields = ("id", "status", "items", "subtotal", "created_at", "updated_at")
        read_only_fields = ("id", "status", "items", "subtotal", "created_at", "updated_at")

    def get_subtotal(self, obj):
        return f"{obj.subtotal:.2f}"
