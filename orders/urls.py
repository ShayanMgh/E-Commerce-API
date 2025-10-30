from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, CreateOrderView

router = DefaultRouter()
router.register(r"orders", OrderViewSet, basename="orders")

urlpatterns = [
    path("checkout/create-order/", CreateOrderView.as_view(), name="create-order"),
    path("", include(router.urls)),
]
