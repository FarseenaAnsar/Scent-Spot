from decimal import Decimal
from django.utils import timezone
from core.models.offer import ProductOffer, CategoryOffer

def get_product_offer(product):
    """Get the active product offer for a specific product"""
    now = timezone.now()
    offers = ProductOffer.objects.filter(
        product=product,
        active=True,
        valid_from__lte=now,
        valid_to__gte=now
    )
    return offers.order_by('-discount_percentage').first()

def get_category_offer(product):
    """Get the active category offer for a product's category"""
    now = timezone.now()
    offers = CategoryOffer.objects.filter(
        category=product.category,
        active=True,
        valid_from__lte=now,
        valid_to__gte=now
    )
    return offers.order_by('-discount_percentage').first()

def get_best_offer(product):
    """Get the best offer (highest discount) for a product"""
    product_offer = get_product_offer(product)
    category_offer = get_category_offer(product)
    
    if product_offer and category_offer:
        # Return the offer with the higher discount percentage
        if product_offer.discount_percentage >= category_offer.discount_percentage:
            return product_offer
        return category_offer
    elif product_offer:
        return product_offer
    elif category_offer:
        return category_offer
    return None

def calculate_discount_price(product):
    """Calculate the discounted price for a product"""
    offer = get_best_offer(product)
    if not offer:
        return product.price
    
    discount_amount = (Decimal(str(product.price)) * offer.discount_percentage) / 100
    return product.price - int(discount_amount)

def get_offer_details(product):
    """Get offer details for a product including discount percentage and type"""
    offer = get_best_offer(product)
    if not offer:
        return None
    
    offer_type = "Product" if isinstance(offer, ProductOffer) else "Category"
    return {
        'type': offer_type,
        'name': offer.name,
        'discount_percentage': offer.discount_percentage,
        'original_price': product.price,
        'discounted_price': calculate_discount_price(product)
    }