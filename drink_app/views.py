from django.shortcuts import render
from .models import *
from decimal import Decimal, InvalidOperation
from django.db.models import Count
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib.auth.forms import PasswordChangeForm


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

    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    min_price = request.GET.get("min", "").strip()
    max_price = request.GET.get("max", "").strip()

    products = Product.objects.all()

    # SEARCH
    if query:
        products = products.filter(
            name__icontains=query
        )

    # CATEGORY
    if category and category != "all":
        products = products.filter(
            category=category
        )

    # MIN PRICE
    if min_price:
        try:
            products = products.filter(
                price__gte=Decimal(min_price)
            )
        except (InvalidOperation, ValueError):
            pass

    # MAX PRICE
    if max_price:
        try:
            products = products.filter(
                price__lte=Decimal(max_price)
            )
        except (InvalidOperation, ValueError):
            pass

    # PAGINATION
    paginator = Paginator(products, 9)

    page_number = request.GET.get("page")

    products = paginator.get_page(page_number)

    # CATEGORIES
    category_values = (
        Product.objects
        .values_list("category", flat=True)
        .distinct()
        .order_by("category")
    )

    categories = []

    for value in category_values:

        if value:

            categories.append({
                "value": value,
                "display": value.replace("-", " ").title(),
                "count": Product.objects.filter(
                    category=value
                ).count(),
            })

    context = {
        "products": products,

        "query": query,

        "categories": categories,

        "total_products":
            Product.objects.count(),

        "current_category":
            category,

        "min_price":
            min_price,

        "max_price":
            max_price,
    }

   
    if request.headers.get("HX-Request"):

        return render(
            request,
            "products/product_list.html",
            context
        )

    return render(
        request,
        "products.html",
        context
    )

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



@login_required(login_url="login")
def pass_change(request):

    if request.method == "POST":
        form = PasswordChangeForm(
            user=request.user,
            data=request.POST
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Your password has been changed successfully."
            )

            return redirect("profile")

    else:
        form = PasswordChangeForm(
            user=request.user
        )

    return render(
        request,
        "profile/changepassword.html",
        {
            "form": form
        }
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

def logout_view(request):

    if request.method == "POST":
        logout(request)

        messages.success(
            request,
            "You have been logged out."
        )

        return redirect("index")

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

    # GET PARAMETERS
    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()

    # GET ALL ACTIVE PRODUCTS
    products = Shop.objects.filter(
        is_active=True
    )

    # SEARCH
    if query:
        products = products.filter(
            name__icontains=query
        )

    # CATEGORY
    if category and category != "all":
        products = products.filter(
            category=category
        )

    # --------------------------------
    # PAGINATION MUST BE LAST
    # --------------------------------

    paginator = Paginator(products, 9)

    page_number = request.GET.get("page")

    products = paginator.get_page(page_number)

    # CATEGORY COUNTS
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

        "total_products": Shop.objects.filter(
            is_active=True
        ).count(),

        "category_counts": category_counts,

        "categories": categories,

        "selected_category": category,

        "query": query,
    }

    return render(
        request,
        "products.html",
        context
    )


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

