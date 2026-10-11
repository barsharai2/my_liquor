
def cart_count(request):
    cart_data = request.session.get("cart", {})

    count = 0

    for quantity in cart_data.values():
        try:
            count += max(0, int(quantity))
        except (TypeError, ValueError):
            continue

    return {"cart_count": count}