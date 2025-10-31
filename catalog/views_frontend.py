# catalog/views_frontend.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.urls import reverse
from catalog.models import Product
from cart.models import Cart, CartItem

@login_required
def product_list(request):
    products = Product.objects.filter(is_active=True).order_by("id")
    return render(request, "catalog/products.html", {"products": products})

@login_required
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    return render(request, "catalog/product_detail.html", {"product": product})

@login_required
@require_POST
def add_to_cart(request, product_id):
    qty = int(request.POST.get("qty", "1") or "1")
    qty = max(1, qty)

    cart, _ = Cart.objects.get_or_create(user=request.user, status=Cart.STATUS_OPEN)
    # upsert item
    item = CartItem.objects.filter(cart=cart, product_id=product_id).first()
    if item:
        item.qty += qty
        item.save(update_fields=["qty"])
    else:
        CartItem.objects.create(cart=cart, product_id=product_id, qty=qty, unit_price=Product.objects.get(pk=product_id).price)

    return redirect(reverse("front-cart"))

@login_required
def view_cart(request):
    cart = Cart.objects.filter(user=request.user, status=Cart.STATUS_OPEN).first()
    items = []
    subtotal = 0
    if cart:
        items = list(CartItem.objects.select_related("product").filter(cart=cart).order_by("id"))
        for it in items:
            subtotal += float(it.unit_price) * it.qty
    return render(request, "cart/cart.html", {"cart": cart, "items": items, "subtotal": subtotal})

@login_required
@require_POST
def remove_from_cart(request, item_id):
    CartItem.objects.filter(id=item_id, cart__user=request.user, cart__status=Cart.STATUS_OPEN).delete()
    return redirect(reverse("front-cart"))
