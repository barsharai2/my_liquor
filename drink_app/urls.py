from django.contrib import admin
from django.urls import path
from .views import*

urlpatterns = [

path('', index, name='index'),
path('products/', shop, name='product'),
path('about/',about, name='about'),
path('contact/',contact, name='contact'),
path('login/',login, name='login'),
path('register/',register, name='register'),
path('cart/',cart, name='cart'),
path("offers/",offers, name="offers"),
path("brands/", brands, name="brands"),
path("add-to-cart/<int:product_id>/",add_to_cart,name="add_to_cart" ),
   
]