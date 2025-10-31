from django.conf import settings
from django.shortcuts import render

def checkout_page(request):
    """
    Minimal demo page that uses Stripe.js and your API.
    Expects STRIPE_PUBLISHABLE_KEY in settings (from .env).
    """
    return render(
        request,
        "checkout.html",
        {
            "STRIPE_PUBLISHABLE_KEY": getattr(settings, "STRIPE_PUBLISHABLE_KEY", "pk_test_xxx"),
        },
    )
