from django.urls import path
from .views import CreatePaymentIntentView, StripeWebhookView

urlpatterns = [
    path("payments/create-intent/", CreatePaymentIntentView.as_view(), name="payments-create-intent"),
    path("payments/webhook/", StripeWebhookView.as_view(), name="payments-webhook"),
]
