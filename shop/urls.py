from django.urls import path
from . import views

urlpatterns = [
    path('', views.store_view, name='store'),
    path('product/<int:pk>/', views.product_detail_view, name='product_detail'),  # <-- Add this exact line
]
