# payments/views.py
import json
import logging
from decimal import Decimal

import stripe
from django.conf import settings
from django.db import transaction
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from orders.models import Order
from .models import StripeEvent

log = logging.getLogger("payments.stripe")


def _amount_minor_units(amount: Decimal) -> int:
    """Convert Decimal major units (e.g., USD) to minor units (cents)."""
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
                # If mismatch, create a new PI (simple/dev-friendly strategy)
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
            log.info(
                "Created/Retrieved PI order=%s pi=%s amount=%s %s",
                order.id, order.payment_intent_id, amount, currency
            )
            return Response(
                {"payment_intent_id": order.payment_intent_id, "client_secret": client_secret},
                status=200,
            )
        except Exception as e:
            # Broad catch because this environment's `stripe` module lacks `stripe.error`.
            log.error("Payments error order=%s type=%s msg=%s", order.id, type(e).__name__, str(e))
            return Response({"detail": "payments_error", "message": str(e)}, status=400)


class StripeWebhookView(APIView):
    """
    POST /api/payments/webhook/
    Verifies Stripe signature (unless dev override enabled),
    handles:
      - payment_intent.succeeded => mark order paid + decrement stock
      - payment_intent.payment_failed => mark order failed (no stock change)
    """
    authentication_classes = []  # Stripe calls this (no auth)
    permission_classes = []

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request):
        payload = request.body
        sig_header = request.headers.get("Stripe-Signature", "")

        secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", None)
        allow_unverified = getattr(settings, "PAYMENTS_ALLOW_UNVERIFIED_WEBHOOKS", False)

        try:
            if allow_unverified or not secret:
                event = json.loads(payload.decode("utf-8"))
            else:
                event = stripe.Webhook.construct_event(
                    payload=payload, sig_header=sig_header, secret=secret
                )
        except Exception as e:
            log.error("Webhook verification failed: %s", e)
            return Response({"detail": "invalid_signature"}, status=status.HTTP_400_BAD_REQUEST)

        event_id = event.get("id")
        event_type = event.get("type")
        data = event.get("data", {}).get("object", {})

        # Idempotency: ensure we only process each event once
        try:
            with transaction.atomic():
                StripeEvent.objects.create(event_id=event_id)
        except Exception:
            log.info("Duplicate webhook event ignored: %s", event_id)
            return Response({"status": "ignored"}, status=200)

        try:
            if event_type == "payment_intent.succeeded":
                pi_id = data.get("id")
                metadata = data.get("metadata") or {}
                order_id = metadata.get("order_id")
                if not order_id:
                    raise ValueError("Missing order_id in PaymentIntent metadata")

                order = Order.objects.get(pk=order_id)
                if order.payment_intent_id and order.payment_intent_id != pi_id:
                    log.warning(
                        "PI mismatch for order=%s saved=%s incoming=%s",
                        order.id, order.payment_intent_id, pi_id
                    )
                if not order.payment_intent_id:
                    order.payment_intent_id = pi_id
                    order.save(update_fields=["payment_intent_id"])

                order.mark_paid_and_decrement_stock()
                log.info("Order marked PAID and stock decremented: order=%s pi=%s", order.id, pi_id)
                return Response({"status": "ok"}, status=200)

            elif event_type == "payment_intent.payment_failed":
                pi_id = data.get("id")
                metadata = data.get("metadata") or {}
                order_id = metadata.get("order_id")
                if order_id:
                    Order.objects.filter(pk=order_id).update(status=Order.STATUS_FAILED, updated_at=now())
                    log.info("Order marked FAILED: order=%s pi=%s", order_id, pi_id)
                return Response({"status": "ok"}, status=200)

            else:
                log.info("Unhandled event type: %s", event_type)
                return Response({"status": "unhandled"}, status=200)

        except Exception as e:
            log.error("Webhook processing error: %s", e, exc_info=True)
            return Response({"detail": "webhook_processing_error", "message": str(e)}, status=400)
