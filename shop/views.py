from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Product
from .models import Product, StorefrontConfig

def store_view(request):
    # Capture whatever text the user types into the search bar
    query = request.GET.get('search', '').strip()

    config = StorefrontConfig.objects.first()

    if query:
        # Search if the text matches either the item name OR the brand name
        all_products = Product.objects.filter(
            Q(name__icontains=query) | Q(brand__icontains=query)
        )
    else:
        # If the search bar is empty, display all menswear inventory as usual
        all_products = Product.objects.all()

    context = {
        'products': all_products,
        'query': query,
        'config': config,  # <-- Pass your custom settings to HTML
    }
    return render(request, 'shop/store.html', context)

def product_detail_view(request, pk):
    # Fetch the specific item by its ID, or throw a 404 page if it doesn't exist
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'shop/product_detail.html', {'product': product})
