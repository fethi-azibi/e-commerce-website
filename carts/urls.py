from django.urls import path
from . import views

urlpatterns = [
    path('', views.cart, name='cart'),
    path('add_card/<int:product_id>/', views.add_cart, name='add_card'),
    path('remove_card/<int:product_id>/<int:card_item_id>/', views.remove_card, name='remove_card'),
    path('remove_card_item/<int:product_id>/<int:card_item_id>/', views.remove_cart_item, name='remove_card_item'),
    path('checkout/', views.checkout, name='checkout')
]