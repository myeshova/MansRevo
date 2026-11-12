import logging
import os
from decimal import Decimal

import stripe
from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Product, StorefrontConfig, Order, OrderItem

logger = logging.getLogger(__name__)


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
    query = request.GET.get("search", "").strip()
    config = StorefrontConfig.objects.first()
    all_products = Product.objects.filter(
        Q(name__icontains=query) | Q(brand__icontains=query)
    ) if query else Product.objects.all()
    return render(request, "shop/store.html", {
        "products": all_products,
        "query": query,
        "config": config,
        "bag_count": _bag_count(request),
    })


def product_detail_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, "shop/product_detail.html", {
        "product": product,
        "bag_count": _bag_count(request),
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
        items.append({"product": product, "quantity": quantity, "line_total": line_total})

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


def _money_from_cents(value):
    return (Decimal(int(value or 0)) / Decimal("100")).quantize(Decimal("0.01"))


def _customer_shipping_data(session):
    collected = session.get("collected_information") or {}
    shipping = collected.get("shipping_details") or session.get("shipping_details") or {}
    address = shipping.get("address") or {}
    customer = session.get("customer_details") or {}
    return {
        "email": customer.get("email") or session.get("customer_email") or "",
        "name": shipping.get("name") or customer.get("name") or "",
        "line1": address.get("line1") or "",
        "line2": address.get("line2") or "",
        "city": address.get("city") or "",
        "state": address.get("state") or "",
        "postal_code": address.get("postal_code") or "",
        "country": address.get("country") or "",
    }


def _send_order_confirmation(order):
    if not order.email:
        raise RuntimeError("Stripe did not provide a customer email for this paid order.")
    if not settings.EMAIL_HOST_PASSWORD and not settings.DEBUG:
        raise RuntimeError("Gmail SMTP is not configured in the production environment.")
    lines = [
        f"Order {str(order.order_number)[:8]}",
        "",
        "Items:",
    ]
    for item in order.items.all():
        lines.append(f"{item.quantity} × {item.product_name} — ${item.unit_price:.2f} each")
    lines.extend([
        "",
        f"Subtotal: ${order.subtotal_amount:.2f}",
        f"Shipping: ${order.shipping_amount:.2f}",
        f"Tax: ${order.tax_amount:.2f}",
        f"Total: ${order.total_amount:.2f}",
        "",
        "We’ve received your payment and will process your order.",
        "MansRevo",
    ])
    sent = send_mail(
        f"MansRevo order confirmation {str(order.order_number)[:8]}",
        "\n".join(lines),
        settings.DEFAULT_FROM_EMAIL,
        [order.email],
        fail_silently=False,
    )
    return sent == 1


def _fulfill_paid_session(session):
    if session.get("payment_status") not in {"paid", "no_payment_required"}:
        return None
    metadata = session.get("metadata") or {}
    order_id = metadata.get("order_id") or session.get("client_reference_id")
    if not order_id:
        raise ValueError("Checkout Session does not contain an order reference.")

    customer = _customer_shipping_data(session)
    total_details = session.get("total_details") or {}
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order_id)
        if order.status not in {Order.STATUS_PAID, Order.STATUS_NEEDS_REVIEW}:
            order_items = list(order.items.select_related("product").all())
            products = {
                product.pk: product
                for product in Product.objects.select_for_update().filter(
                    pk__in=[item.product_id for item in order_items if item.product_id]
                ).order_by("pk")
            }
            inventory_available = all(
                item.product_id in products and products[item.product_id].stock >= item.quantity
                for item in order_items
            )
            if inventory_available:
                for item in order_items:
                    product = products[item.product_id]
                    product.stock -= item.quantity
                    product.save(update_fields=["stock"])
                order.status = Order.STATUS_PAID
            else:
                order.status = Order.STATUS_NEEDS_REVIEW
                logger.error("Paid order %s needs inventory review.", order.pk)

        order.stripe_session_id = session.get("id") or order.stripe_session_id
        order.stripe_payment_intent_id = session.get("payment_intent") or ""
        order.email = customer["email"] or order.email
        order.currency = (session.get("currency") or "usd").lower()
        order.shipping_name = customer["name"]
        order.shipping_address_line1 = customer["line1"]
        order.shipping_address_line2 = customer["line2"]
        order.shipping_city = customer["city"]
        order.shipping_state = customer["state"]
        order.shipping_postal_code = customer["postal_code"]
        order.shipping_country = customer["country"]
        order.shipping_amount = _money_from_cents(total_details.get("amount_shipping"))
        order.tax_amount = _money_from_cents(total_details.get("amount_tax"))
        order.total_amount = _money_from_cents(session.get("amount_total"))

        if order.email and not order.confirmation_email_sent_at:
            email_sent = _send_order_confirmation(order)
            if email_sent:
                order.confirmation_email_sent_at = timezone.now()
            elif not settings.DEBUG:
                raise RuntimeError("Order confirmation email was not sent.")
        order.save()
        return order


