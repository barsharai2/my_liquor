from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(Product)
admin.site.register(CartItem)
@admin.register(Shop)

class ShopAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "category",
        "price",
        "abv",
        "rating",
        "is_active",
        "created_at",
    )

    list_filter = (
        "category",
        "abv_level",
        "is_active",
    )

    search_fields = (
        "name",
        "description",
    )

    list_editable = (
        "price",
        "is_active",
    )

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


# Offer Admin
class OfferAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'discount_percentage',
        'start_date',
        'end_date',
        'is_active',
    )
    search_fields = (
        'name',
        'description',
    )


    list_filter = (
        'is_active',
        'start_date',
        'end_date',
    )

    filter_horizontal = ('products',)


admin.site.register(Offer, OfferAdmin)