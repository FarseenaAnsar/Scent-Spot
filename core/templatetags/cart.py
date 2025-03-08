from django import template 

register = template.Library()

@register.filter(name = "is_in_cart")
def is_in_cart(product, cart):
    keys = cart.keys()
    for prd_id in keys:
        if(prd_id == ""):
            break
        if (int(prd_id) == int(product.id)):
            return cart.get(prd_id)
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