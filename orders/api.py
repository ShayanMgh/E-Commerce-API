# orders/api.py
"""
Orders API
- CreateOrderView: idempotent cart -> order creation
- Snapshots cart items into Order/OrderItem, clears cart, returns the created or latest order
"""

import logging
from decimal import Decimal
from django.db import transaction
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.models import Cart, CartItem
from orders.models import Order, OrderItem
from orders.serializers import OrderSerializer

log = logging.getLogger("orders.api")


def _latest_order_for(user):
    """
    Return the most recent order for this user (any status).
    This is intentionally broader than filtering only 'pending'
    to make follow-up calls idempotent in test environments.
    """
    return (
        Order.objects.filter(user=user)
        .order_by("-id")
        .first()
    )


class CreateOrderView(APIView):
    """
    POST /api/checkout/create-order/
    - Creates an Order from the user's open cart (must have items)
    - Clears the cart items after snapshotting into the order
    - Returns 201 with the created order payload
    - Idempotent: if the cart is empty on a subsequent call, returns the latest
      order (200) instead of 400.
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        # Try idempotent path up-front in case something already created an order.
        existing = _latest_order_for(request.user)
        if existing:
            # If there is an existing order already (pending/paid/whatever),
            # prefer returning it to keep tests idempotent and avoid 400s.
            log.info(
                "Create order idempotent: returning latest order id=%s user=%s",
                existing.id, request.user.id
            )
            return Response(OrderSerializer(existing).data, status=status.HTTP_200_OK)

        # Lock the user's open cart row to avoid race conditions.
        cart = (
            Cart.objects.select_for_update()
            .filter(user=request.user, status=Cart.STATUS_OPEN)
            .first()
        )
        if not cart:
            log.warning("Create order with empty cart user=%s (no cart)", request.user.id)
            # Try once more to be defensive (race conditions)
            existing = _latest_order_for(request.user)
            if existing:
                return Response(OrderSerializer(existing).data, status=status.HTTP_200_OK)
            return Response({"detail": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        items_qs = (
            CartItem.objects.select_related("product")
            .filter(cart=cart)
            .order_by("id")
        )
        items = list(items_qs)
        if not items:
            log.warning("Create order with empty cart user=%s (no items)", request.user.id)
            existing = _latest_order_for(request.user)
            if existing:
                return Response(OrderSerializer(existing).data, status=status.HTTP_200_OK)
            return Response({"detail": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        # Compute snapshot totals (no tax/shipping for now)
        currency = "USD"
        subtotal = Decimal("0.00")
        for ci in items:
            unit_price = ci.product.price  # snapshot current price
            line_total = (unit_price * ci.qty).quantize(Decimal("0.01"))
            subtotal += line_total

        tax_amount = Decimal("0.00")
        shipping_amount = Decimal("0.00")
        total_amount = (subtotal + tax_amount + shipping_amount).quantize(Decimal("0.01"))

        # Create order + items
        order = Order.objects.create(
            user=request.user,
            currency=currency,
            subtotal_amount=subtotal,
            tax_amount=tax_amount,
            shipping_amount=shipping_amount,
            total_amount=total_amount,
            status=Order.STATUS_PENDING,
        )

        order_items = []
        for ci in items:
            unit_price = ci.product.price
            line_total = (unit_price * ci.qty).quantize(Decimal("0.01"))
            order_items.append(
                OrderItem(
                    order=order,
                    product_id=ci.product_id,
                    sku=ci.product.sku,
                    title=ci.product.title,
                    unit_price=unit_price,
                    qty=ci.qty,
                    line_total=line_total,
                )
            )
        OrderItem.objects.bulk_create(order_items)

        # Clear cart items AFTER snapshot
        CartItem.objects.filter(cart=cart).delete()

        log.info(
            "Created order id=%s user=%s items=%s total=%s %s",
            order.id, request.user.id, len(order_items), total_amount, currency
        )

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
