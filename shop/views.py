from decimal import Decimal
import os

import stripe

from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.db.models import Q
from django.views.decorators.http import require_POST
from .models import Product, StorefrontConfig


def _get_bag(request):
    bag = request.session.get("bag", {})
    if not isinstance(bag, dict):
        bag = {}
        request.session["bag"] = bag
    return bag


def _bag_count(request):
    count = 0
    for quantity in _get_bag(request).values():
        try:
            count += max(0, int(quantity))
        except (TypeError, ValueError):
            continue
    return count

def store_view(request):
    # Capture whatever text the user types into the search bar
    query = request.GET.get('search', '').strip()
    config = StorefrontConfig.objects.first()

    if query:
        all_products = Product.objects.filter(
            Q(name__icontains=query) | Q(brand__icontains=query)
        )
    else:
        all_products = Product.objects.all()

    context = {
        'products': all_products,
        'query': query,
        'config': config,
        'bag_count': _bag_count(request),
    }
    return render(request, 'shop/store.html', context)

def product_detail_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'shop/product_detail.html', {
        'product': product,
        'bag_count': _bag_count(request),
    })


@require_POST
def add_to_bag(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    bag = _get_bag(request)
    key = str(product.pk)

    try:
        quantity = int(bag.get(key, 0))
    except (TypeError, ValueError):
        quantity = 0

    if product.stock <= 0:
        messages.error(request, "This item is currently out of stock.")
    elif quantity >= product.stock:
        messages.warning(request, "Your bag already contains all available stock for this item.")
    else:
        bag[key] = quantity + 1
        request.session["bag"] = bag
        messages.success(request, f"{product.name} was added to your bag.")

    return redirect("bag")


def bag_view(request):
    bag = _get_bag(request)
    product_ids = []
    for raw_id in bag:
        try:
            product_ids.append(int(raw_id))
        except (TypeError, ValueError):
            continue

    products = Product.objects.filter(pk__in=product_ids).in_bulk()
    items = []
    subtotal = Decimal("0.00")
    cleaned_bag = {}

    for raw_id, raw_quantity in bag.items():
        try:
            product_id = int(raw_id)
            quantity = int(raw_quantity)
        except (TypeError, ValueError):
            continue

        product = products.get(product_id)
        if product is None or product.stock <= 0 or quantity <= 0:
            continue

        quantity = min(quantity, product.stock)
        cleaned_bag[str(product_id)] = quantity
        line_total = product.price * quantity
        subtotal += line_total
        items.append({
            "product": product,
            "quantity": quantity,
            "line_total": line_total,
        })

    if cleaned_bag != bag:
        request.session["bag"] = cleaned_bag

    return render(request, "shop/bag.html", {
        "items": items,
        "subtotal": subtotal,
        "bag_count": sum(item["quantity"] for item in items),
    })


@require_POST
def update_bag(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    bag = _get_bag(request)
    key = str(product.pk)

    if request.POST.get("action") == "remove":
        bag.pop(key, None)
        messages.info(request, f"{product.name} was removed from your bag.")
    else:
        try:
            quantity = int(request.POST.get("quantity", "1"))
        except (TypeError, ValueError):
            messages.error(request, "Enter a valid quantity.")
            return redirect("bag")

        if quantity <= 0 or product.stock <= 0:
            bag.pop(key, None)
            messages.info(request, f"{product.name} was removed from your bag.")
        else:
            if quantity > product.stock:
                quantity = product.stock
                messages.warning(request, f"Quantity adjusted to the {product.stock} currently in stock.")
            bag[key] = quantity
            messages.success(request, "Your bag was updated.")

    request.session["bag"] = bag
    return redirect("bag")


@require_POST
def create_checkout_session(request):
    bag = _get_bag(request)
    product_ids = []
    for raw_id in bag:
        try:
            product_ids.append(int(raw_id))
        except (TypeError, ValueError):
            continue

    products = Product.objects.filter(pk__in=product_ids).in_bulk()
    line_items = []
    cleaned_bag = {}
    for raw_id, raw_quantity in bag.items():
        try:
            product_id = int(raw_id)
            quantity = int(raw_quantity)
        except (TypeError, ValueError):
            continue

        product = products.get(product_id)
        if product is None or product.stock <= 0 or quantity <= 0:
            continue
        quantity = min(quantity, product.stock)
        cleaned_bag[str(product_id)] = quantity
        line_items.append({
            "price_data": {
                "currency": "usd",
                "unit_amount": int(product.price * 100),
                "product_data": {"name": product.name},
            },
            "quantity": quantity,
        })

    if not line_items:
        messages.error(request, "Your bag is empty or its items are unavailable.")
        return redirect("bag")

    request.session["bag"] = cleaned_bag
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe.api_key:
        messages.error(request, "Checkout is not configured yet.")
        return redirect("bag")

    session = stripe.checkout.Session.create(
        ui_mode="hosted_page",
        mode="payment",
        billing_address_collection="auto",
        phone_number_collection={"enabled": False},
        automatic_tax={"enabled": False},
        allow_promotion_codes=False,
        submit_type="auto",
        integration_identifier="hosted_web_0001",
        origin_context="web",
        success_url=request.build_absolute_uri(reverse("checkout_success")) + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=request.build_absolute_uri(reverse("bag")),
        line_items=line_items,
    )
    return redirect(session.url, permanent=False)


def checkout_success(request):
    return render(request, "shop/checkout_success.html")