def _mark_order_from_session(session, status):
    metadata = session.get("metadata") or {}
    order_id = metadata.get("order_id") or session.get("client_reference_id")
    if order_id:
        Order.objects.filter(pk=order_id, status=Order.STATUS_PENDING).update(status=status)


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
    cleaned_bag = {}
    product_quantities = []
    subtotal = Decimal("0.00")
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
        product_quantities.append((product, quantity))
        subtotal += product.price * quantity

    if not product_quantities:
        messages.error(request, "Your bag is empty or its items are unavailable.")
        return redirect("bag")

    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe.api_key or stripe.api_key.endswith("..."):
        messages.error(request, "Stripe test or live keys have not been configured on this server.")
        return redirect("bag")
    order = Order.objects.create(
        subtotal_amount=subtotal,
        total_amount=subtotal,
        currency="usd",
    )
    OrderItem.objects.bulk_create([
        OrderItem(
            order=order,
            product=product,
            product_name=product.name,
            brand=product.brand,
            unit_price=product.price,
            quantity=quantity,
        )
        for product, quantity in product_quantities
    ])
    line_items = [{
        "price_data": {
            "currency": "usd",
            "unit_amount": int(product.price * 100),
            "tax_behavior": "exclusive",
            "product_data": {"name": product.name},
        },
        "quantity": quantity,
    } for product, quantity in product_quantities]

    try:
        session = stripe.checkout.Session.create(
            ui_mode="hosted",
            mode="payment",
            billing_address_collection="auto",
            phone_number_collection={"enabled": False},
            automatic_tax={"enabled": False},
            allow_promotion_codes=False,
            submit_type="auto",
            integration_identifier="hosted_web_0002",
            origin_context="web",
            client_reference_id=str(order.pk),
            metadata={"order_id": str(order.pk)},
            success_url=request.build_absolute_uri(reverse("checkout_success")) + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=request.build_absolute_uri(reverse("bag")),
            line_items=line_items,
        )
    except Exception:
        order.status = Order.STATUS_FAILED
        order.save(update_fields=["status", "updated_at"])
        logger.exception("Stripe could not create a Checkout Session for order %s.", order.pk)
        messages.error(request, "Stripe could not start checkout. Please try again or contact the store.")
        return redirect("bag")

    order.stripe_session_id = session.id
    order.save(update_fields=["stripe_session_id", "updated_at"])
    request.session["bag"] = cleaned_bag
    return redirect(session.url, permanent=False)


def checkout_success(request):
    session_id = request.GET.get("session_id")
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    order = None
    payment_confirmed = False
    if session_id and stripe.api_key:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.get("payment_status") in {"paid", "no_payment_required"}:
                order = _fulfill_paid_session(session)
                payment_confirmed = order is not None
                request.session["bag"] = {}
        except Exception:
            logger.exception("Could not confirm Checkout Session on the return page.")
    return render(request, "shop/checkout_success.html", {
        "order": order,
        "payment_confirmed": payment_confirmed,
    })


@csrf_exempt
@require_POST
def stripe_webhook(request):
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if not stripe.api_key or not endpoint_secret:
        logger.error("Stripe webhook is missing STRIPE_SECRET_KEY or STRIPE_WEBHOOK_SECRET.")
        return HttpResponse(status=503)
    signature = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    try:
        event = stripe.Webhook.construct_event(request.body, signature, endpoint_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponseBadRequest("Invalid Stripe webhook signature or payload.")

    event_type = event.get("type")
    session = event.get("data", {}).get("object", {})
    try:
        if event_type in {"checkout.session.completed", "checkout.session.async_payment_succeeded"}:
            if session.get("payment_status") in {"paid", "no_payment_required"}:
                _fulfill_paid_session(session)
        elif event_type == "checkout.session.async_payment_failed":
            _mark_order_from_session(session, Order.STATUS_FAILED)
        elif event_type == "checkout.session.expired":
            _mark_order_from_session(session, Order.STATUS_EXPIRED)
    except Order.DoesNotExist:
        logger.exception("Stripe webhook referred to an order that does not exist.")
        return HttpResponse(status=500)
    except Exception:
        logger.exception("Stripe webhook handling failed for event %s.", event_type)
        return HttpResponse(status=500)
    return HttpResponse(status=200)
