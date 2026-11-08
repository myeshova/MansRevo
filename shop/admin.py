from django.contrib import admin
from .models import Product, StorefrontConfig
# Register your models here.
admin.site.register(Product)
admin.site.register(StorefrontConfig)
