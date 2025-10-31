# payments/views_refund.py
import logging
from decimal import Decimal
from django.conf import settings
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
import stripe

from orders.models import Order

log = logging.getLogger("payments.stripe")

def _amount_minor(amount: Decimal) -> int:
    """
    Convert a Decimal major unit (e.g., USD dollars) to minor units (cents).
    """
    return int((amount * Decimal("100")).quantize(Decimal("1")))

class CreateRefundView(APIView):
    """
    POST /api/payments/refund/
    Body: { "order_id": int, "amount"?: "Decimal as string" }

    Behavior:
    - Requires authenticated user
    - User must own the order or be staff
    - Order must be PAID (we keep status unchanged to avoid migrations for now)
    - If "amount" omitted => full refund of order.total_amount
    - Returns { refund_id, status }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        order_id = request.data.get("order_id")
        if not order_id:
            return Response({"detail": "order_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            return Response({"detail": "order not found"}, status=status.HTTP_404_NOT_FOUND)

        # AuthZ: owner or staff
        if not (request.user.is_staff or order.user_id == request.user.id):
            return Response({"detail": "forbidden"}, status=status.HTTP_403_FORBIDDEN)

        # Require paid order
        if getattr(Order, "STATUS_PAID", "paid") != order.status:
            return Response({"detail": f"order not paid (status={order.status})"}, status=status.HTTP_400_BAD_REQUEST)

        # Stripe key
        secret = getattr(settings, "STRIPE_SECRET_KEY", None)
        if not secret:
            return Response({"detail": "STRIPE_SECRET_KEY not configured"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        stripe.api_key = secret

        # Determine amount (default full)
        req_amount = request.data.get("amount")
        if req_amount is None:
            amount_minor = _amount_minor(order.total_amount)
        else:
            try:
                amount_minor = _amount_minor(Decimal(str(req_amount)))
            except Exception:
                return Response({"detail": "invalid amount"}, status=status.HTTP_400_BAD_REQUEST)

        if not order.payment_intent_id:
            return Response({"detail": "order has no payment_intent_id"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refund = stripe.Refund.create(
                payment_intent=order.payment_intent_id,
                amount=amount_minor,
            )
            log.info(
                "Refund created user=%s order=%s amount_minor=%s refund_id=%s",
                request.user.id, order.id, amount_minor, refund.get("id")
            )
            return Response(
                {"refund_id": refund.get("id"), "status": refund.get("status")},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            log.error("Refund error order=%s type=%s msg=%s", order.id, type(e).__name__, str(e))
            return Response({"detail": "refund_error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
