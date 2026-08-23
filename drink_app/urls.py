from django.contrib import admin
from django.urls import path
from .views import*

urlpatterns = [

path('', index, name='index'),
path('products/',product, name='product'),
path('about/',about, name='about'),
path('contact/',contact, name='contact'),
path('login/',login, name='login'),
path('register/',register, name='register'),
path('cart/',cart, name='cart'),
path("new-arrivals/", new_arrivals, name="new_arrivals"),
path("offers/",offers, name="offers"),
path("brands/", brands, name="brands"),
]