import logging
from decimal import Decimal
from django.db import transaction
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
from catalog.models import Product

log = logging.getLogger("cart.api")

def _get_or_create_open_cart(user):
    cart, created = Cart.objects.get_or_create(user=user, status=Cart.STATUS_OPEN)
    if created:
        log.info("Created new open cart user=%s cart_id=%s", user.id, cart.id)
    return cart

class CartView(APIView):
    """
    GET /api/cart/ -> current user's open cart with items and subtotal.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cart = _get_or_create_open_cart(request.user)
        log.debug("Fetch cart user=%s cart_id=%s", request.user.id, cart.id)
        return Response(CartSerializer(cart).data)

class CartItemViewSet(viewsets.ModelViewSet):
    """
    POST /api/cart/items/       {product_id, qty}
    PATCH /api/cart/items/{id}/ {qty}
    DELETE /api/cart/items/{id}/
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CartItemSerializer

    def get_queryset(self):
        cart = _get_or_create_open_cart(self.request.user)
        return CartItem.objects.select_related("product", "cart").filter(cart=cart).order_by("-created_at")

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        cart = _get_or_create_open_cart(request.user)
        product_id = request.data.get("product_id")
        qty = int(request.data.get("qty", 0))

        # Validate product
        try:
            product = Product.objects.get(pk=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response({"detail": "product not found or inactive"}, status=status.HTTP_400_BAD_REQUEST)

        # Merge with existing item if present
        existing = CartItem.objects.filter(cart=cart, product=product).first()
        new_qty = qty + (existing.qty if existing else 0)
        if new_qty <= 0:
            return Response({"detail": "qty must be >= 1"}, status=status.HTTP_400_BAD_REQUEST)
        if new_qty > product.stock_qty:
            log.warn("Insufficient stock product=%s requested=%s available=%s", product.id, new_qty, product.stock_qty)
            return Response({"detail": f"requested {new_qty} exceeds available {product.stock_qty}"}, status=400)

        if existing:
            existing.qty = new_qty
            existing.unit_price = product.price  # refresh snapshot
            existing.save()
            item = existing
            log.info("Updated cart item user=%s cart=%s product=%s qty=%s", request.user.id, cart.id, product.id, item.qty)
        else:
            item = CartItem.objects.create(cart=cart, product=product, qty=qty, unit_price=product.price)
            log.info("Added item user=%s cart=%s product=%s qty=%s", request.user.id, cart.id, product.id, qty)

        serializer = self.get_serializer(item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        item = self.get_queryset().filter(pk=kwargs["pk"]).first()
        if not item:
            return Response({"detail": "cart item not found"}, status=404)

        qty = request.data.get("qty", None)
        if qty is None:
            return Response({"detail": "qty is required"}, status=400)
        qty = int(qty)
        if qty <= 0:
            # delete if qty <= 0
            log.info("Delete item via qty<=0 user=%s item=%s", request.user.id, item.id)
            item.delete()
            return Response(status=204)

        product = item.product
        if qty > product.stock_qty:
            return Response({"detail": f"requested {qty} exceeds available {product.stock_qty}"}, status=400)

        item.qty = qty
        item.unit_price = product.price  # refresh snapshot on update
        item.save()
        log.info("Updated item user=%s item=%s qty=%s", request.user.id, item.id, qty)
        return Response(self.get_serializer(item).data)

    def destroy(self, request, *args, **kwargs):
        item = self.get_queryset().filter(pk=kwargs["pk"]).first()
        if not item:
            return Response({"detail": "cart item not found"}, status=404)
        log.info("Deleted item user=%s item=%s", request.user.id, item.id)
        item.delete()
        return Response(status=204)
