from django.urls import path
from . import views

urlpatterns = [
    path('', views.store_view, name='store'),
    path('product/<int:pk>/', views.product_detail_view, name='product_detail'),  # <-- Add this exact line
    path('bag/', views.bag_view, name='bag'),
    path('checkout/', views.create_checkout_session, name='create_checkout_session'),
    path('checkout/success/', views.checkout_success, name='checkout_success'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('bag/add/<int:product_id>/', views.add_to_bag, name='add_to_bag'),
    path('bag/update/<int:product_id>/', views.update_bag, name='update_bag'),
]
