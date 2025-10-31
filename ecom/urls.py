from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from .views import checkout_page  # only the HTML demo view lives here
from catalog.views_frontend import product_list, product_detail, add_to_cart, view_cart, remove_from_cart

def healthz(_request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path("admin/", admin.site.urls),

    # API: health/schema/docs
    path("api/healthz/", healthz, name="healthz"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),

    # API: app routers
    path("api/", include("users.urls")),
    path("api/", include("catalog.urls")),
    path("api/", include("cart.urls")),
    path("api/", include("orders.urls")),
    path("api/", include("payments.urls")),  # Stripe endpoints are defined inside payments/urls.py

    # Minimal demo checkout page
    path("checkout/", checkout_page, name="checkout"),
    
    path("store/", product_list, name="front-products"),
    path("store/p/<slug:slug>/", product_detail, name="front-product-detail"),    
    path("cart/", view_cart, name="front-cart"),
    path("cart/add/<int:product_id>/", add_to_cart, name="front-add-to-cart"),
    path("cart/remove/<int:item_id>/", remove_from_cart, name="front-remove-from-cart"),
]
