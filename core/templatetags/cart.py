from django import template
from django.contrib.auth.models import AnonymousUser
from core.models.cart import CartItem
from core.models.wishlist import Wishlist

register = template.Library()

@register.filter(name = "is_in_cart")
def is_in_cart(product, cart):
    # First check if we have a user in the context
    request = getattr(product, '_request', None)
    if request and request.user and request.user.is_authenticated:
        # Check database cart
        try:
            cart_item = CartItem.objects.filter(user=request.user, product=product).first()
            if cart_item:
                return cart_item.quantity
        except Exception:
            pass
    
    # Fall back to session cart
    if cart:
        keys = cart.keys()
        for prd_id in keys:
            if prd_id == "":
                break
            try:
                if int(prd_id) == int(product.id):
                    return cart.get(prd_id)
            except (ValueError, TypeError):
                continue
    return False

@register.filter(name = "cart_quantity")
def cart_quantity(product, cart):
    total = 0
    if not product or not cart:
        return total
    for p in product:
        total += p.price * cart.get(str(p.id), 0)  # Convert id to string since session keys are strings
    return total

@register.filter(name = "cart_price")
def cart_price(product, cart_session):
    total = 0
    if not product or not cart_session:
        return total
    for p in product:
        total += p.price * cart_session.get(str(p.id), 0)
    return total

@register.filter(name = "cart_total")
def cart_total(cart_items):
    total = 0
    if cart_items:
        for item in cart_items:
            total += item.product.price * item.quantity
    return total


@register.filter(name = "currency")
def currency(number):
    return "₹" + str(number)

@register.filter(name = "mul")
def mul(n1, n2):
    return n1 * n2

@register.filter(name = "sum")
def sum(n1, n2):
    return n1 + n2

@register.filter(name = "cart_num")
def cart_num(cart):
    keys = cart.keys()
    return len(keys)

@register.filter(name = "loop_counter")
def loop_counter(num):
    return range(num)

@register.filter(name = "is_in_wishlist")
def is_in_wishlist(product, user):
    """Check if a product is in the user's wishlist"""
    if not user.is_authenticated:
        return False
    return Wishlist.objects.filter(user=user, product=product).exists()