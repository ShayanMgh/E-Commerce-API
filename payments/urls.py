from django.urls import path
from .views import CreatePaymentIntentView

urlpatterns = [
    path("payments/create-intent/", CreatePaymentIntentView.as_view(), name="payments-create-intent"),
]
