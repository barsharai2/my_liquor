from django.shortcuts import render
from .models import *
from django.db.models import Count


# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.models import User

from .models import Product, Blog


# =========================================================
# HOME
# =========================================================

def index(request):
    """
    Home page
    """

    products = Product.objects.all()[:8]
    now = timezone.now()

    offers = Offer.objects.filter(
        is_active=True,
        start_date__lte=now,
        end_date__gte=now
    ).prefetch_related('products')

    context = {
        "products": products,
        'offers':offers,
    }

    return render(request, "index.html", context)


# =========================================================
# PRODUCTS / SHOP
# =========================================================

def product(request):
    """
    Product listing + search
    """

    query = request.GET.get("q", "").strip()

    products = Product.objects.all()

    # Search
    if query:
        products = products.filter(
            name__icontains=query
        )

    context = {
        "products": products,
        "query": query,
    }

    return render(request, "products.html", context)


# =========================================================
# PRODUCT DETAIL
# =========================================================

def product_detail(request, pk):
    """
    Single product page
    """

    product = get_object_or_404(
        Product,
        pk=pk
    )

    context = {
        "product": product,
    }

    return render(
        request,
        "product-detail.html",
        context
    )


# =========================================================
# ABOUT
# =========================================================

def about(request):

    return render(
        request,
        "about.html"
    )


# =========================================================
# CONTACT
# =========================================================

def contact(request):

    if request.method == "POST":

        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        # You can save this to a Contact model later.
        # Or send an email using Django's send_mail().

        messages.success(
            request,
            "Thank you! Your message has been received."
        )

        return redirect("/contact/#contact")


    return render(
        request,
        "contact.html"
    )


# =========================================================
# BLOG
# =========================================================

def blog(request):

    posts = Blog.objects.all().order_by(
        "-created_at"
    )

    context = {
        "posts": posts,
    }

    return render(
        request,
        "blog.html",
        context
    )




    products = Product.objects.all().order_by("-id")
    return render(request, "new_arrivals.html", {
        "products": products
    })


# =========================================================
# LOGIN
# =========================================================

def login(request):

    if request.user.is_authenticated:
        return redirect("index")

    if request.method == "POST":

        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            user = User.objects.get(
                email=email
            )

        except User.DoesNotExist:

            messages.error(
                request,
                "Invalid email or password."
            )

            return redirect("login")

        user = authenticate(
            request,
            username=user.username,
            password=password
        )

        if user is not None:

            auth_login(
                request,
                user
            )

            messages.success(
                request,
                "You have successfully logged in."
            )

            return redirect("index")

        else:

            messages.error(
                request,
                "Invalid email or password."
            )

            return redirect("login")

    return render(
        request,
        "login.html"
    )


# =========================================================
# REGISTER
# =========================================================

def register(request):

    if request.user.is_authenticated:
        return redirect("index")

    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password")

        # Check email
        if User.objects.filter(
            email=email
        ).exists():

            messages.error(
                request,
                "An account with this email already exists."
            )

            return redirect("register")

        # Create username
        username = email.split("@")[0]

        # Make username unique
        original_username = username
        counter = 1

        while User.objects.filter(
            username=username
        ).exists():

            username = (
                f"{original_username}{counter}"
            )

            counter += 1

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # Save name
        user.first_name = name
        user.save()

        messages.success(
            request,
            "Your account has been created."
        )

        return redirect("login")

    return render(
        request,
        "register.html"
    )


# =========================================================
# LOGOUT
# =========================================================

def user_logout(request):

    logout(request)

    messages.success(
        request,
        "You have been logged out."
    )

    return redirect("index")


# =========================================================
# CART
# =========================================================

def cart(request):

    cart_items = []

    cart_data = request.session.get(
        "cart",
        {}
    )

    for product_id, quantity in cart_data.items():

        try:

            product = Product.objects.get(
                id=product_id
            )

            cart_items.append({
                "product": product,
                "quantity": quantity,
            })

        except Product.DoesNotExist:

            pass

    context = {
        "cart_items": cart_items,
    }

    return render(
        request,
        "cart.html",
        context
    )


# =========================================================
# ADD TO CART
# =========================================================

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart = request.session.get("cart", {})

    product_id = str(product.id)

    if product_id in cart:
        cart[product_id] += 1
    else:
        cart[product_id] = 1

    request.session["cart"] = cart
    request.session.modified = True

    messages.success(
        request,
        f"{product.name} added to your cart."
    )

    return redirect("cart")

# =========================================================
# REMOVE FROM CART
# =========================================================

def remove_from_cart(request, product_id):

    cart_data = request.session.get(
        "cart",
        {}
    )

    product_id = str(product_id)

    if product_id in cart_data:

        del cart_data[product_id]

    request.session["cart"] = cart_data

    request.session.modified = True

    return redirect("cart")

def brands (request):
    return render(request,"brand.html")

def offers (request):
    return render(request,"offer.html")

# product-shop
def shop(request):

    category = request.GET.get("category")

    products = Shop.objects.filter(
        is_active=True
    )

    if category:
        products = products.filter(
            category=category
        )

    category_counts = (
        Shop.objects
        .filter(is_active=True)
        .values("category")
        .annotate(total=Count("id"))
    )

    category_counts = {
        item["category"]: item["total"]
        for item in category_counts
    }

    categories = []

    for value, display in Shop.CATEGORY_CHOICES:
        categories.append({
            "value": value,
            "display": display,
            "count": category_counts.get(value, 0),
        })

    context = {
        "products": products,
        "total_products": products.count(),
        "category_counts": category_counts,
        "categories": categories,
        "selected_category": category,
    }

    return render(request, "products.html", context)


def offers(request):
    now = timezone.now()

    offers = Offer.objects.filter(
        is_active=True,
    ).prefetch_related('products')

    for offer in offers:
        for product in offer.products.all():

            discount = (
                product.price *
                offer.discount_percentage / 100
            )

            product.offer_price = product.price - discount

    return render(request, 'offer.html', {
        'offers': offers
    })