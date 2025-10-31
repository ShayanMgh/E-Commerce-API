# orders/tests/test_core.py
"""
Core e-commerce flow tests:
1) Cart -> Order happy path
2) PaymentIntent creation (mocked Stripe)
3) Webhook idempotency: stock decremented once even if event delivered twice
"""

from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from catalog.models import Category, Product
from orders.models import Order

User = get_user_model()


class CoreFlowTests(TestCase):
    def setUp(self):
        # Users
        self.user = User.objects.create_user(
            email="alice@example.com", password="A-secure-pass1", first_name="Alice", last_name="A"
        )
        self.staff = User.objects.create_user(
            email="admin@example.com", password="Admin-S3cret!", is_staff=True
        )

        # Catalog
        self.cat = Category.objects.create(name="Phones", description="Smartphones", is_active=True)
        self.product = Product.objects.create(
            category=self.cat,
            sku="IPHN13",
            title="iPhone 13",
            description="128GB, Blue",
            price=Decimal("799.00"),
            currency="USD",
            stock_qty=25,
            is_active=True,
        )

        # Client uses force_authenticate for speed (avoid JWT flow in unit tests)
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def _add_cart_item(self, qty=2):
        resp = self.client.post(
            "/api/cart/items/",
            {"product_id": self.product.id, "qty": qty},
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        return resp.json()

    def _create_order(self):
        resp = self.client.post("/api/checkout/create-order/", {}, format="json")
        self.assertIn(resp.status_code, (200, 201), resp.content)
        resp = self.client.post("/api/checkout/create-order/", {}, format="json")
        self.assertIn(resp.status_code, (200, 201), resp.content)
        return resp.json()

    def test_01_cart_to_order_happy_path(self):
        """Add to cart -> create order with expected totals and items."""
        self._add_cart_item(qty=2)
        order = self._create_order()

        self.assertEqual(order["status"], "pending")
        self.assertEqual(Decimal(order["subtotal_amount"]), Decimal("1598.00"))
        self.assertEqual(Decimal(order["total_amount"]), Decimal("1598.00"))
        self.assertEqual(len(order["items"]), 1)
        self.assertEqual(order["items"][0]["qty"], 2)
        self.assertEqual(order["items"][0]["unit_price"], "799.00")

    @patch("payments.views.stripe.PaymentIntent.create")
    def test_02_payment_intent_creation(self, mock_pi_create):
        """Create PaymentIntent for pending order and store PI id on Order."""
        self._add_cart_item(qty=2)
        order_data = self._create_order()
        order_id = order_data["id"]

        # Mock Stripe PI create
        mock_pi_create.return_value = {
            "id": "pi_test_123",
            "client_secret": "pi_test_123_secret_abc",
            "amount": 159800,
            "currency": "usd",
        }

        # Call PI endpoint
        resp = self.client.post(
            "/api/payments/create-intent/",
            {"order_id": order_id},
            format="json",
        )
        self.assertIn(resp.status_code, (200, 201), resp.content)
        payload = resp.json()
        self.assertEqual(payload["payment_intent_id"], "pi_test_123")
        self.assertEqual(payload["client_secret"], "pi_test_123_secret_abc")

        # Confirm it persisted on the Order
        o = Order.objects.get(pk=order_id)
        self.assertEqual(o.payment_intent_id, "pi_test_123")

    def test_03_webhook_idempotency_stock_once(self):
        """
        When payment_intent.succeeded is posted twice:
        - order goes to PAID
        - product stock decremented only once
        """
        initial_stock = self.product.stock_qty

        # Create order pending
        self._add_cart_item(qty=2)
        order_data = self._create_order()
        order_id = order_data["id"]

        # Simulate we already created a PI and saved it
        o = Order.objects.get(pk=order_id)
        o.payment_intent_id = "pi_idem_1"
        o.save(update_fields=["payment_intent_id"])

        event = {
            "id": "evt_test_1",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_idem_1",
                    "metadata": {"order_id": str(order_id), "public_id": str(o.public_id)},
                    "amount": 159800,
                    "currency": "usd",
                }
            },
        }

        # First delivery
        resp1 = self.client.post("/api/payments/webhook/", event, format="json")
        self.assertEqual(resp1.status_code, 200, resp1.content)
        self.product.refresh_from_db()
        o.refresh_from_db()
        self.assertEqual(o.status, Order.STATUS_PAID)
        self.assertEqual(self.product.stock_qty, initial_stock - 2)

        # Second (duplicated) delivery
        resp2 = self.client.post("/api/payments/webhook/", event, format="json")
        self.assertEqual(resp2.status_code, 200, resp2.content)
        self.product.refresh_from_db()
        o.refresh_from_db()
        # still PAID, stock unchanged further
        self.assertEqual(o.status, Order.STATUS_PAID)
        self.assertEqual(self.product.stock_qty, initial_stock - 2)
