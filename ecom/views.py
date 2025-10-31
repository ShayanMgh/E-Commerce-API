from django.conf import settings
from django.shortcuts import render

def checkout_page(request):
    return render(
        request,
        "checkout.html",
        {
            "STRIPE_PUBLISHABLE_KEY": getattr(settings, "STRIPE_PUBLISHABLE_KEY", "pk_test_xxx"),
        },
    )
