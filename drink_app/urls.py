from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views

from django.contrib.auth.views import LogoutView

from .views import*

urlpatterns = [

path('', index, name='index'),
path('products/', shop, name='product'),
path('about/',about, name='about'),
path('contact/',contact, name='contact'),
path('login/',login, name='login'), 
path("logout/",LogoutView.as_view(next_page="/"),name="logout",),
path('register/',register, name='register'),
path('cart/',cart, name='cart'),
path("offers/",offers, name="offers"),
path("brands/", brands, name="brands"),
path("add-to-cart/<int:product_id>/",add_to_cart,name="add_to_cart" ),
path('password_change/',pass_change,name='password_change'),
        # ................forget password............
path('password_reset/', auth_views.PasswordResetView.as_view( template_name="auth/password_reset.html", html_email_template_name="auth/mail.html"), name='password_reset'),
path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(template_name="auth/password_reset_done.html"), name='password_reset_done'),
path('password_reset_confirm/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(template_name="auth/set-password.html"), name='password_reset_confirm'),
path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view( template_name="auth/password_reset_complete.html"), name='password_reset_complete'),

   
]