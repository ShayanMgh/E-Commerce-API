import logging
from decimal import Decimal
from django.conf import settings
from django.db import transaction
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

import stripe
from orders.models import Order

log = logging.getLogger("payments.stripe")

def _amount_minor_units(amount: Decimal) -> int:
    # USD: cents. For zero-decimal currencies adapt later.
    return int((amount * Decimal("100")).quantize(Decimal("1")))

class CreatePaymentIntentView(APIView):
    """
    POST /api/payments/create-intent/
    Body: { "order_id": <int> }
    - Validates ownership and PENDING status
    - Creates or retrieves a Stripe PaymentIntent for order.total_amount
    - Saves payment_intent_id on Order
    - Returns { client_secret, payment_intent_id }
    """
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        order_id = request.data.get("order_id")
        if not order_id:
            return Response({"detail": "order_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.objects.select_for_update().get(pk=order_id)
        except Order.DoesNotExist:
            return Response({"detail": "order not found"}, status=404)

        if not (request.user.is_staff or order.user_id == request.user.id):
            return Response({"detail": "forbidden"}, status=403)

        if order.status != Order.STATUS_PENDING:
            return Response({"detail": f"order not pending (status={order.status})"}, status=400)

        if order.total_amount <= 0:
            return Response({"detail": "order total must be > 0"}, status=400)

        # Configure Stripe
        secret = getattr(settings, "STRIPE_SECRET_KEY", None)
        if not secret:
            return Response({"detail": "STRIPE_SECRET_KEY not configured"}, status=500)
        stripe.api_key = secret

        amount = _amount_minor_units(order.total_amount)
        currency = (order.currency or "USD").lower()

        try:
            if order.payment_intent_id:
                # Retrieve existing
                pi = stripe.PaymentIntent.retrieve(order.payment_intent_id)
                # If amounts differ (rare), update the amount if allowed
                # Note: amount update rules vary by status; for simplicity we re-use as-is if amounts match,
                # otherwise we create a new PI.
                if int(pi["amount"]) != amount or pi["currency"] != currency:
                    log.info("Existing PI mismatch; creating new PI order=%s", order.id)
                    pi = stripe.PaymentIntent.create(
                        amount=amount,
                        currency=currency,
                        metadata={"order_id": str(order.id), "public_id": str(order.public_id)},
                        automatic_payment_methods={"enabled": True},
                    )
                    order.payment_intent_id = pi["id"]
                    order.save(update_fields=["payment_intent_id"])
            else:
                # Create new PI
                pi = stripe.PaymentIntent.create(
                    amount=amount,
                    currency=currency,
                    metadata={"order_id": str(order.id), "public_id": str(order.public_id)},
                    automatic_payment_methods={"enabled": True},
                )
                order.payment_intent_id = pi["id"]
                order.save(update_fields=["payment_intent_id"])

            client_secret = pi.get("client_secret")
            log.info("Created/Retrieved PI order=%s pi=%s amount=%s %s", order.id, order.payment_intent_id, amount, currency)
            return Response(
                {"payment_intent_id": order.payment_intent_id, "client_secret": client_secret},
                status=200,
            )
        except stripe.error.StripeError as e:
            log.error("Stripe error order=%s type=%s msg=%s", order.id, type(e).__name__, str(e))
            return Response({"detail": "stripe_error", "message": str(e)}, status=400)
