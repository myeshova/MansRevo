from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.contrib.auth import get_user_model  # <-- This exact line fixes the unrecognized error
from .models import Product, StorefrontConfig

def store_view(request):
    # TEMPORARY: Auto-generate admin credentials safely on the live server
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'MansRevo2026!')

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
    }
    return render(request, 'shop/store.html', context)

def product_detail_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'shop/product_detail.html', {'product': product})
