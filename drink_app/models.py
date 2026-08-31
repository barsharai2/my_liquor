from django.db import models
from django.utils import timezone


# Create your models here.


class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True
    )
    

    def __str__(self):
        return self.name


class Blog(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(
        upload_to="blog/",
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.title

class CartItem(models.Model):
    product_name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def total_price(self):
        return self.price * self.quantity

class Shop(models.Model):

    CATEGORY_CHOICES = [
        ("whisky", "Whisky"),
        ("vodka", "Vodka"),
        ("rum", "Rum"),
        ("gin", "Gin"),
        ("tequila", "Tequila"),
        ("brandy", "Brandy & Cognac"),
        ("liqueurs", "Liqueurs"),
        ("red-wine", "Red Wine"),
        ("white-wine", "White Wine"),
        ("rose", "Rosé"),
        ("sparkling", "Sparkling Wine"),
        ("lager", "Lager"),
        ("ipa", "IPA"),
        ("craft-beer", "Craft Beer"),
    ]

    ABV_CHOICES = [
        ("low", "Under 10%"),
        ("medium", "10% - 20%"),
        ("strong", "20% - 40%"),
        ("very-strong", "40%+"),
    ]

    name = models.CharField(max_length=200)

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES
    )

    description = models.TextField(blank=True)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=0
    )

    review_count = models.PositiveIntegerField(default=0)

    abv = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Alcohol percentage, e.g. 40 for 40%"
    )

    abv_level = models.CharField(
        max_length=20,
        choices=ABV_CHOICES,
        blank=True
    )

    volume = models.CharField(
        max_length=50,
        default="750ml"
    )

    image = models.ImageField(
        upload_to="shop/products/"
    )

    badge = models.CharField(
        max_length=30,
        blank=True,
        help_text="Example: BESTSELLER, NEW, POPULAR"
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):

        # Automatically determine ABV range
        if self.abv < 10:
            self.abv_level = "low"

        elif self.abv < 20:
            self.abv_level = "medium"

        elif self.abv < 40:
            self.abv_level = "strong"

        else:
            self.abv_level = "very-strong"

        super().save(*args, **kwargs)

class Offer(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    products = models.ManyToManyField(
        'Shop',
        related_name='offers',
        blank=True
    )

    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    @property
    def is_current(self):
        now = timezone.now()

        return (
            self.is_active
            and self.start_date <= now <= self.end_date
        )