from rest_framework import serializers
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ("id", "product_id", "sku", "title", "unit_price", "qty", "line_total", "created_at")
        read_only_fields = fields

    def get_line_total(self, obj):
        return f"{(obj.unit_price * obj.qty):.2f}"

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id", "public_id", "status", "currency",
            "subtotal_amount", "tax_amount", "shipping_amount", "total_amount",
            "payment_intent_id", "items", "created_at", "updated_at",
        )
        read_only_fields = fields
