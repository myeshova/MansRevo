from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Product, StorefrontConfig

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
    }
    return render(request, 'shop/store.html', context)

def product_detail_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'shop/product_detail.html', {'product': product})
