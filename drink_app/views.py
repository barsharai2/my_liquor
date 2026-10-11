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

import base64
import hashlib
import hmac
import json
import uuid
from decimal import Decimal, InvalidOperation

import requests

from django.conf import settings
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import Shop


def make_esewa_signature(message):
    key = settings.ESEWA_SECRET_KEY.encode("utf-8")
    digest = hmac.new(
        key,
        message.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(digest).decode("utf-8")


@require_POST
def esewa_checkout(request):
    cart_data = request.session.get("cart", {})
    total = Decimal("0.00")

    products = Shop.objects.filter(
        id__in=cart_data.keys(),
        is_active=True,
    )

    for product in products:
        try:
            quantity = int(cart_data.get(str(product.id), 0))
        except (TypeError, ValueError):
            continue

        if 1 <= quantity <= 99:
            total += product.price * quantity

    if total <= 0:
        messages.error(request, "Your cart is empty.")
        return redirect("cart")

    # eSewa ePay expects a unique transaction UUID.
    transaction_uuid = uuid.uuid4().hex
    total_amount = f"{total:.2f}"
    product_code = settings.ESEWA_PRODUCT_CODE

    signed_fields = (
        f"total_amount={total_amount},"
        f"transaction_uuid={transaction_uuid},"
        f"product_code={product_code}"
    )

    signature = make_esewa_signature(signed_fields)

    request.session["pending_esewa"] = {
        "transaction_uuid": transaction_uuid,
        "total_amount": total_amount,
        "product_code": product_code,
    }

    context = {
        "payment_url": settings.ESEWA_PAYMENT_URL,
        "amount": total_amount,
        "total_amount": total_amount,
        "transaction_uuid": transaction_uuid,
        "product_code": product_code,
        "tax_amount": "0",
        "product_service_charge": "0",
        "product_delivery_charge": "0",
        "success_url": request.build_absolute_uri(
            reverse("esewa_success")
        ),
        "failure_url": request.build_absolute_uri(
            reverse("esewa_failure")
        ),
        "signed_field_names": (
            "total_amount,transaction_uuid,product_code"
        ),
        "signature": signature,
    }

    return render(request, "esewa_checkout.html", context)


def esewa_success(request):
    pending = request.session.get("pending_esewa")

    if not pending:
        messages.error(
            request,
            "No pending eSewa transaction was found.",
        )
        return redirect("cart")

    encoded_data = request.GET.get("data", "")

    try:
        decoded = base64.b64decode(
            encoded_data,
            validate=True,
        )
        response_data = json.loads(decoded.decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
        messages.error(request, "Invalid eSewa payment response.")
        return redirect("cart")

    # Verify the signature returned by eSewa.
    signed_names = response_data.get("signed_field_names", "")
    signature_fields = signed_names.split(",")

    if not signature_fields or any(
        name not in response_data for name in signature_fields
    ):
        messages.error(request, "Payment signature is incomplete.")
        return redirect("cart")

    response_message = ",".join(
        f"{name}={response_data[name]}"
        for name in signature_fields
    )
    expected_signature = make_esewa_signature(response_message)
    received_signature = response_data.get("signature", "")

    if not hmac.compare_digest(
        expected_signature,
        received_signature,
    ):
        messages.error(request, "Payment signature verification failed.")
        return redirect("cart")

    # Ensure the response matches this browser's pending transaction.
    if (
        response_data.get("transaction_uuid")
        != pending["transaction_uuid"]
        or response_data.get("product_code")
        != pending["product_code"]
        or response_data.get("status") != "COMPLETE"
    ):
        messages.error(request, "Payment is not confirmed.")
        return redirect("cart")

    try:
        returned_total = Decimal(str(response_data["total_amount"]))
        expected_total = Decimal(pending["total_amount"])
    except (KeyError, InvalidOperation, TypeError, ValueError):
        messages.error(request, "Invalid payment amount.")
        return redirect("cart")

    if returned_total != expected_total:
        messages.error(request, "Payment amount does not match.")
        return redirect("cart")

    # Verify the transaction independently with eSewa's status API.
    try:
        result = requests.get(
            settings.ESEWA_STATUS_URL,
            params={
                "product_code": pending["product_code"],
                "total_amount": pending["total_amount"],
                "transaction_uuid": pending["transaction_uuid"],
            },
            timeout=15,
        )
        result.raise_for_status()
        status_data = result.json()
    except (requests.RequestException, ValueError):
        messages.error(
            request,
            "Could not verify payment with eSewa. Please check again.",
        )
        return redirect("cart")

    try:
        verified_total = Decimal(str(status_data.get("total_amount")))
    except (InvalidOperation, TypeError, ValueError):
        verified_total = Decimal("-1")

    if (
        status_data.get("status") != "COMPLETE"
        or status_data.get("transaction_uuid")
        != pending["transaction_uuid"]
        or status_data.get("product_code")
        != pending["product_code"]
        or verified_total != expected_total
    ):
        messages.error(
            request,
            "eSewa has not confirmed this payment.",
        )
        return redirect("cart")

    # Clear the cart only after verification.
    request.session["cart"] = {}
    request.session.pop("pending_esewa", None)

    return render(request, "esewa_success.html", {
        "transaction_uuid": pending["transaction_uuid"],
        "total": expected_total,
    })


def esewa_failure(request):
    messages.warning(
        request,
        "Payment was cancelled, failed, or is still pending. "
        "Please check the transaction status before retrying.",
    )
    return redirect("cart")


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
# CART PAGE
# =========================================================

def cart(request):
    cart_data = request.session.get("cart", {})
    cart_items = []
    total = Decimal("0.00")
    valid_cart = {}

    products = Shop.objects.filter(id__in=cart_data.keys())

    for product in products:
        try:
            quantity = int(cart_data.get(str(product.id), 0))
        except (TypeError, ValueError):
            continue

        if quantity < 1:
            continue

        quantity = min(quantity, 99)
        subtotal = product.price * quantity
        total += subtotal

        valid_cart[str(product.id)] = quantity

        cart_items.append({
            "product": product,
            "quantity": quantity,
            "subtotal": subtotal,
        })

    request.session["cart"] = valid_cart

    return render(request, "cart.html", {
        "cart_items": cart_items,
        "total": total,
    })


# =========================================================
# ADD TO CART
# =========================================================


def add_to_cart(request, product_id):
    product = get_object_or_404(
        Shop,
        id=product_id,
        is_active=True,
    )

    cart_data = request.session.get("cart", {})
    key = str(product.id)

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1

    quantity = max(1, quantity)
    current_quantity = int(cart_data.get(key, 0))

    cart_data[key] = min(current_quantity + quantity, 99)

    request.session["cart"] = cart_data
    request.session.modified = True

    messages.success(
        request,
        f"{product.name} added to your cart."
    )

    return redirect("cart")


# =========================================================
# UPDATE CART QUANTITY
# =========================================================


def update_cart(request, product_id):
    cart_data = request.session.get("cart", {})
    key = str(product_id)

    if key not in cart_data:
        return redirect("cart")

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1

    if quantity <= 0:
        cart_data.pop(key, None)
    else:
        cart_data[key] = min(quantity, 99)

    request.session["cart"] = cart_data
    request.session.modified = True

    return redirect("cart")


# =========================================================
# REMOVE FROM CART
# =========================================================


def remove_from_cart(request, product_id):
    cart_data = request.session.get("cart", {})
    cart_data.pop(str(product_id), None)

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

