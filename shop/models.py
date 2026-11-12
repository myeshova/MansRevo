import uuid

from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    image = models.ImageField(upload_to="products/", blank=True, null=True)

    def __str__(self):
        return f"{self.brand} - {self.name}"


class StorefrontConfig(models.Model):
    HERO_EFFECT_CHOICES = [
        ("none", "No animation"),
        ("rise", "Rise and fade"),
        ("fade", "Soft fade"),
        ("zoom", "Gentle zoom"),
        ("focus", "Focus reveal"),
    ]

    title = models.CharField(max_length=200, default="REVOLUTIONARY TAILORING")
    subtitle = models.CharField(max_length=200, default="The Autumn / Winter Collection")
    banner_image = models.ImageField(upload_to="storefront/", help_text="Upload your main full-page header image here.")
    hero_effect = models.CharField(
        max_length=10,
        choices=HERO_EFFECT_CHOICES,
        default="rise",
        verbose_name="Hero text effect",
    )

    class Meta:
        verbose_name = "Storefront Configuration"
        verbose_name_plural = "Storefront Configuration"

    def __str__(self):
        return "Main Storefront Settings"


class Order(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_NEEDS_REVIEW = "needs_review"
    STATUS_FAILED = "failed"
    STATUS_EXPIRED = "expired"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending payment"),
        (STATUS_PAID, "Paid"),
        (STATUS_NEEDS_REVIEW, "Paid — inventory review needed"),
        (STATUS_FAILED, "Payment failed"),
        (STATUS_EXPIRED, "Checkout expired"),
    ]

    order_number = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    stripe_session_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    email = models.EmailField(blank=True)
    currency = models.CharField(max_length=3, default="usd")
    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_name = models.CharField(max_length=255, blank=True)
    shipping_address_line1 = models.CharField(max_length=255, blank=True)
    shipping_address_line2 = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=120, blank=True)
    shipping_state = models.CharField(max_length=120, blank=True)
    shipping_postal_code = models.CharField(max_length=40, blank=True)
    shipping_country = models.CharField(max_length=2, blank=True)
    confirmation_email_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {str(self.order_number)[:8]}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL)
    product_name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity} × {self.product_name}"
