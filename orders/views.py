import logging
from decimal import Decimal
from django.db import transaction
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order, OrderItem
from .serializers import OrderSerializer
from cart.models import Cart, CartItem
from catalog.models import Product

log = logging.getLogger("orders.api")

class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List/retrieve orders. Users see only their own orders.
    Staff can see all.
    """
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Order.objects.prefetch_related("items").all()
        user = self.request.user
        if not user.is_staff:
            qs = qs.filter(user=user)
        return qs

class CreateOrderView(APIView):
    """
    POST /api/checkout/create-order/
    Convert the current open cart into an Order snapshot.
    - Validates items still active and stock >= qty (no decrement yet).
    - Copies items into OrderItem snapshots and computes totals.
    - Marks the cart as CONVERTED and clears its items.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user
        cart, created = Cart.objects.get_or_create(user=user, status=Cart.STATUS_OPEN)
        if created or cart.items.count() == 0:
            log.warning("Create order with empty cart user=%s", user.id)
            return Response({"detail": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate currency consistency and stock
        currency = None
        for item in cart.items.select_related("product"):
            p: Product = item.product
            if not p.is_active:
                return Response({"detail": f"Product {p.id} is inactive"}, status=400)
            if item.qty > p.stock_qty:
                return Response({"detail": f"Insufficient stock for product {p.id}"}, status=400)
            if currency is None:
                currency = p.currency
            elif p.currency != currency:
                return Response({"detail": "Mixed currencies in cart not supported"}, status=400)

        # Build Order & OrderItems
        order = Order.objects.create(
            user=user,
            status=Order.STATUS_PENDING,
            currency=currency or "USD",
        )

        subtotal = Decimal("0.00")
        for ci in cart.items.select_related("product"):
            p: Product = ci.product
            oi = OrderItem.objects.create(
                order=order,
                product_id=p.id,
                sku=p.sku,
                title=p.title,
                unit_price=p.price,  # snapshot current price
                qty=ci.qty,
            )
            subtotal += oi.unit_price * oi.qty

        tax = Decimal("0.00")
        shipping = Decimal("0.00")
        total = subtotal + tax + shipping

        order.subtotal_amount = subtotal
        order.tax_amount = tax
        order.shipping_amount = shipping
        order.total_amount = total
        order.save()

        # Clear/convert cart (a new open cart will be created on next access)
        cart.items.all().delete()
        cart.status = Cart.STATUS_CONVERTED
        cart.save()

        log.info("Created order id=%s user=%s items=%s total=%s %s",
                 order.id, user.id, order.items.count(), order.total_amount, order.currency)

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
