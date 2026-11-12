from django.contrib import admin
from .models import Product, StorefrontConfig, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "product_name", "brand", "unit_price", "quantity")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number", "status", "email", "total_amount", "currency", "created_at")
    list_filter = ("status", "currency", "created_at")
    search_fields = ("email", "stripe_session_id", "stripe_payment_intent_id")
    readonly_fields = ("order_number", "stripe_session_id", "stripe_payment_intent_id", "created_at", "updated_at")
    inlines = (OrderItemInline,)


admin.site.register(Product)
admin.site.register(StorefrontConfig)
